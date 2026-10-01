import pandas as pd
import psycopg

DB_PARAMS = {
    "dbname": "ecomarket_db",
    "user": "ecomarket_user",
    "password": "ecomarket_password",
    "host": "localhost",
    "port": "5432"
}

def run_gold_etl():
    """
    Gold Layer ETL & Feature Engineering Pipeline.
    
    Transforms clean Silver data into analytics metrics and engineered features:
    - CONCEPT A: Category-level Price Z-Score (Statistical Normalization)
    - CONCEPT B: Value Score (Quality-to-Price Ratio Index)
    - CONCEPT C: Deal Opportunity Target Flag (Ground Truth Labeling)
    """
    print(" Starting Gold Layer ETL & Feature Engineering...")

    with psycopg.connect(**DB_PARAMS) as conn:
        # Load cleaned Silver products data
        query = "SELECT id, title, category, price, rating_score, is_in_stock, product_url FROM silver_products;"
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("ERROR! No data found in silver_products table.")
            return

        print(f"DONE! Loaded {len(df)} records from silver_products.")

        # ==============================================================================
        # PART 1: CATEGORY METRICS AGGREGATION (gold_category_metrics)
        # ==============================================================================
        cat_metrics = df.groupby("category").agg(
            total_products=("id", "count"),
            avg_price=("price", "mean"),
            min_price=("price", "min"),
            max_price=("price", "max"),
            in_stock_rate=("is_in_stock", lambda x: (x.sum() / len(x)) * 100)
        ).reset_index()

        cat_metrics["avg_price"] = cat_metrics["avg_price"].round(2)
        cat_metrics["min_price"] = cat_metrics["min_price"].round(2)
        cat_metrics["max_price"] = cat_metrics["max_price"].round(2)
        cat_metrics["in_stock_rate"] = cat_metrics["in_stock_rate"].round(2)

        upsert_cat_sql = """
        INSERT INTO gold_category_metrics (category, total_products, avg_price, min_price, max_price, in_stock_rate)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (category) DO UPDATE SET
            total_products = EXCLUDED.total_products,
            avg_price = EXCLUDED.avg_price,
            min_price = EXCLUDED.min_price,
            max_price = EXCLUDED.max_price,
            in_stock_rate = EXCLUDED.in_stock_rate,
            updated_at = CURRENT_TIMESTAMP;
        """

        cat_records = cat_metrics.to_records(index=False).tolist()
        with conn.cursor() as cur:
            cur.executemany(upsert_cat_sql, cat_records)
            conn.commit()
        print(f"DONE! Inserted {len(cat_metrics)} aggregated categories into gold_category_metrics.")

        # ==============================================================================
        # PART 2: FEATURE ENGINEERING (gold_product_scores)
        # ==============================================================================
        
        # ------------------------------------------------------------------------------
        # CONCEPT A: Category-Relative Price Z-Score
        # Formula: Z = (x - mu) / sigma
        # - x: Product price
        # - mu: Mean price within the product's category
        # - sigma: Standard deviation within the product's category
        # Quantifies how many standard deviations a price is from its category mean.
        # Negative Z-scores (Z <= -0.5) highlight items priced significantly below average.
        # ------------------------------------------------------------------------------
        def compute_zscore(x):
            std = x.std()
            return (x - x.mean()) / std if std > 0 else 0

        df["price_zscore"] = df.groupby("category")["price"].transform(compute_zscore).round(2)

        # Price Tier Categorization
        def get_price_tier(price):
            if price < 20:
                return "Budget"
            elif price < 40:
                return "Mid-Range"
            else:
                return "Premium"

        df["price_tier"] = df["price"].apply(get_price_tier)

        # ------------------------------------------------------------------------------
        # CONCEPT B: Value Score (Quality / Price Index)
        # Formula: Value Score = (Rating Score / Price) * 10
        # Measures cost-efficiency by comparing customer satisfaction (rating) 
        # directly against the product cost.
        # ------------------------------------------------------------------------------
        df["rating_score"] = df["rating_score"].fillna(3)  # Default median rating fallback
        df["value_score"] = ((df["rating_score"] / df["price"]) * 10).round(2)

        # ------------------------------------------------------------------------------
        # CONCEPT C: Deal Opportunity Target Flag (Ground Truth Target Label)
        # Condition: High Customer Satisfaction (Rating >= 4) AND Below-Average Price (Z <= -0.5)
        # Generates a binary boolean label (True/False) used as the target (y) for ML.
        # ------------------------------------------------------------------------------
        df["is_deal_opportunity"] = (df["rating_score"] >= 4) & (df["price_zscore"] <= -0.5)

        # Prepare payload for PostgreSQL upsert
        df_scores = df[["id", "product_url", "price_zscore", "price_tier", "value_score", "is_deal_opportunity"]].copy()
        df_scores.rename(columns={"id": "product_id"}, inplace=True)

        upsert_score_sql = """
        INSERT INTO gold_product_scores (product_id, product_url, price_zscore, price_tier, value_score, is_deal_opportunity)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_url) DO UPDATE SET
            price_zscore = EXCLUDED.price_zscore,
            price_tier = EXCLUDED.price_tier,
            value_score = EXCLUDED.value_score,
            is_deal_opportunity = EXCLUDED.is_deal_opportunity,
            updated_at = CURRENT_TIMESTAMP;
        """

        score_records = df_scores.to_records(index=False).tolist()
        with conn.cursor() as cur:
            cur.executemany(upsert_score_sql, score_records)
            conn.commit()

        print(f"DONE! Engineered features for {len(df_scores)} products inserted into gold_product_scores.")

if __name__ == "__main__":
    run_gold_etl()