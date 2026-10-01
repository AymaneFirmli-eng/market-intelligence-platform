"""
ML PART : RANDOMFORESTCLASSIFER

THEORY for RF  :
-------------------------------
1. RANDOM FOREST ARCHITECTURE (Ensemble Learning):
- Uses Bagging (Bootstrap <=> separating data attributes # columns and their type 
&  Aggregating <=> unifying democratically trees result) to build multiple unpruned Decision
    Trees in parallel.
- Bootstrapping: Each tree trains on a random subset of rows sampled WITH 
    replacement.
- Random Subspace: At each node split, the algorithm evaluates only a random
    subset of features (m = sqrt(p) GENERAL RULE ACCORDING TO des recherches).
    This decorrelates the trees so their individual errors cancel out when aggregated.

2. WHY JOBLIB INSTEAD OF PICKLE IN MODEL SAVING ?
- Standard Python `pickle` processes objects line-by-line, which is slow for
    huge blocks of numerical data and turns model data into bytes disregarding what they are (just text to byte kind of thing).
- `joblib` is optimized for Scikit-Learn objects containing C-contiguous (1 block 1 row) 
    NumPy arrays (like decision tree thresholds). It dumps raw memory blocks 
    directly to disk using zero-copy memory mapping.

3. CONFUSION MATRIX METRICS: (true/false = deal or not ; postive/neg = model detected the deal)
- True Positive (TP)  : Actual Deal = 1, Predicted Deal = 1. (Hit)
- True Negative (TN)  : Actual Normal = 0, Predicted Normal = 0. (Correct Rejection)
- False Positive (FP) : Actual Normal = 0, Predicted Deal = 1. (TYPE I ERROR)
                        *DANGEROUS*: False alarms destroy user trust in the platform.
- False Negative (FN) : Actual Deal = 1, Predicted Normal = 0. (TYPE II ERROR)
                        Missed bargain opportunity.

4. PERFORMANCE METRICS:
- Precision = TP / (TP + FP)  -> Quality of deal alerts (minimizes false alarms).
- Recall    = TP / (TP + FN)  -> Coverage of actual deals (minimizes missed deals).
- F1-Score  = 2 * (Precision * Recall) / (Precision + Recall) -> Balanced mean.
- ROC-AUC   = Ranks ability to score deals higher than non-deals across all 
                thresholds (1.0 = Perfect ranking, 0.5 = Random coin flip).
===============================================================================
"""

import json
import os

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# Import connection parameters from local credentials module
from credentials import DB_PARAMS


def load_gold_data() -> pd.DataFrame:
    """
    Fetches feature-engineered data from the Gold database layer joined with
    Silver raw product details.
    
    Returns:
        pd.DataFrame: A DataFrame containing numeric features and target labels.
    """
    query = """
        SELECT 
            sp.price,
            sp.rating_score,
            sp.is_in_stock::int AS in_stock,
            gps.price_zscore,
            gps.value_score,
            gps.is_deal_opportunity
        FROM gold_product_scores gps
        JOIN silver_products sp ON gps.id = sp.id;
    """

    # Establish connection using DB_PARAMS dictionary unpacking
    with psycopg.connect(**DB_PARAMS) as conn:
        df = pd.read_sql(query, conn)

    return df



