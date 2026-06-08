from router import router_node, add_movie_node, add_actor_node, unknown_node, route_logic
from langgraph.graph import StateGraph, END
from schemas import AgentState

# СБОРКА ГРАФА
workflow = StateGraph(AgentState)

# Добавляем узлы
workflow.add_node("router", router_node)
workflow.add_node("add_movie", add_movie_node)
workflow.add_node("add_actor", add_actor_node)
workflow.add_node("unknown", unknown_node)

# Устанавливаем стартовую точку
workflow.set_entry_point("router")

# Создаем условные переходы от роутера
workflow.add_conditional_edges(
    "router",          # Откуда выходим
    route_logic,       # Функция, которая решает, куда идти
    {
        # Карта переходов: если функция вернула ключ, идем в значение (имя узла)
        "add_movie": "add_movie",
        "add_actor": "add_actor",
        "unknown": "unknown"
    }
)

# Завершаем граф после выполнения ветки
workflow.add_edge("add_movie", END)
workflow.add_edge("add_actor", END)
workflow.add_edge("unknown", END)

# Компилируем
app = workflow.compile()

while True:
    print("=== ИИ-Справочник Фильмов: ===")
    try:
        print("Чтобы выйти, введите 'exit'")
        q = input("--> ").strip()

        if q == 'exit':
            print("Завершение работы.")
            break

        # игнорирование пустых вводов
        if not q:
            continue

        result = app.invoke({"user_query": q})

        print(f"\nОТВЕТ АГЕНТА: {result['final_response']}")
        print("-" * 60)

    except KeyboardInterrupt:
        print("\nПрограмма принудительно остановлена пользователем.")
        break

    except Exception as e:
        print(f"\n[Критическая ошибка] Произошел сбой при обработке запроса: {e}")
        print("Вы можете продолжить отправку запросов.\n")
        print("-" * 60)
