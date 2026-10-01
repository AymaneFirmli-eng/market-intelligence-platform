import re
import psycopg
import pandas as pd

DB_PARAMS = {
    "dbname": "ecomarket_db",
    "user": "ecomarket_user",
    "password": "ecomarket_password",
    "host": "localhost",
    "port": "5432"
}

# Mapping des notes textuelles vers entiers
RATING_MAP = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5
}

def clean_price(val: str) -> float | None:
    """ Extrait la valeur numérique du prix """
    if not val:
        return None
    match = re.search(r"(\d+[\.,]?\d*)", str(val))
    return float(match.group(1).replace(",", ".")) if match else None

def clean_rating(val: str) -> int | None:
    """ Convertit le texte de note en entier """
    if not val:
        return None
    val_str = str(val).strip().lower()
    for key, score in RATING_MAP.items():
        if key in val_str:
            return score
    return None

def clean_stock(val: str) -> bool:
    """ Determine la disponibilite du produit """
    if not val:
        return False
    val_str = str(val).lower()
    return "in stock" in val_str or "available" in val_str or "oui" in val_str

def run_silver_etl():
    """ Execute le pipeline ETL Bronze vers Silver """
    print(" Démarrage du pipeline ETL Bronze -> Silver...")

    with psycopg.connect(**DB_PARAMS) as conn:
        # 1. Extraction depuis bronze_products
        query_raw = "SELECT title, price_raw, rating_raw, availability_raw, category, product_url FROM bronze_products;"
        df_bronze = pd.read_sql_query(query_raw, conn)

        if df_bronze.empty:
            print(" Aucune donnée trouvée dans bronze_products. Exécutez scraper.py d'abord.")
            return

        print(f" {len(df_bronze)} lignes brutes extraites de bronze_products.")

        # 2. Nettoyage et transformation
        df_silver = pd.DataFrame()
        df_silver["title"] = df_bronze["title"].str.strip()
        df_silver["category"] = df_bronze["category"].str.strip()
        df_silver["price"] = df_bronze["price_raw"].apply(clean_price)
        df_silver["rating_score"] = df_bronze["rating_raw"].apply(clean_rating)
        df_silver["is_in_stock"] = df_bronze["availability_raw"].apply(clean_stock)
        df_silver["product_url"] = df_bronze["product_url"].str.strip()

        # Suppression des lignes invalides
        df_silver = df_silver.dropna(subset=["title", "price", "product_url"])

        # 3. Insertion Upsert dans silver_products
        upsert_sql = """
        INSERT INTO silver_products (title, category, price, rating_score, is_in_stock, product_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_url) DO UPDATE SET
            title = EXCLUDED.title,
            category = EXCLUDED.category,
            price = EXCLUDED.price,
            rating_score = EXCLUDED.rating_score,
            is_in_stock = EXCLUDED.is_in_stock,
            updated_at = CURRENT_TIMESTAMP;
        """

        records = df_silver.to_records(index=False).tolist()
        
        with conn.cursor() as cur:
            cur.executemany(upsert_sql, records)
            conn.commit()

        print(f" {len(df_silver)} produits nettoyés et insérés dans silver_products !")

if __name__ == "__main__":
    run_silver_etl()