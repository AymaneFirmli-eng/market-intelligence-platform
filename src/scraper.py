"""
Web Scraping & Raw Data Ingestion Module (Bronze Layer).
Uses HTTPX for networking, Selectolax for high-performance HTML parsing,
Pydantic for schema validation, and Psycopg for idempotent PostgreSQL UPSERT.
"""

from __future__ import annotations
import httpx
from selectolax.parser import HTMLParser
from pydantic import BaseModel, Field
import psycopg

# PostgreSQL connection parameters
DB_PARAMS = {
    "dbname": "ecomarket_db",
    "user": "ecomarket_user",
    "password": "ecomarket_password",
    "host": "localhost",
    "port": "5432"
}

# ------------------------------------------------------------------------------
# DATA CONTRACT (Pydantic Model)
# ------------------------------------------------------------------------------
class RawProduct(BaseModel):
    """
    Validation schema for raw scraped product data.
    Enforces data contract before database ingestion.
    """
    title: str = Field(..., description="Product title")
    price_raw: str = Field(..., description="Raw text price (e.g. £51.77)")
    rating_raw: str = Field(..., description="Raw text rating (e.g. Three)")
    availability_raw: str = Field(..., description="Raw stock availability string")
    category: str = Field(..., description="Product category name")
    product_url: str = Field(..., description="Product detail URL")

# ------------------------------------------------------------------------------
# DOM PARSER (Selectolax Engine)
# ------------------------------------------------------------------------------
def parse_category_page(html_content: str, category_name: str) -> list[RawProduct]:
    """
    Parses catalog page HTML and extracts validated raw product records.

    Args:
        html_content (str): Raw HTML payload.
        category_name (str): Assigned category label.

    Returns:
        list[RawProduct]: List of Pydantic-validated product objects.
    """
    tree = HTMLParser(html_content)
    products = []

    # Iterate over product container nodes in DOM
    for node in tree.css("article.product_pod"):
        title_node = node.css_first("h3 a")
        price_node = node.css_first(".price_color")
        rating_node = node.css_first("p.star-rating")
        stock_node = node.css_first(".instock.availability")

        if title_node and price_node:
            title = title_node.attributes.get("title") or title_node.text(strip=True)
            url = title_node.attributes.get("href", "")
            price_raw = price_node.text(strip=True)
            
            # Extract star rating class (e.g. "star-rating Three" -> "Three")
            rating_classes = rating_node.attributes.get("class", "") if rating_node else ""
            rating_raw = rating_classes.replace("star-rating", "").strip()
            
            availability_raw = stock_node.text(strip=True) if stock_node else ""

            # Instantiation & Pydantic schema validation
            raw_p = RawProduct(
                title=title,
                price_raw=price_raw,
                rating_raw=rating_raw,
                availability_raw=availability_raw,
                category=category_name,
                product_url=url
            )
            products.append(raw_p)

    return products

# ------------------------------------------------------------------------------
# DATABASE INGESTION (Bronze Layer / UPSERT Pattern)
# ------------------------------------------------------------------------------
def save_to_bronze(products: list[RawProduct]) -> None:
    """
    Inserts raw product records into 'bronze_products'.
    Uses 'ON CONFLICT DO UPDATE' (UPSERT) to guarantee pipeline idempotency.
    """
    if not products:
        return

    # Idempotent SQL query handling URL conflicts
    sql = """
    INSERT INTO bronze_products (title, price_raw, rating_raw, availability_raw, category, product_url)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (product_url) DO UPDATE SET
        title = EXCLUDED.title,
        price_raw = EXCLUDED.price_raw,
        rating_raw = EXCLUDED.rating_raw,
        availability_raw = EXCLUDED.availability_raw,
        category = EXCLUDED.category;
    """

    records = [
        (p.title, p.price_raw, p.rating_raw, p.availability_raw, p.category, p.product_url)
        for p in products
    ]

    with psycopg.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, records)
            conn.commit()

# ------------------------------------------------------------------------------
# MULTI-PAGE SCRAPING ORCHESTRATION
# ------------------------------------------------------------------------------
def run_scraper():
    """
    Orchestrates web scraping execution across all catalog pages (50 pages).
    """
    base_url = "http://books.toscrape.com/catalogue/page-{}.html"
    total_scraped = 0
    print(" Starting Web Scraper...")

    with httpx.Client(timeout=10.0) as client:
        for page in range(1, 51):
            url = base_url.format(page)
            response = client.get(url)

            if response.status_code == 200:
                products = parse_category_page(response.text, category_name="General")
                save_to_bronze(products)
                total_scraped += len(products)
                print(f" Page {page}/50 processed: {len(products)} records ingested into bronze_products.")
            else:
                print(f" Request failed for page {page} (Status: {response.status_code})")

    print(f" Scraping complete! Total: {total_scraped} records stored in Bronze layer.")

if __name__ == "__main__":
    run_scraper()