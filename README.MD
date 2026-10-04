# 🛒 E-Commerce Market Intelligence Platform

[![CI Pipeline](https://github.com/AymaneFirmli-eng/market-intelligence-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/AymaneFirmli-eng/market-intelligence-platform/actions)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Database](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-blue)
![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-000000.svg)

An enterprise-grade, end-to-end market intelligence and deal detection engine. Built on a multi-stage **Medallion Data Architecture** (Bronze → Silver → Gold), this platform automates web data extraction, relational storage, statistical feature engineering, machine learning deal classification, and local **Retrieval-Augmented Generation (RAG)** querying.

---

## 🎯 Executive Summary & Business Impact

In competitive retail and e-commerce, tracking price volatility, discount signals, and market positioning in real time is essential for strategic decision-making. 

This platform automates the entire analytics pipeline:
1. **Automated Data Ingestion**: Multi-page web scraping with DOM parsing (`selectolax`) and runtime schema enforcement (`Pydantic`).
2. **Refined Data Storage**: Progressive data transformation inside **PostgreSQL 16** using the **Medallion Architecture** pattern.
3. **Feature Engineering & ML Scoring**: Automated statistical baseline calculation (Price Z-Scores) and **Random Forest classification** to identify high-confidence bargain deals while minimizing false positives.
4. **Local RAG Agent**: Natural language retrieval over domain tables and vector embeddings (`pgvector`) powered by local LLMs (`Ollama`).
5. **Production UI & CI/CD**: Interactive **Streamlit** executive dashboard backed by an automated **GitHub Actions** testing and linting suite.

---

## 🏗️ System Architecture (Medallion Pattern)

```text
               [ Target E-Commerce Data Source ]
                               │
                               ▼ (httpx / selectolax / Pydantic validation)
 ┌───────────────────────────────────────────────────────────┐
 │ BRONZE LAYER  │ raw_products                              │
 │               │ Raw scraped payloads & unparsed string fields │
 └─────────────────────────────┬─────────────────────────────┘
                               │
                               ▼ (Regex sanitization / Type casting / DDL constraints)
 ┌───────────────────────────────────────────────────────────┐
 │ SILVER LAYER  │ silver_products                           │
 │               │ Sanitized relational schema (Floats, Ints) │
 └─────────────────────────────┬─────────────────────────────┘
                               │
                               ▼ (Z-Score calculation / Value Score / Deal Flagging)
 ┌───────────────────────────────────────────────────────────┐
 │ GOLD LAYER    │ gold_market_intelligence                  │
 │               │ ML-ready feature store & analytics layer  │
 └──────────────┬─────────────────────────────┬──────────────┘
                │                             │
                ▼                             ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│ Machine Learning Pipeline     │ │ RAG & Vector Engine           │
│ Random Forest Deal Classifier │ │ SQL/pgvector Retrieval Agent  │
└──────────────┬────────────────┘ └──────────────┬────────────────┘
               │                                 │
               └────────────────┬────────────────┘
                                │
                                ▼
               ┌─────────────────────────────────┐
               │ Streamlit Executive Dashboard   │
               └─────────────────────────────────┘
```

---

## 🛠️ Tech Stack & Tooling

| Layer | Technology & Tools |
| :--- | :--- |
| **Infrastructure & Database** | Docker Compose, PostgreSQL 16, `pgvector` |
| **Ingestion & Validation** | Python 3.10+, `httpx`, `selectolax`, `Pydantic v2` |
| **Database Drivers & ORM** | `psycopg3`, `SQLAlchemy`, `pandas` |
| **Machine Learning** | `scikit-learn` (Random Forest), `numpy`, `joblib` |
| **Generative AI & RAG** | Local LLM (`Ollama` / Qwen / Llama 3), `pgvector` embeddings |
| **User Interface** | `Streamlit` |
| **Code Quality & CI/CD** | `pytest`, `ruff`, GitHub Actions |

---

## 📂 Project Structure

```text
market-intelligence-platform/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI workflow (Ruff + Pytest)
├── data/                       # Local raw and processed dataset exports
├── results/                    # Machine learning evaluation artifacts
│   ├── figures/                # Visualizations (e.g., confusion matrix PNG)
│   └── metrics/                # Exported model metrics (JSON)
├── sql/                        # Relational DDL schema definitions
│   ├── 01_create_bronze_tables.sql
│   ├── 02_create_silver_tables.sql
│   └── 03_create_gold_tables.sql
├── src/                        # Platform source code
│   ├── __init__.py
│   ├── cleaner.py              # Bronze -> Silver ETL cleaning pipeline
│   ├── credentials.py          # Secure environment variables loader
│   ├── db.py                   # PostgreSQL connection & pgvector initializer
│   ├── gold_etl.py             # Silver -> Gold feature engineering pipeline
│   ├── rag_agent.py            # Natural language RAG retrieval engine
│   ├── scraper.py              # Asynchronous scraper & Bronze layer ingestion
│   └── train_model.py          # Random Forest classifier training & evaluation
├── tests/                      # Automated unit test suite
│   └── test_pipelines.py       # Data sanitization & feature calculation tests
├── .env.example                # Environment variables template
├── .gitignore                  # Git exclusion rule list
├── app.py                      # Multi-tab Streamlit dashboard application
├── docker-compose.yml          # Containerized PostgreSQL 16 + pgvector setup
├── requirements.txt            # Version-locked dependency manifest
└── README.md                   # Platform documentation
```

---

## 🚀 Quickstart & Execution Guide

Follow these steps to set up and run the platform locally from scratch.

### 1. Prerequisites
- **Python 3.10+**
- **Docker** and **Docker Compose**
- **Git**

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/AymaneFirmli-eng/market-intelligence-platform.git
cd market-intelligence-platform

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the template file to create your local `.env` configuration:
```bash
cp .env.example .env
```
Ensure your `.env` contains the required local database credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=market_db
DB_USER=postgres
DB_PASSWORD=postgres
```

### 4. Launch Database Service
Spin up the containerized PostgreSQL database with the `pgvector` extension:
```bash
docker-compose up -d
```

Initialize the database schema and enable the `vector` extension:
```bash
python -m src.db
```

---

## 🔄 Running the End-to-End Pipeline

Execute the pipeline stages sequentially to ingest, refine, score, and model market data:

### Stage 1: Ingest Raw Data (Bronze Layer)
Scrapes product listings and writes raw payloads to `bronze_products`:
```bash
python -m src.scraper
```

### Stage 2: Clean & Sanitize (Silver Layer)
Transforms raw string values into standardized numeric types and loads `silver_products`:
```bash
python -m src.cleaner
```

### Stage 3: Feature Engineering (Gold Layer)
Computes Z-scores, composite Value Scores, and populates `gold_market_intelligence`:
```bash
python -m src.gold_etl
```

### Stage 4: Train Deal Classification Model
Trains a Random Forest classifier, evaluates metrics, and exports artifacts to `results/`:
```bash
python -m src.train_model
```

### Stage 5: Launch Streamlit Executive Dashboard
Start the interactive dashboard to visualize market trends, inspect model metrics, and interact with the RAG agent:
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧪 Testing & Quality Assurance

Maintain code quality and verify business logic using the automated testing and linting tools:

### Run Code Linter (`ruff`)
```bash
ruff check src/
```

### Run Unit Test Suite (`pytest`)
Executes assertions against price parsing, edge cases, and statistical feature calculations:
```bash
pytest tests/ -v
```

---

## 🛡️ Engineering & Security Standards

- **Zero Credential Leaks**: Sensitive access keys are completely decoupled from source code using `.env` files managed via `python-dotenv`.
- **Automated Continuous Integration**: Every push or pull request to `main` triggers a GitHub Actions workflow (`.github/workflows/ci.yml`) that lints the codebase and runs unit test assertions.
- **Strict Lint Compliance**: Formatted according to PEP 8 standards using `ruff`.

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).