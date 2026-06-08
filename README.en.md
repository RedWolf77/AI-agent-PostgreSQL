# AI Agent for PostgreSQL DBMS

> **Project Status:** In Development

---

## Project Description
This project is a software implementation of an autonomous AI agent designed to automatically search, structure, modify, and save cinema-related information into a PostgreSQL relational database.

The system architecture is based on the **"Router"** pattern, which implements the concept of a **Lean State**. The developed agent automatically determines the user's intent, extracts named entities, performs asynchronous searches in open sources (Web Scraping), and executes strict data validation before writing it to the DBMS.

---

## Architecture and Technology Stack

### System Components:
* **Programming Language:** Python 3.10+
* **AI Frameworks:** LangChain, LangGraph (`StateGraph`)
* **Data Validation:** Pydantic v2
* **Database:** PostgreSQL (`psycopg2-binary` access driver)
* **Data Scraping:** DuckDuckGo Search API (`ddgs`), `WebBaseLoader`

---

## Deployment and Setup Instructions

### 1. Database Preparation
Before running the application, you need to deploy a PostgreSQL DBMS instance and initialize the table structure. If necessary, adapt the SQL queries to match your target data schema.

### 2. Environment Configuration
Create a `.env` configuration file in the root directory of the project and define the database connection parameters:

```env
DB_PASSWORD=your_postgres_password
```

### 3. Installing Dependencies

Install the required packages and libraries using the `pip` package manager:

```bash
pip install langchain langchain-openai langgraph psycopg2-binary pydantic duckduckgo-search python-dotenv
```

### 4. Running the Local LLM

To enable the agent's functionality, you need to run a local large language model via the Ollama platform:

```bash
ollama run your_llm_name
```

### 5. Running the AI Agent

Once the previous steps are successfully completed, initialize the main application script with the following command:

```bash
python main.py
```
