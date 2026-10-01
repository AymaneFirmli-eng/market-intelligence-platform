from pathlib import Path
import psycopg

DB_PARAMS = {
    "dbname": "ecomarket_db",
    "user": "ecomarket_user",
    "password": "ecomarket_password",
    "host": "localhost",
    "port": "5432"
}

def execute_sql_file(file_path: Path):
    """Exécute un fichier .sql complet dans PostgreSQL."""
    with psycopg.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cur:
            with open(file_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
                cur.execute(sql_script)
            conn.commit()
            print(f" Exécuté avec succès : {file_path.name}")

def init_db():
    try:
        # Activer pgvector
        with psycopg.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
        
        # Exécuter les scripts de création de tables dans le dossier sql
        sql_dir = Path(__file__).parent.parent / "sql"
        for sql_file in sorted(sql_dir.glob("*.sql")):
            execute_sql_file(sql_file)

    except Exception as e:
        print(f" Erreur lors de l'initialisation : {e}")

if __name__ == "__main__":
    init_db()