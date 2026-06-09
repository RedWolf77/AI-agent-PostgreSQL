from typing import Literal, TypedDict, Optional
from pydantic import BaseModel, Field
from datetime import date

# схема для LLM
class RouterSchema(BaseModel):
    intent: Literal["add_movie", "add_actor", "delete_movie", "unknown"] = Field(
        description= (
            "Точное намерение пользователя. "
            "ВНИМАТЕЛЬНО анализируй глаголы! "
            "Что пользователь хочет сделать? Возможно: добавления фильма, добавление актера, удаление фильма. "
        )
    )
    entity_name: str = Field(
        description="Название фильма или имя актера для поиска/добавления/удаления.",
        default=""
    )

# Состяния графа
class AgentState(TypedDict):
    user_query: str                          # Запрос пользователя
    intent: Optional[str]                    # Намерение (add_movie, и т.д.)
    extracted_name: Optional[str]            # Извлеченное название/имя
    found_records: Optional[list]            # Хранилище записей, найденных в БД перед удалением
    final_response: Optional[str]            # Итоговый ответ пользователю



###
### СХЕМЫ ДЛЯ БД
###

# Фильм
class MovieSchema(BaseModel):
    name: str = Field(description="Официальное название фильма")
    plot: str = Field(description="Краткое описание сюжета фильма")
    age_rating: int = Field(description="Возрастной ценз фильма (например: 0, 6, 12, 16, 18)")

# Актер
class ActorSchema(BaseModel):
    last_name: str = Field(description="Фамилия актера")
    first_name: str = Field(description="Имя актера")
    middle_name: Optional[str] = Field(
        description="Отчество актера (может быть пустым для тех, у кого его нет)",
        default=None
    )
    birth_date: date = Field(description="Дата рождения актера")
    death_date: Optional[date] = Field(
        description="Дата смерти актера (оставь пустой/Null, если актер жив)",
        default=None
    )

