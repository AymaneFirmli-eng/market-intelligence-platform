"""
===============================================================================
Minimalistic Retrieval-Augmented Generation (RAG) pipeline:
1. Retrieval: Queries PostgreSQL Gold/Silver tables for top deal opportunities.
2. Context Synthesis: Formats structured DB records into natural language insights.
===============================================================================
"""

import pandas as pd
import psycopg
from src.credentials import DB_PARAMS


def retrieve_deal_context(
    query_keyword: str = "", limit: int = 5
) -> pd.DataFrame:
    """
    RETRIEVAL STEP: Fetches top deal opportunities from PostgreSQL 
    based on optional product title keywords and Value Score ranking.
    """
    # FIXED: Changed `gps.is_deal_opportunity = 1` to `gps.is_deal_opportunity = TRUE`
    base_query = """
        SELECT 
            sp.title,
            sp.price,
            sp.rating_score,
            gps.price_zscore,
            gps.value_score
        FROM gold_product_scores gps
        JOIN silver_products sp ON gps.id = sp.id
        WHERE gps.is_deal_opportunity = TRUE
    """

    params = []
    if query_keyword:
        base_query += " AND LOWER(sp.title) LIKE %s"
        params.append(f"%{query_keyword.lower()}%")

    base_query += " ORDER BY gps.value_score DESC LIMIT %s;"
    params.append(limit)

    with psycopg.connect(**DB_PARAMS) as conn:
        df = pd.read_sql(base_query, conn, params=params)

    return df


def generate_market_insight(user_prompt: str) -> str:
    """
    GENERATION STEP: Extracts key search intent from prompt, retrieves 
    relevant DB records, and returns a formatted natural language response.
    """
    # Simple keyword parsing for retrieval routing
    keyword = ""
    for word in user_prompt.split():
        if len(word) > 3 and word.lower() not in [
            "show", "find", "best", "deals", "cheap", "top", "with"
        ]:
            keyword = word
            break

    df_deals = retrieve_deal_context(query_keyword=keyword, limit=5)

    if df_deals.empty:
        return f"No specific deal opportunities found matching '{keyword or user_prompt}'."

    # Build response text
    response_lines = [
        f"### 🤖 Market Intelligence Report (Found {len(df_deals)} Top Deals)\n"
    ]

    for _, row in df_deals.iterrows():
        title = row["title"]
        price = row["price"]
        rating = row["rating_score"]
        zscore = row["price_zscore"]
        value_score = row["value_score"]

        response_lines.append(
            f"- **{title}**\n"
            f"  - **Price:** ${price:.2f} | **Rating:** {rating:.1f} ⭐\n"
            f"  - **Price Z-Score:** `{zscore:.2f}` (vs. category avg) | "
            f"**Value Score:** `{value_score:.1f}/100`\n"
        )

    return "\n".join(response_lines)


if __name__ == "__main__":
    # Test sample query
    sample_query = "Find me top deals for laptop"
    print(generate_market_insight(sample_query))