from system_settings import llm
from agent_tools import (
    search_internet, save_movie_to_db, save_actor_to_db, search_movies_in_db,
    delete_movie_from_db, search_actors_in_db, delete_actor_from_db
)
from schemas import MovieSchema, RouterSchema, AgentState, ActorSchema

# Узел-диспетчер
def router_node(state: AgentState) -> dict:
    print(f"\n[Диспетчер] Анализирую запрос: '{state['user_query']}'")

    prompt = f"""
    Проанализируй запрос пользователя и определи, к какой категории он относится.
    Запрос: "{state['user_query']}"
    """

    # Настраиваем модель строго на схему роутера
    router_llm = llm.with_structured_output(RouterSchema)
    decision = router_llm.invoke(prompt)

    print(f"[Диспетчер] Решение: Намерение={decision.intent}, Сущность='{decision.entity_name}'")

    # Сохраняем решение в состояние графа
    return {
        "intent": decision.intent,
        "extracted_name": decision.entity_name
    }

###
### УЗЛЫ ИСПОЛНИТЕЛИ
###

# Узел добавления фильма
def add_movie_node(state: AgentState) -> dict:
    movie_title = state["extracted_name"]
    print(f"\n[Узел: Фильмы] Запускаю процесс добавления фильма: {movie_title}")

    structured_llm = llm.with_structured_output(MovieSchema)

    query = f"фильм {movie_title} сюжет возрастной рейтинг кинопоиск"

    raw_data = search_internet(query)

    prompt = f"""
        Проанализируй собранные тексты из нескольких источников о фильме и заполни структуру MovieSchema.

        КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
        1. Заполняй все текстовые поля (name, plot) СТРОГО НА РУССКОМ ЯЗЫКЕ.
        2. В поле 'plot' запиши именно краткое описание сюжета (о чем фильм), а не отзывы или рецензии критиков.

        Собранные тексты из интернета:
        {raw_data['web_content']}
    """

    movie_obj = structured_llm.invoke(prompt)
    save_movie_to_db(movie_obj)

    return {"final_response": f"Фильм '{movie_title}' успешно найден и добавлен в базу!"}


# Узел добавления актера
def add_actor_node(state: AgentState) -> dict:
    actor_name = state["extracted_name"]
    print(f"\n[Узел: Актеры] Запускаю процесс добавления актера: {actor_name}")

    structured_llm = llm.with_structured_output(ActorSchema)

    query = f"фильм {actor_name} сюжет возрастной рейтинг кинопоиск"

    raw_data = search_internet(query)

    prompt = f"""
            Проанализируй собранные тексты из нескольких источников об актере и заполни структуру ActorSchema.

            КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
            1. Заполняй все текстовые поля СТРОГО НА РУССКОМ ЯЗЫКЕ.

            Собранные тексты из интернета:
            {raw_data['web_content']}
        """

    actor_obj = structured_llm.invoke(prompt)
    save_actor_to_db(actor_obj)

    return {"final_response": f"Актер '{actor_name}' успешно добавлен в базу!"}


def delete_movie_node(state: AgentState) -> dict:
    movie_title = state["extracted_name"]
    print(f"\n[Узел: Удаление] Запуск процесса удаления фильма: '{movie_title}'")

    # Поиск совпадений в базе данных
    records = search_movies_in_db(movie_title)

    if not records:
        return {"final_response": f"Удаление невозможно: фильм '{movie_title}' не найден в базе данных."}

    # Если найдена ровно одна запись, то подтверждаем и удаляем
    if len(records) == 1:
        target = records[0]
        print(f"[Узел: Удаление] Найдено точное совпадение: ID {target['id']} - {target['name']}")

        # Подтверждение от пользователя
        confirm = input(f"Вы действительно хотите удалить фильм '{target['name']}'? (да/нет): ").strip().lower()
        if confirm in ["да", "yes", "y"]:
            success = delete_movie_from_db(target['id'])
            msg = f"Фильм '{target['name']}' успешно удален из базы данных." if success else "Ошибка при удалении."
        else:
            msg = "Удаление отменено пользователем."
        return {"final_response": msg}

    # Если найдено несколько записей, то выводим список на выбор
    print(f"\n[Узел: Удаление] Найдено несколько совпадений ({len(records)}):")
    for idx, rec in enumerate(records, start=1):
        print(f"  [{idx}]  Название: {rec['name']} | Сюжет: {rec['plot']} ID: {rec['id']} ")

    try:
        choice = input("\nВведите номер записи для удаления (или 0 для отмены): ").strip()
        choice_idx = int(choice)

        if choice_idx == 0 or choice_idx > len(records):
            return {"final_response": "Удаление отменено."}

        target = records[choice_idx - 1]
        success = delete_movie_from_db(target['id'])

        return {
            "final_response": f"Фильм '{target['name']}' (ID: {target['id']}) успешно удален." if success else "Ошибка при удалении."
        }
    except ValueError:
        return {"final_response": "Некорректный ввод. Операция удаления прервана."}


# Узел удаления актера
def delete_actor_node(state: AgentState) -> dict:
    actor_name = state["extracted_name"]
    print(f"\n[Узел: Удаление Актера] Запуск процесса поиска актера: '{actor_name}'")

    records = search_actors_in_db(actor_name)

    if not records:
        return {"final_response": f"Удаление невозможно: актер '{actor_name}' не найден в базе данных."}

    # Если найден ровно один актер
    if len(records) == 1:
        target = records[0]
        print(f"[Узел: Удаление Актера] Найдено точное совпадение: ID {target['id']} - {target['name']} (ДР: {target['birth_date']})")

        confirm = input(f"Вы действительно хотите удалить актера '{target['name']}'? (да/нет): ").strip().lower()
        if confirm in ["да", "yes", "y"]:
            success = delete_actor_from_db(target['id'])
            msg = f"Актер '{target['name']}' успешно удален из базы данных." if success else "Ошибка при удалении."
        else:
            msg = "Удаление отменено пользователем."
        return {"final_response": msg}

    # Если найдено несколько актеров
    print(f"\n[Узел: Удаление Актера] Найдено несколько совпадений ({len(records)}):")
    for idx, rec in enumerate(records, start=1):
        print(f"  [{idx}]  ФИО: {rec['name']} | Дата рождения: {rec['birth_date']} | ID: {rec['id']} ")

    try:
        choice = input("\nВведите номер записи для удаления (или 0 для отмены): ").strip()
        choice_idx = int(choice)

        if choice_idx == 0 or choice_idx > len(records):
            return {"final_response": "Удаление отменено."}

        target = records[choice_idx - 1]
        success = delete_actor_from_db(target['id'])

        return {
            "final_response": f"Актер '{target['name']}' (ID: {target['id']}) успешно удален." if success else "Ошибка при удалении."
        }
    except ValueError:
        return {"final_response": "Некорректный ввод. Операция удаления прервана."}


def unknown_node(state: AgentState) -> dict:
    print("\n[Узел: Неизвестно] Не удалось определить действие.")
    return {"final_response": "Я пока не умею это делать. Я могу добавлять фильмы или актеров."}


def route_logic(state: AgentState) -> str:
    # Возвращаем строку, которая совпадает с названием нужного узла
    return state["intent"]