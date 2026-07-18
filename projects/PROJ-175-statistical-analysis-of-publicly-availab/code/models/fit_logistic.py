import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def load_processed_data():
    path = project_root / "data" / "final" / "train_set.parquet"
    if not path.exists():
        raise FileNotFoundError("train_set.parquet not found.")
    return pd.read_parquet(path)

def prepare_features(df):
    """Prepare features for logistic regression."""
    # Simplified feature selection
    features = ["log_co_occurrence", "flavor_similarity"]
    # Handle categorical role
    if "role_label" in df.columns:
        df = pd.get_dummies(df, columns=["role_label"], drop_first=True)
        features.extend([c for c in df.columns if c.startswith("role_label_")])
    
    X = df[features].fillna(0)
    y = df["compatibility_label"] if "compatibility_label" in df.columns else pd.Series([0]*len(df))
    return X, y, features

def fit_logistic_models(X, y, features):
    """Fit Null and Full models."""
    # Null model (frequency only)
    X_null = X[["log_co_occurrence"]] if "log_co_occurrence" in X.columns else X.iloc[:, :1]
    model_null = LogisticRegression(penalty='l2', solver='lbfgs', max_iter=1000)
    model_null.fit(X_null, y)
    y_pred_null = model_null.predict_proba(X_null)[:, 1]
    auc_null = roc_auc_score(y, y_pred_null)

    # Full model
    model_full = LogisticRegression(penalty='l2', solver='lbfgs', max_iter=1000)
    model_full.fit(X, y)
    y_pred_full = model_full.predict_proba(X)[:, 1]
    auc_full = roc_auc_score(y, y_pred_full)

    return {
        "null": {"model": model_null, "auc": auc_null},
        "full": {"model": model_full, "auc": auc_full}
    }

def save_models_and_results(results):
    """Save models and results."""
    data_dir = project_root / "data" / "final"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output = {
        "null_auc": results["null"]["auc"],
        "full_auc": results["full"]["auc"],
        "delta": results["full"]["auc"] - results["null"]["auc"]
    }
    
    with open(data_dir / "logistic_results.json", 'w') as f:
        json.dump(output, f, indent=2)

def main():
    """Main logistic regression entry point."""
    df = load_processed_data()
    X, y, features = prepare_features(df)
    results = fit_logistic_models(X, y, features)
    save_models_and_results(results)
    print("Logistic regression completed.")

if __name__ == "__main__":
    main()
