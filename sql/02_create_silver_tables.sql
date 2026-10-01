-- ==============================================================================
-- DATABASE SCHEMA: SILVER & GOLD LAYERS
-- ==============================================================================

-- Enable pgvector extension for vector embeddings & similarity search
CREATE EXTENSION IF NOT EXISTS vector;

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