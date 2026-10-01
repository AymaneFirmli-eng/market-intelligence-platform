import psycopg

DB_PARAMS = {
    "dbname": "ecomarket_db",
    "user": "ecomarket_user",
    "password": "ecomarket_password",
    "host": "localhost",
    "port": "5432"
}

def init_db():
    try:
        with psycopg.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                print(" Connexion réussie à PostgreSQL depuis Python !")
                print(f" Version : {version[0]}")
                print(" Extension 'vector' (pgvector) activée avec succès.")
    except Exception as e:
        print(f" Erreur de connexion : {e}")

if __name__ == "__main__":
    init_db()
    
    