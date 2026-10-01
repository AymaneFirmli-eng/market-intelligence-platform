-- Couche Silver : Données nettoyées et typées
CREATE TABLE IF NOT EXISTS silver_products (
    product_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    rating_score INT CHECK (rating_score BETWEEN 1 AND 5),
    is_in_stock BOOLEAN DEFAULT TRUE,
    product_url VARCHAR(500) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_silver_category ON silver_products(category);
CREATE INDEX IF NOT EXISTS idx_silver_price ON silver_products(price);