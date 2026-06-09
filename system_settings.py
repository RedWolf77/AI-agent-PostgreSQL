import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

os.environ["USER_AGENT"] = "MovieAgent/1.0 (Educational Academic Project)"

llm = ChatOpenAI(
    model="qwen2.5:7b",
    api_key="ollama",
    base_url="http://localhost:11434/v1",
    temperature=0
)

connection_config = {
    "dbname": "AI_Справочник_Фильмов",
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD"),
    "host": "localhost",
    "port": "5432"
}