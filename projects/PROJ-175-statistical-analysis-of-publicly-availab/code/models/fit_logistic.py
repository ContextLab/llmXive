"""
Logistic Regression Fitting Module
Fits Null and Full models with L2 regularization.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure project root is in path for imports if run as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.memory_monitor import check_memory_limit

def load_processed_data():
    """
    Loads the training data and predictor list.
    Expects:
      - data/processed/train_set.parquet (created by T019/split)
      - data/final_predictors.json (created by T040b)
    """
    train_path = project_root / "data" / "processed" / "train_set.parquet"
    predictors_path = project_root / "data" / "final_predictors.json"

    if not train_path.exists():
        raise FileNotFoundError(f"Training data not found at {train_path}. Run T019 first.")
    if not predictors_path.exists():
        raise FileNotFoundError(f"Predictor list not found at {predictors_path}. Run T040b first.")

    df = pd.read_parquet(train_path)
    with open(predictors_path, 'r') as f:
        config = json.load(f)
    
    predictors = config.get("predictors", [])
    
    # Validate columns
    missing = [col for col in predictors if col not in df.columns]
    if missing:
        raise ValueError(f"Predictors {missing} missing from training data.")
    
    if "compatibility_label" not in df.columns:
        raise ValueError("Target column 'compatibility_label' missing from training data.")

    return df, predictors

def prepare_features(df, predictors):
    """
    Separates features (X) and target (y).
    Handles categorical encoding if necessary (assumed numeric or pre-encoded per T018).
    """
    X = df[predictors].copy()
    y = df["compatibility_label"].copy()
    
    # Check for NaNs in X (logistic regression cannot handle NaNs)
    if X.isnull().any().any():
        # Fallback to median imputation for safety, though T018 should have handled this
        X = X.fillna(X.median())
    
    return X, y

def fit_logistic_models(X, y, predictors):
    """
    Fits Null (intercept only) and Full (all predictors + L2) models.
    Uses sklearn's LogisticRegression for robustness and speed.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, accuracy_score, log_loss
    from sklearn.model_selection import cross_val_score
    import warnings
    warnings.filterwarnings('ignore')

    results = {
        "null_model": {},
        "full_model": {},
        "metrics": {},
        "model_params": {}
    }

    # --- Null Model (Intercept Only) ---
    # We create a dummy feature (all 1s) to fit intercept only, or just compute mean probability
    # LogisticRegression with fit_intercept=True and no features effectively models P(y=1) = sigmoid(intercept)
    # However, sklearn requires at least one feature. We'll fit a model with a single constant column.
    X_null = np.ones((len(X), 1))
    
    null_clf = LogisticRegression(fit_intercept=False, solver='lbfgs', max_iter=1000)
    null_clf.fit(X_null, y)
    
    # Predictions for Null
    y_pred_null_prob = null_clf.predict_proba(X_null)[:, 1]
    y_pred_null_class = (y_pred_null_prob > 0.5).astype(int)
    
    results["null_model"] = {
        "intercept": float(null_clf.intercept_[0]),
        "coefficients": None,
        "predictions": y_pred_null_prob.tolist()
    }

    # --- Full Model (Frequency + Similarity + Role) ---
    # L2 regularization (default penalty='l2')
    full_clf = LogisticRegression(
        penalty='l2', 
        solver='lbfgs', 
        max_iter=1000, 
        C=1.0, 
        random_state=42
    )
    full_clf.fit(X, y)

    # Predictions for Full
    y_pred_full_prob = full_clf.predict_proba(X)[:, 1]
    y_pred_full_class = (y_pred_full_prob > 0.5).astype(int)

    results["full_model"] = {
        "intercept": float(full_clf.intercept_[0]),
        "coefficients": dict(zip(predictors, [float(c) for c in full_clf.coef_[0]])),
        "predictions": y_pred_full_prob.tolist()
    }

    # --- Metrics ---
    # Null Model Metrics
    try:
        null_auc = roc_auc_score(y, y_pred_null_prob)
    except ValueError:
        null_auc = 0.5 # Undefined if y is constant

    null_acc = accuracy_score(y, y_pred_null_class)
    null_ll = log_loss(y, y_pred_null_prob)

    # Full Model Metrics
    try:
        full_auc = roc_auc_score(y, y_pred_full_prob)
    except ValueError:
        full_auc = 0.5

    full_acc = accuracy_score(y, y_pred_full_class)
    full_ll = log_loss(y, y_pred_full_prob)

    # Cross-Validation (5-fold) for Full Model
    try:
        cv_scores = cross_val_score(full_clf, X, y, cv=5, scoring='roc_auc')
        cv_mean = float(np.mean(cv_scores))
        cv_std = float(np.std(cv_scores))
    except Exception as e:
        cv_mean = None
        cv_std = None

    results["metrics"] = {
        "null_model": {
            "auc": float(null_auc),
            "accuracy": float(null_acc),
            "log_loss": float(null_ll)
        },
        "full_model": {
            "auc": float(full_auc),
            "accuracy": float(full_acc),
            "log_loss": float(full_ll),
            "cv_auc_mean": cv_mean,
            "cv_auc_std": cv_std
        },
        "delta": {
            "auc_improvement": float(full_auc - null_auc) if null_auc and full_auc else None
        }
    }

    results["model_params"] = {
        "solver": "lbfgs",
        "penalty": "l2",
        "C": 1.0,
        "random_state": 42
    }

    return results

def save_models_and_results(results, output_path):
    """
    Saves the results dictionary to JSON.
    Note: Large prediction lists might be truncated in JSON for size, 
    but the task requires the file to exist. We save the full list.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Logistic regression results saved to {output_path}")

def main():
    print("Starting Logistic Regression Fit (T022)...")
    
    # Memory check
    check_memory_limit(limit_mb=6144)
    
    # Load data
    df, predictors = load_processed_data()
    print(f"Loaded {len(df)} samples with predictors: {predictors}")
    
    # Prepare features
    X, y = prepare_features(df, predictors)
    
    # Fit models
    results = fit_logistic_models(X, y, predictors)
    
    # Save output
    output_path = project_root / "data" / "final" / "logistic_results.json"
    save_models_and_results(results, output_path)
    
    print("T022 Complete.")

if __name__ == "__main__":
    import argparse
    main()
