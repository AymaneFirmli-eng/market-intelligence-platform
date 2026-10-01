-- ==============================================================================
-- DATABASE SCHEMA: MEDALLION ARCHITECTURE (BRONZE & SILVER)
-- ==============================================================================

-- Enable pgvector extension for vector embeddings & similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- ------------------------------------------------------------------------------
-- BRONZE LAYER (Raw Data / Landing Zone)
-- Stores raw web scraper output as ingested.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bronze_products (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    price_raw TEXT,                  -- e.g., "£51.77" (Uncleaned)
    rating_raw TEXT,                 -- e.g., "Three" (Uncleaned)
    availability_raw TEXT,           -- e.g., "In stock (22 available)"
    category TEXT,
    product_url TEXT UNIQUE NOT NULL, -- Business key for idempotency / UPSERT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- SILVER LAYER (Cleaned & Structured Data)
-- Stores typed, validated data ready for analytics, BI & Machine Learning.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS silver_products (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    category VARCHAR(100),
    price NUMERIC(10, 2) NOT NULL,   -- Cleaned numeric decimal price
    rating_score INT,                -- Extracted integer rating score (1-5)
    is_in_stock BOOLEAN DEFAULT TRUE,-- Parsed stock status boolean
    product_url TEXT UNIQUE NOT NULL, -- Uniqueness constraint for sync updates
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);