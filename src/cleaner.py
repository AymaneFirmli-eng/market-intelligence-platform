"""
ETL Pipeline: Data Cleaning & Transformation (Bronze -> Silver Layer).
Extracts raw data from 'bronze_products', applies regex-based transformations,
type castings, and data filtering, then loads structured records into 'silver_products'.
"""

from __future__ import (
    annotations,  # Enable PEP 563 type hint annotations for Python <3.10
)

import re

import pandas as pd
import psycopg

# Database connection parameters
from src.credentials import DB_PARAMS

# Rating mapping dictionary: converts textual word ratings to integers
RATING_MAP = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5
}

# ------------------------------------------------------------------------------
# HELPER DATA CLEANER FUNCTIONS
# ------------------------------------------------------------------------------
def clean_price(val: str) -> float | None:
    """
    Extracts numeric float value from raw price string via regular expression.
    Example: "£51.77" -> 51.77
    """
    if not val:
        return None
    match = re.search(r"(\d+[\.,]?\d*)", str(val))
    return float(match.group(1).replace(",", ".")) if match else None

def clean_rating(val: str) -> int | None:
    """
    Converts raw text rating to an integer between 1 and 5.
    Example: "Three" -> 3
    """
    if not val:
        return None
    val_str = str(val).strip().lower()
    for key, score in RATING_MAP.items():
        if key in val_str:
            return score
    return None

def clean_stock(val: str) -> bool:
    """
    Parses availability string into a boolean stock indicator.
    Example: "In stock (22 available)" -> True
    """
    if not val:
        return False
    val_str = str(val).lower()
    return "in stock" in val_str or "available" in val_str or "oui" in val_str

# ------------------------------------------------------------------------------
# BRONZE TO SILVER ETL PIPELINE
# ------------------------------------------------------------------------------
def run_silver_etl():
    """
    Executes full Extract, Transform, Load (ETL) lifecycle:
    1. Extract  : Reads 'bronze_products' into a Pandas DataFrame.
    2. Transform: Applies vectorised regex cleaning and type conversions.
    3. Load     : Performs idempotent batch UPSERT into 'silver_products'.
    """
    print(" Starting ETL pipeline: Bronze -> Silver...")

    with psycopg.connect(**DB_PARAMS) as conn:
        # 1. EXTRACTION: Read from Bronze layer
        query_raw = "SELECT title, price_raw, rating_raw, availability_raw, category, product_url FROM bronze_products;"
        df_bronze = pd.read_sql_query(query_raw, conn)

        if df_bronze.empty:
            print(" No data found in bronze_products. Run scraper.py first.")
            return

        print(f" {len(df_bronze)} raw records extracted from bronze_products.")

        # 2. TRANSFORMATION: Clean and cast data types
        df_silver = pd.DataFrame()
        df_silver["title"] = df_bronze["title"].str.strip()
        df_silver["category"] = df_bronze["category"].str.strip()
        df_silver["price"] = df_bronze["price_raw"].apply(clean_price)
        df_silver["rating_score"] = df_bronze["rating_raw"].apply(clean_rating)
        df_silver["is_in_stock"] = df_bronze["availability_raw"].apply(clean_stock)
        df_silver["product_url"] = df_bronze["product_url"].str.strip()

        # Data Quality check: drop rows missing core required fields
        df_silver = df_silver.dropna(subset=["title", "price", "product_url"])

        # 3. LOADING: UPSERT Pattern (ON CONFLICT DO UPDATE)
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

        print(f" {len(df_silver)} clean product records inserted into silver_products!")

if __name__ == "__main__":
    run_silver_etl()