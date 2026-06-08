from system_settings import llm
from agent_tools import search_internet, save_movie_to_db, save_actor_to_db
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

    structured_llm = llm.with_structured_output(MovieSchema)

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


def unknown_node(state: AgentState) -> dict:
    print("\n[Узел: Неизвестно] Не удалось определить действие.")
    return {"final_response": "Я пока не умею это делать. Я могу добавлять фильмы или актеров."}


def route_logic(state: AgentState) -> str:
    # Возвращаем строку, которая совпадает с названием нужного узла
    return state["intent"]