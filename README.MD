# 🛒 Market Intelligence Platform 🛒

Une plateforme **End-to-End** de veille concurrentielle et d'analyse marché e-commerce, combinant **Data Engineering**, **Data Science / Machine Learning** et **IA Générative (RAG)**.

---

##  Description Globale & Objectif Métier

Dans le secteur du retail et de l'e-commerce, suivre en continu la dynamique des prix, la disponibilité des produits et la perception des clients est stratégique.

**Market Intelligence Platform** automatise cette chaîne de valeur décisionnelle :
1. **Acquisition & Ingestion** : Extraction automatisée et asynchrone des catalogues produits.
2. **Stockage & Modélisation (Medallion Architecture)** : Traitement progressif des données brutes (*Bronze*) vers des données nettoyées et structurées (*Silver* / *Gold*).
3. **Analytics & Machine Learning** : Prédiction de tendances de prix (séries temporelles) et analyse de sentiment des avis clients (NLP).
4. **Agent IA & RAG Local** : Agent conversationnel basé sur un LLM local (`Ollama` + `pgvector`) permettant d'interroger la base de données métier en langage naturel.
5. **Dashboard Interactif** : Interface `Streamlit` pour la restitution des analyses, des prédictions et des requêtes IA.

---

##  Compétences & Skills Mobilisés

- **Data Engineering** : Web scraping robuste, parsing DOM ultra-rapide (`selectolax`), validation de schéma (`Pydantic`), requêtage SQL avancé (`PostgreSQL 16`, `psycopg3`), modélisation Medallion (Bronze/Silver/Gold).
- **Data Science & Analytics** : Exploration de données (EDA), analyse statistique, feature engineering, typage et nettoyage de données complexes.
- **Machine Learning & NLP** : Prédiction de séries temporelles (XGBoost / Prophet), classification de texte et sentiment analysis.
- **IA Générative & RAG** : Vector embeddings (`sentence-transformers`), stockage vectoriel (`pgvector`), pipeline RAG et orchestration LLM local (`Ollama`).
- **DevOps & Software Engineering** : Conteneurisation (`Docker`, `Docker Compose`), gestion des dépendances isolées, versioning `Git` / `GitHub`, qualimétrie et tests (`pytest`, `ruff`).

---

##  Stack Technique

| Domaine | Technologies / Libraries |
| :--- | :--- |
| **Infrastructure & Database** | Docker, Docker Compose, PostgreSQL 16, `pgvector` |
| **Ingestion & Data Pipeline** | Python 3.12, `httpx`, `selectolax`, `pydantic`, `psycopg3` |
| **Data Processing & Analytics** | Pandas, SQLAlchemy |
| **Machine Learning & NLP** | Scikit-learn, XGBoost, `sentence-transformers` |
| **IA Générative & Agent** | Ollama (Qwen / Llama 3), `pgvector` |
| **Application & Restitution** | Streamlit, FastAPI |
| **Qualité & CI/CD** | Pytest, Ruff, GitHub Actions |

---

##  Architecture des Données (Medallion Architecture)

```text
[ Web E-Commerce ]
       │
       ▼ (Scraper Python / Selectolax / Pydantic)
┌──────────────┐
│  BRONZE      │  bronze_products (Données brutes : prix textuels, notes en texte, URLs)
└──────┬───────┘
       │
       ▼ (ETL Cleaner / Transformers)
┌──────────────┐
│  SILVER      │  silver_products (Données typées : Numeric, Int, Booleans, Contraintes SQL)
└──────┬───────┘
       │
       ▼ (Aggregations / Sentiment Analysis / Embeddings Vectoriels)
┌──────────────┐
│  GOLD        │  gold_analytics / vector_embeddings (Tables prêtes pour ML & RAG)
└──────────────┘

##  Structure du Projet
Plaintext
ecomarket-intelligence/
├── data/               # Dossiers d'exports et données brutes/processées
├── sql/                # Scripts DDL de création des tables PostgreSQL
│   ├── 01_create_raw_tables.sql
│   └── 02_create_cleaned_tables.sql
├── src/                # Code source de la plateforme
│   ├── db.py           # Connexion PostgreSQL & activation de pgvector
│   ├── scraper.py      # Extraction Web & Ingestion Bronze
│   └── cleaner.py      # Transformation ETL Bronze -> Silver
├── tests/              # Suite de tests unitaires et d'intégration
├── docker-compose.yml  # Orchestration du service PostgreSQL + pgvector
├── requirements.txt    # Dépendances Python versionnées
└── README.md           # Documentation du projet


## Installation & Démarrage Rapide
 ** Cloner le projet et configurer l'environnement : **

Bash
git clone [https://github.com/AymaneFirmli-eng/ecomarket-intelligence.git](https://github.com/AymaneFirmli-eng/ecomarket-intelligence.git)
cd ecomarket-intelligence
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Lancer la base de données PostgreSQL via Docker :

Bash
docker compose up -d
Initialiser la base et l'extension vectorielle :

Bash
python src/db.py
Lancer l'ingestion Bronze (Web Scraping) :

Bash
python src/scraper.py
Exécuter la transformation Silver (Data Cleaning) :

Bash
python src/cleaner.py