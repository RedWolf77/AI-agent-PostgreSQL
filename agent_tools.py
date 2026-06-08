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