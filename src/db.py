"""
Database Connection & Initialization Module for PostgreSQL.
Verifies server health and ensures 'pgvector' extension availability at startup.
"""

import psycopg

# Connection parameters for local Docker container
from src.credentials import DB_PARAMS




def init_db() -> None:
    """
    Establishes database connection, checks SGBD version,
    and enables the 'pgvector' extension if not present.
    """
    try:
        with psycopg.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                # 1. Verify PostgreSQL version
                cur.execute("SELECT version();")
                version = cur.fetchone()
                
                # 2. Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                
                print(" Successfully connected to PostgreSQL from Python!")
                print(f" SGBD Version: {version[0] if version else 'Unknown'}")
                print(" 'vector' extension (pgvector) successfully enabled.")
    except Exception as e:
        print(f" Database connection error: {e}")

if __name__ == "__main__":
    init_db()