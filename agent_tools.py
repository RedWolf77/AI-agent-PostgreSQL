import psycopg2
from ddgs import DDGS
from langchain_community.document_loaders import WebBaseLoader
from typing import Optional
from schemas import MovieSchema, ActorSchema
from system_settings import connection_config


def search_internet(query: str) -> dict[str, str]:
    """
     Функция поиска информации в интернете
    """

    try:
        with DDGS() as ddgs:
            hits = ddgs.text(query, region="ru-ru", max_results=3)
            if not hits:
                return {"error": "Ничего не найдено!", "web_content": None}

            # структура hits (список с найденной информацией):
            # title: название ссылки
            # href: сама ссылка
            # body: краткая сводка с сайта (сниппет)

            urls_to_download = []   # список ссылок для чтения
            snippets_backup = []    # копия данных

            # Проходимся по каждой записи в hits и забираем оттуда ссылку на чтение
            for h in hits:
                url = h['href']
                urls_to_download.append(url)
                snippets_backup.append(f"Заголовок: {h['title']}\nОписание: {h['body']}")
                print(f"Найдена ссылка: {url}")

            print(f"Найдено {len(urls_to_download)} чистых ссылок.")

            merged_contents = []

            # Чтение ссылок
            for index, url in enumerate(urls_to_download, start=1):
                try:
                    print(f"[{index}/{len(urls_to_download)}] Выкачиваем текст из: {url}")
                    loader = WebBaseLoader(url)
                    docs = loader.load()

                    if docs and docs[0].page_content:
                        page_text = docs[0].page_content.strip()
                        # берем первые 2000 символов, чтобы не перегружать модель
                        clean_chunk = " ".join(page_text.split())[:2000]
                        merged_contents.append(f"--- ТЕКСТ ИЗ ИСТОЧНИКА №{index} ({url}) ---\n{clean_chunk}")
                except Exception as page_err:
                    print(f"Не удалось скачать {url}: {page_err}")
                    continue

            # Усли сайты заблокировали робота, то используем сниппеты поисковика
            if not merged_contents:
                print("Сайты не отдают текст (возможно, блокировка). Используем поисковые сниппеты.")
                final_context = "\n\n".join(snippets_backup)
            else:
                final_context = "\n\n\n".join(merged_contents)
                print(f"Содержимое сайтов успешно прочитано.")

            return {"web_content": final_context, "error": None}

    except Exception as e:
        return {"error": f"Ошибка поиска: {e}", "web_content": None}


###
### ЗАПРОСЫ К БД
###
def save_movie_to_db(movie: MovieSchema) -> Optional[int]:
    """
    Сохранение в таблицу Фильм
    """

    query = """
            INSERT INTO "Справочник Фильмов"."Фильм" ("название", "сюжет", "возрастной_рейтинг")
            VALUES (%s, %s, %s)
            RETURNING "id_фильм";
        """

    try:
        with psycopg2.connect(**connection_config) as connection:
            with connection.cursor() as cursor:
                # передаем параметры
                cursor.execute(query, (
                    movie.name,
                    movie.plot,
                    movie.age_rating
                ))

                # Возвращаем сгенерирвоанный ID
                generated_id = cursor.fetchone()[0]

                connection.commit()
                print(f"Запись добавлена: Фильм '{movie.name}' ID: {generated_id}")
                return generated_id
    except Exception as error:
        print(f"Ошибка при работе с PostgreSQL: {error}")
        return None


def save_actor_to_db(actor: ActorSchema):
    """
    Сохранение в таблицу Актер
    """
    query = """
            INSERT INTO "Справочник Фильмов"."Актер" ("Фамилия", "Имя", "Отчество", "дата_рождения", "дата_смерти")
            VALUES (%s, %s, %s, %s, %s)
            RETURNING "id_актер";
        """

    try:
        with psycopg2.connect(**connection_config) as connection:
            with connection.cursor() as cursor:
                # Передаем параметры
                cursor.execute(query, (
                    actor.last_name,
                    actor.first_name,
                    actor.middle_name,
                    actor.birth_date,
                    actor.death_date,
                ))

                # Возвращаем сгенерирвоанный ID
                generated_id = cursor.fetchone()[0]

                connection.commit()
                print(f"Запись добавлена: Актер '{actor.last_name} {actor.first_name}' ID: {generated_id}")
                return generated_id
    except Exception as error:
        print(f"Ошибка при работе с PostgreSQL: {error}")
        return None


def search_movies_in_db(title: str) -> list:
    """
    Поиск существующих фильмов в БД для верификации перед удалением
    """
    query = """
        SELECT "id_фильм", "название", "сюжет" 
        FROM "Справочник Фильмов"."Фильм"
        WHERE "название" ILIKE %s;
    """
    try:
        with psycopg2.connect(**connection_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (f"%{title}%",))
                rows = cursor.fetchall()
                return [{"id": r[0], "name": r[1], "plot": r[2][:50] + "..."} for r in rows]
    except Exception as e:
        print(f"Ошибка поиска в БД: {e}")
        return []

def delete_movie_from_db(movie_id: int) -> bool:
    """
    Удаление фильма по первичному ключу ID
    """
    query = 'DELETE FROM "Справочник Фильмов"."Фильм" WHERE "id_фильм" = %s;'
    try:
        with psycopg2.connect(**connection_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (movie_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"Ошибка удаления из БД: {e}")
        return False


def search_actors_in_db(name: str) -> list:
    """
    Поиск существующих актеров в БД для верификации перед удалением.
    Поиск ведется по Имени, Фамилии или Отчеству.
    """
    query = """
        SELECT * 
        FROM "Справочник Фильмов"."Актер"
        WHERE concat_ws(' ', trim("Фамилия"), trim("Имя"), trim("Отчество")) ILIKE ALL(%s);
    """
    try:
        with psycopg2.connect(**connection_config) as conn:
            with conn.cursor() as cursor:
                # Разбиваем строку на слова и каждое слово оборачиваем в %%
                search_words = [f"%{word}%" for word in name.strip().split()]

                cursor.execute(query, (search_words,))
                rows = cursor.fetchall()

                results = []
                for r in rows:
                    f_name = r[1].strip() if r[1] else ""
                    i_name = r[2].strip() if r[2] else ""
                    o_name = r[3].strip() if r[3] else ""

                    # Собираем ФИО
                    full_name = " ".join(filter(None, [f_name, i_name, o_name]))
                    b_date = str(r[4]) if r[4] else "Не указана"

                    results.append({
                        "id": r[0],
                        "name": full_name,
                        "birth_date": b_date
                    })
                return results
    except Exception as e:
        print(f"Ошибка поиска актеров в БД: {e}")
        return []


def delete_actor_from_db(actor_id: int) -> bool:
    """
    Удаление актера по первичному ключу ID
    """
    query = 'DELETE FROM "Справочник Фильмов"."Актер" WHERE "id_актер" = %s;'
    try:
        with psycopg2.connect(**connection_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (actor_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"Ошибка удаления актера из БД: {e}")
        return False