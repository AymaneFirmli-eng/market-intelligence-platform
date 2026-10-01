"""

UNIT TEST SUITE
===============================================================================
Tests core data transformation, sanitization, and feature engineering logic
used across the Bronze, Silver, and Gold pipelines.
===============================================================================
"""

import numpy as np
import pandas as pd
import pytest


# -----------------------------------------------------------------------------
# HELPER TRANSFORMATIONS (Mirroring cleaner.py & gold_etl.py logic)
# -----------------------------------------------------------------------------
def clean_price(price_str) -> float:
    """Sanitizes raw scraped price strings into float numbers."""
    if price_str is None or pd.isna(price_str):
        return np.nan
    import re

    cleaned = re.sub(r"[^\d.]", "", str(price_str).replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return np.nan


def compute_gold_features(df: pd.DataFrame) -> pd.DataFrame:
    """Computes Price Z-Score, Value Score, and Deal Flag on Silver data."""
    df = df.copy()
    mean_price = df["price"].mean()
    std_price = df["price"].std(ddof=0)

    if std_price == 0 or pd.isna(std_price):
        df["price_zscore"] = 0.0
    else:
        df["price_zscore"] = (df["price"] - mean_price) / std_price

    # Value Score formula: high rating + lower relative price
    df["value_score"] = (df["rating_score"] * 12) - (df["price_zscore"] * 15)

    # Opportunity condition: below average price & rating >= 4.0
    df["is_deal_opportunity"] = (df["price_zscore"] < 0.0) & (
        df["rating_score"] >= 4.0
    )
    return df


# -----------------------------------------------------------------------------
# PYTEST TEST CASES
# -----------------------------------------------------------------------------
def test_clean_price_valid_currency_formats():
    """Validates price cleaning across common scraped formatting variants."""
    assert clean_price("$1,299.99") == 1299.99
    assert clean_price(" $45.50 ") == 45.50
    assert clean_price("100.00 €") == 100.0
    assert clean_price("899") == 899.0


def test_clean_price_invalid_and_null_inputs():
    """Ensures improper data produces NaN without crashing the pipeline."""
    assert np.isnan(clean_price(None))
    assert np.isnan(clean_price("N/A"))
    assert np.isnan(clean_price(""))
    assert np.isnan(clean_price(np.nan))


def test_compute_gold_features_deal_detection():
    """Verifies Z-score calculation and deal flag logic on standard sample data."""
    sample_df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "title": ["Product A", "Product B", "Product C"],
            "price": [500.0, 1000.0, 1500.0],  # Mean = 1000
            "rating_score": [4.5, 4.0, 3.5],
        }
    )

    result_df = compute_gold_features(sample_df)

    # Product A: Price below average (Z-score < 0) and rating >= 4.0 -> Deal Opportunity
    assert bool(result_df.loc[0, "is_deal_opportunity"]) is True
    assert result_df.loc[0, "price_zscore"] < 0

    # Product C: High price (Z-score > 0) and rating < 4.0 -> Not a Deal
    assert bool(result_df.loc[2, "is_deal_opportunity"]) is False
    assert result_df.loc[2, "price_zscore"] > 0


def test_gold_features_zero_price_variance():
    """Handles edge case where all products in a batch have identical prices."""
    uniform_price_df = pd.DataFrame(
        {
            "id": [1, 2],
            "title": ["Item X", "Item Y"],
            "price": [250.0, 250.0],
            "rating_score": [4.2, 4.8],
        }
    )

    result_df = compute_gold_features(uniform_price_df)

    # Zero variance must yield Z-Scores of 0.0 without division by zero errors
    assert (result_df["price_zscore"] == 0.0).all()
    
    
# to run this test file:  pytest tests/ -v