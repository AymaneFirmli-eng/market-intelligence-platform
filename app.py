"""

===============================================================================
Minimalistic dashboard providing:
1. Gold Layer Market Overview (Real deals fetched from PostgreSQL)
2. ML Model Performance (Loading saved metrics & evaluation figures)
3. Live Deal Detector (Interactive prediction using joblib model)
===============================================================================
"""

import json
import os
import joblib
import pandas as pd
import psycopg
import streamlit as st

# Connection parameters for local Docker PostgreSQL instance
from src.credentials import DB_PARAMS

# Page Configuration
st.set_page_config(
    page_title="Market Intelligence Dashboard",
    page_icon="🛍️",
    layout="wide"
)


@st.cache_data(ttl=300)
def load_gold_data() -> pd.DataFrame:
    """
    Fetches Gold layer scores joined with Silver raw product details.
    Cached for 5 minutes to optimize performance.
    """
    query = """
        SELECT 
            sp.title,
            sp.price,
            sp.rating_score,
            sp.is_in_stock::int AS in_stock,
            gps.price_zscore,
            gps.value_score,
            gps.is_deal_opportunity
        FROM gold_product_scores gps
        JOIN silver_products sp ON gps.id = sp.id
        ORDER BY gps.value_score DESC;
    """
    with psycopg.connect(**DB_PARAMS) as conn:
        df = pd.read_sql(query, conn)
    return df


# -----------------------------------------------------------------------------
# MAIN HEADER & TABS
# -----------------------------------------------------------------------------
st.title("🛍️ E-Commerce Market Intelligence Platform")
st.caption("Real-time PostgreSQL Medallion pipeline & Random Forest Deal Detection")

# In app.py, update st.tabs definition:
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Market Deals (Gold Data)",
    "📈 Model Performance",
    "🤖 Live Deal Predictor",
    "💬 AI Assistant (RAG)"
])




# =============================================================================
# TAB 1: GOLD LAYER MARKET OVERVIEW
# =============================================================================
with tab1:
    st.header("Gold Layer — Detected Bargains")

    try:
        df = load_gold_data()

        # Key Business Metrics
        col1, col2, col3 = st.columns(3)
        total_products = len(df)
        total_deals = int(df["is_deal_opportunity"].sum())
        deal_ratio = (total_deals / total_products * 100) if total_products > 0 else 0

        col1.metric("Scanned Products", f"{total_products}")
        col2.metric("Detected Deals", f"{total_deals}")
        col3.metric("Deal Ratio", f"{deal_ratio:.1f}%")

        st.divider()

        # Filter option
        show_deals_only = st.checkbox("Show only detected deal opportunities", value=True)
        
        display_df = df[df["is_deal_opportunity"] == 1] if show_deals_only else df

        st.dataframe(
            display_df,
            column_config={
                "price": st.column_config.NumberColumn("Price ($)", format="$%.2f"),
                "rating_score": st.column_config.NumberColumn("Rating", format="%.1f ⭐"),
                "price_zscore": st.column_config.NumberColumn("Price Z-Score", format="%.2f"),
                "value_score": st.column_config.NumberColumn("Value Score", format="%.1f"),
                "is_deal_opportunity": st.column_config.CheckboxColumn("Is Deal?"),
            },
            use_container_width=True,
            hide_index=True,
        )

    except Exception as e:
        st.error(f"Failed to load Gold layer data from PostgreSQL: {e}")


# =============================================================================
# TAB 2: MODEL PERFORMANCE MONITORING
# =============================================================================
with tab2:
    st.header("Random Forest Model Evaluation")

    metrics_path = "results/metrics/metrics.json"
    cm_path = "results/figures/confusion_matrix.png"
    fi_path = "results/figures/feature_importance.png"

    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            metrics = json.load(f)

        # High-level Scores
        col1, col2, col3 = st.columns(3)
        auc_score = metrics.get("roc_auc", 0.0)
        report = metrics.get("classification_report", {})
        deal_metrics = report.get("1", {})

        col1.metric("ROC-AUC Score", f"{auc_score:.4f}")
        col2.metric("Precision (Deal Class)", f"{deal_metrics.get('precision', 0.0):.2%}")
        col3.metric("Recall (Deal Class)", f"{deal_metrics.get('recall', 0.0):.2%}")

        st.divider()

        # Visualizations
        col_fig1, col_fig2 = st.columns(2)

        with col_fig1:
            st.subheader("Confusion Matrix")
            if os.path.exists(cm_path):
                st.image(cm_path, use_container_width=True)
            else:
                st.info("Confusion matrix plot not found.")

        with col_fig2:
            st.subheader("Feature Importance")
            if os.path.exists(fi_path):
                st.image(fi_path, use_container_width=True)
            else:
                st.info("Feature importance plot not found.")
    else:
        st.warning("No saved metrics found. Please run `python src/train_model.py` first.")


# =============================================================================
# TAB 3: LIVE DEAL PREDICTOR (INTERACTIVE INFERENCE)
# =============================================================================
with tab3:
    st.header("Predict Deal Opportunity in Real Time")
    st.caption("Input custom product features to test the trained Scikit-Learn `.joblib` model.")

    model_path = "data/models/random_forest_deal_detector.joblib"

    if os.path.exists(model_path):
        model = joblib.load(model_path)

        col_a, col_b = st.columns(2)

        with col_a:
            price = st.number_input("Product Price ($)", min_value=1.0, max_value=5000.0, value=89.99)
            rating_score = st.slider("Rating Score (1.0 to 5.0)", min_value=1.0, max_value=5.0, value=4.7, step=0.1)
            in_stock = st.selectbox("In Stock Status", options=[1, 0], format_func=lambda x: "Yes" if x == 1 else "No")

        with col_b:
            price_zscore = st.number_input("Price Z-Score (vs category avg)", value=-2.1, step=0.1)
            value_score = st.number_input("Calculated Value Score", value=88.5, step=1.0)

        st.divider()

        if st.button("Evaluate Product", type="primary"):
            # Construct DataFrame with exact feature names used during training
            input_features = pd.DataFrame([{
                "price": price,
                "rating_score": rating_score,
                "in_stock": in_stock,
                "price_zscore": price_zscore,
                "value_score": value_score
            }])

            # Inference
            prediction = model.predict(input_features)[0]
            probability = model.predict_proba(input_features)[0][1]

            if prediction == 1:
                st.success(f"🎉 **DEAL OPPORTUNITY DETECTED!** (Model Confidence: **{probability:.1%}**)")
            else:
                st.info(f"ℹ️ **STANDARD PRICE ITEM** (Model Confidence for Deal: **{probability:.1%}**)")
    else:
        st.warning("Model file `random_forest_deal_detector.joblib` missing. Run `train_model.py` to train and save the model.")
        
# =============================================================================
# TAB 4: Conversational bot
# =============================================================================
with tab4:
    st.header("Ask Market Intelligence Assistant")
    user_query = st.text_input(
        "Enter product category or search term:",
        value="laptop"
    )
    if st.button("Search Deals"):
        from src.rag_agent import generate_market_insight
        insight = generate_market_insight(user_query)
        st.markdown(insight)