def train_and_evaluate() -> None:
    """
    Loads Gold data, splits features/labels, trains a 100-tree RandomForest
    with real-time tqdm progress, evaluates performance metrics, and exports
    artifacts (joblib model, JSON metrics, Matplotlib figures).
    """
    # -------------------------------------------------------------------------
    # 1. LOAD DATA & VALIDATE
    # -------------------------------------------------------------------------
    print("Loading Gold layer data (joining on silver)...")
    df = load_gold_data()

    # Feature selection (X) and Target label (y)
    X = df[
        ["price", "rating_score", "in_stock", "price_zscore", "value_score"]
    ].fillna(0)
    y = df["is_deal_opportunity"]

    # SAFE PANDAS VALIDATION:
    # Evaluating `if not X` or `if not y` causes a `ValueError: The truth value 
    # of a DataFrame/Series is ambiguous` in Pandas. `.empty` checks dimension size safely.
    if X.empty or y.empty:
        raise ValueError("Gold table is empty or missing data. Please run gold_etl.py first.")

    # -------------------------------------------------------------------------
    # 2. TRAIN / TEST SPLIT (STRATIFIED)
    # -------------------------------------------------------------------------
    # - test_size=0.2 : Reserves 20% of data for un-seen testing evaluation.
    # - random_state=42 : Freezes the random seed for reproducible splits.
    # - stratify=y : Ensures the exact ratio of Deals (1) vs Normal (0) is 
    #   preserved in both training and testing sets, preventing zero-recall bias.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # -------------------------------------------------------------------------
    # 3. INCREMENTAL ENSEMBLE TRAINING (BOOTSTRAPPING & BAGGING)
    # -------------------------------------------------------------------------
    print("Training RandomForestClassifier...")
    n_trees = 100
    
    # warm_start=True allows adding trees incrementally to monitor progress via tqdm
    clf = RandomForestClassifier(warm_start=True, random_state=42)

    for i in tqdm(range(1, n_trees + 1), desc="Fitting Trees", unit="tree"):
        clf.n_estimators = i
        clf.fit(X_train, y_train)

    # -------------------------------------------------------------------------
    # 4. MODEL INFERENCE & EVALUATION
    # -------------------------------------------------------------------------
    # Hard predictions (0 or 1) based on default 0.5 threshold
    y_pred = clf.predict(X_test)
    
    # Probability scores (0.0 to 1.0) for deal class confidence
    y_proba = clf.predict_proba(X_test)[:, 1]
    
    # ALTERNATIVE TO GET MORE/LESS ACCURACY DEPENDING ON THE ACTUAL USER PREFERENCE
    # REPLACE y_predict by a strict rule (NOT 50% as .predict does) put the two lines below instead (80% example)
    # y_proba = clf.predict_proba(X_test)[:, 1]
    #y_pred_strict = (y_proba >= 0.80).astype(int)
    
    

    # Calculate Precision, Recall, F1-Score, and ROC-AUC
    report = classification_report(y_test, y_pred, output_dict=True)
    auc = float(roc_auc_score(y_test, y_proba))

    print(f"Model trained successfully. ROC-AUC Score: {auc:.4f}")

    # -------------------------------------------------------------------------
    # 5. SERIALIZE MODEL ARTIFACT (JOBLIB)
    # -------------------------------------------------------------------------
    # joblib memory-maps NumPy array representations of tree splits directly 
    # to disk, bypassing slow Python object loops.
    os.makedirs("data/models", exist_ok=True)
    model_path = "data/models/random_forest_deal_detector.joblib"
    joblib.dump(clf, model_path)
    print(f"Model serialized to: {model_path}")

    # -------------------------------------------------------------------------
    # 6. EXPORT METRICS JSON
    # -------------------------------------------------------------------------
    os.makedirs("results/metrics", exist_ok=True)
    metrics = {"roc_auc": auc, "classification_report": report}
    with open("results/metrics/metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)

    # -------------------------------------------------------------------------
    # 7. GENERATE VISUAL ANALYTICS (MATPLOTLIB)
    # -------------------------------------------------------------------------
    os.makedirs("results/figures", exist_ok=True)

    # A. Confusion Matrix Plot
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(5, 4))
    plt.imshow(cm, cmap="Blues")
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted Label (0 = Normal, 1 = Deal)")
    plt.ylabel("Actual Label (0 = Normal, 1 = Deal)")
    
    # Annotate matrix cells with raw counts
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(
                j,
                i,
                str(cm[i, j]),
                ha="center",
                va="center",
                color="red" if cm[i, j] > cm.max() / 2 else "black",
            )
    plt.tight_layout()
    plt.savefig("results/figures/confusion_matrix.png")
    plt.close()

    # B. Feature Importance Plot (Mean Decrease in Impurity / Gini Impurity)
    importances = clf.feature_importances_
    features = X.columns
    indices = np.argsort(importances)

    plt.figure(figsize=(6, 4))
    plt.title("Feature Importance (Gini Impurity Drop)")
    plt.barh(range(len(indices)), importances[indices], align="center")
    plt.yticks(range(len(indices)), [features[i] for i in indices])
    plt.xlabel("Relative Importance")
    plt.tight_layout()
    plt.savefig("results/figures/feature_importance.png")
    plt.close()

    print("Visual analytics exported to results/figures/")


if __name__ == "__main__":
    train_and_evaluate()