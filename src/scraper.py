import time
from urllib.parse import urljoin
import httpx
from pydantic import BaseModel
from selectolax.parser import HTMLParser
import psycopg

DB_PARAMS = {
    "dbname": "ecomarket_db",
    "user": "ecomarket_user",
    "password": "ecomarket_password",
    "host": "localhost",
    "port": "5432"
}

BASE_URL = "http://books.toscrape.com/"

class RawProductItem(BaseModel):
    title: str
    price_raw: str
    rating_raw: str
    availability_raw: str
    category: str
    product_url: str


def get_category_urls(client: httpx.Client) -> dict[str, str]:
    """Récupère la liste des catégories et leurs URLs."""
    response = client.get(BASE_URL)
    parser = HTMLParser(response.text)
    categories = {}
    for a in parser.css("div.side_categories ul.nav-list ul li a"):
        cat_name = a.text(strip=True)
        cat_url = urljoin(BASE_URL, a.attributes.get("href", ""))
        categories[cat_name] = cat_url
    return categories


def scrape_category(client: httpx.Client, cat_name: str, cat_url: str) -> list[RawProductItem]:
    """Scrape toutes les pages d'une catégorie donnée."""
    products = []
    current_url = cat_url

    while current_url:
        resp = client.get(current_url)
        if resp.status_code != 200:
            break

        parser = HTMLParser(resp.text)
        for article in parser.css("article.product_pod"):
            title_elem = article.css_first("h3 a")
            title = title_elem.attributes.get("title", "") if title_elem else ""
            rel_link = title_elem.attributes.get("href", "") if title_elem else ""
            product_url = urljoin(current_url, rel_link)

            price_elem = article.css_first("p.price_color")
            price_raw = price_elem.text(strip=True) if price_elem else ""

            rating_elem = article.css_first("p.star-rating")
            rating_raw = ""
            if rating_elem:
                classes = rating_elem.attributes.get("class", "").split()
                rating_raw = [c for c in classes if c != "star-rating"][0] if len(classes) > 1 else ""

            avail_elem = article.css_first("p.instock.availability")
            availability_raw = avail_elem.text(strip=True) if avail_elem else ""

            item = RawProductItem(
                title=title,
                price_raw=price_raw,
                rating_raw=rating_raw,
                availability_raw=availability_raw,
                category=cat_name,
                product_url=product_url
            )
            products.append(item)

        next_page = parser.css_first("li.next a")
        if next_page:
            current_url = urljoin(current_url, next_page.attributes.get("href", ""))
        else:
            current_url = None

    return products


def save_raw_products(products: list[RawProductItem]):
    """Insertion par lot (bulk insert) dans la table raw_products."""
    query = """
    INSERT INTO bronze_products (title, price_raw, rating_raw, availability_raw, category, product_url)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (product_url) DO UPDATE SET
    price_raw = EXCLUDED.price_raw,
    rating_raw = EXCLUDED.rating_raw,
    availability_raw = EXCLUDED.availability_raw,
    scraped_at = CURRENT_TIMESTAMP;
    """
    with psycopg.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cur:
            data = [
                (p.title, p.price_raw, p.rating_raw, p.availability_raw, p.category, p.product_url)
                for p in products
            ]
            cur.executemany(query, data)
        conn.commit()


def main():
    print(" Démarrage du Web Scraping...")
    start_time = time.time()
    
    with httpx.Client(timeout=10.0) as client:
        categories = get_category_urls(client)
        print(f" {len(categories)} catégories trouvées.")
        
        total_scraped = 0
        for cat_name, cat_url in categories.items():
            products = scrape_category(client, cat_name, cat_url)
            if products:
                save_raw_products(products)
                total_scraped += len(products)
                print(f" Category '{cat_name}': {len(products)} produits sauvegardés.")

    elapsed = round(time.time() - start_time, 2)
    print(f"\n Scraping terminé en {elapsed}s ! Total: {total_scraped} produits insérés/mis à jour.")


if __name__ == "__main__":
    main()