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

q = "Слушай, а добавь в базу фильм 'Начало' Кристофера Нолана"

print(f"ПОЛЬЗОВАТЕЛЬ: {q}")

result = app.invoke({"user_query": q})

print(f"\nОТВЕТ АГЕНТА: {result['final_response']}")