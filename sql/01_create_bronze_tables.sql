-- Couche Bronze : Données brutes (Landing Zone)
CREATE TABLE IF NOT EXISTS bronze_products (
    id SERIAL PRIMARY KEY,
    title TEXT,
    price_raw TEXT,
    rating_raw TEXT,
    availability_raw TEXT,
    category TEXT,
    product_url TEXT UNIQUE,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);