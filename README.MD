# 🛒 Market Intelligence Platform

An **end-to-end** competitive intelligence and e-commerce market analysis platform combining **Data Engineering**, **Data Science / Machine Learning**, and **Generative AI (Local RAG)**.

---

## 🎯 Executive Summary & Business Impact

In retail and e-commerce, tracking pricing dynamics, inventory availability, and customer perception is crucial for strategic decision-making.

**Market Intelligence Platform** automates this entire value chain:
1. **Data Acquisition & Ingestion**: Automated multi-page web scraping and schema validation.
2. **Storage & Data Modeling (Medallion Architecture)**: Progressive data refining from raw (*Bronze*) to cleaned/typed (*Silver*) and analytical (*Gold*) data layers.
3. **Analytics & Machine Learning**: Price trend forecasting (time series) and customer sentiment classification (NLP).
4. **Generative AI & Local RAG**: Natural language query engine using a local LLM (`Ollama`) and vector store (`pgvector`).
5. **Interactive Dashboard**: Full-stack `Streamlit` application for analytics, ML inference, and AI agent interactions.

---

## 🧠 Core Competencies & Skills Demonstrated

- **Data Engineering**: Robust web scraping, high-performance DOM parsing (`selectolax`), schema validation (`Pydantic`), advanced SQL (`PostgreSQL 16`, `psycopg3`), Medallion data architecture (Bronze/Silver/Gold).
- **Data Science & Analytics**: Exploratory Data Analysis (EDA), statistical modeling, feature engineering, complex data cleaning and type coercion.
- **Machine Learning & NLP**: Time series forecasting (XGBoost / Prophet), text classification, and sentiment analysis.
- **Generative AI & Local RAG**: Vector embeddings (`sentence-transformers`), vector storage (`pgvector`), RAG pipeline, and local LLM orchestration (`Ollama`).
- **DevOps & Software Engineering**: Containerization (`Docker`, `Docker Compose`), environment isolation, version control (`Git` / `GitHub`), code quality, and testing (`pytest`, `ruff`).

---

## 🛠️ Tech Stack & Tooling

| Layer / Domain | Technology & Frameworks |
| :--- | :--- |
| **Infrastructure & Database** | Docker, Docker Compose, PostgreSQL 16, `pgvector` |
| **Ingestion & Data Pipeline** | Python 3.12, `httpx`, `selectolax`, `pydantic`, `psycopg3` |
| **Data Processing & Analytics** | Pandas, SQLAlchemy |
| **Machine Learning & NLP** | Scikit-learn, XGBoost, `sentence-transformers` |
| **Generative AI & Local RAG** | Ollama (Qwen / Llama 3), `pgvector` |
| **Application & Restitution** | Streamlit, FastAPI |
| **Code Quality & CI/CD** | Pytest, Ruff, GitHub Actions |

---

## 🏗️ Data Architecture (Medallion Pattern)

```text
[ E-Commerce Web Target ]
       │
       ▼ (Python Scraper / Selectolax / Pydantic Validation)
┌──────────────┐
│  BRONZE      │  bronze_products (Raw uncleaned data: text prices, ratings, URLs)
└──────┬───────┘
       │
       ▼ (ETL Cleaner / Regex Transformation / Type Casting)
┌──────────────┐
│  SILVER      │  silver_products (Typed data: Numeric, Int, Booleans, SQL Constraints)
└──────┬───────┘
       │
       ▼ (Feature Engineering / Sentiment Analysis / Vector Embeddings)
┌──────────────┐
│  GOLD        │  gold_analytics & vector_embeddings (ML-ready & Vector Search Layer)
└──────────────┘

## Project Structure 
Plaintext
ecomarket-intelligence/
├── data/               # Dossiers d'exports et données brutes/processées
├── sql/                # Scripts DDL de création des tables PostgreSQL
│   ├── 01_create_bronze_tables.sql
│   └── 02_create_silver_tables.sql
├── src/                # Code source de la plateforme
│   ├── db.py           # Connexion PostgreSQL & activation de pgvector
│   ├── scraper.py      # Extraction Web & Ingestion Bronze
│   └── cleaner.py      # Transformation ETL Bronze -> Silver
├── tests/              # Suite de tests unitaires et d'intégration
├── docker-compose.yml  # Orchestration du service PostgreSQL + pgvector
├── requirements.txt    # Dépendances Python versionnées
└── README.md           # Documentation du projet

