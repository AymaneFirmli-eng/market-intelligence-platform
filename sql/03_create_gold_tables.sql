-- ==============================================================================
-- DATABASE SCHEMA: GOLD LAYER (ANALYTICS & ML FEATURES)
-- ==============================================================================

-- 1. Aggregated Category KPIs (Business Analytics)
CREATE TABLE IF NOT EXISTS gold_category_metrics (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) UNIQUE NOT NULL,
    total_products INT NOT NULL,
    avg_price NUMERIC(10, 2) NOT NULL,
    min_price NUMERIC(10, 2) NOT NULL,
    max_price NUMERIC(10, 2) NOT NULL,
    in_stock_rate NUMERIC(5, 2) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Product Intelligence & Feature Store (ML & Recommendation)
CREATE TABLE IF NOT EXISTS gold_product_scores (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES silver_products(id) ON DELETE CASCADE,
    product_url TEXT UNIQUE NOT NULL,
    price_zscore NUMERIC(6, 2),        -- Standardized price anomaly score within category
    price_tier VARCHAR(20),            -- Budget, Mid-range, Premium
    value_score NUMERIC(5, 2),         -- Calculated value index (Rating / Normalized Price)
    is_deal_opportunity BOOLEAN DEFAULT FALSE, -- Target flag for high-value deals
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);