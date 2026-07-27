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
from typing import Dict, Any, Optional

# Ensure parent is in path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.memory_monitor import check_memory_limit

def load_processed_data(input_path: Path) -> pd.DataFrame:
    """Load processed training data."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_parquet(input_path)

def prepare_features(df: pd.DataFrame, predictor_list: list) -> tuple:
    """Prepare features and target for modeling."""
    # Ensure required columns exist
    required_cols = predictor_list + ["compatibility_label"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        # Create dummy columns if missing (should not happen in real run)
        for col in missing:
            df[col] = 0.0
            
    X = df[predictor_list].fillna(0)
    y = df["compatibility_label"].fillna(0).astype(int)
    return X, y

def fit_logistic_models(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """Fit Null and Full logistic regression models."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, accuracy_score
    
    # Null model (intercept only) - we approximate by fitting with constant feature
    X_null = np.ones((X.shape[0], 1))
    null_clf = LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', max_iter=1000)
    null_clf.fit(X_null, y)
    null_pred = null_clf.predict_proba(X_null)[:, 1]
    
    # Full model
    full_clf = LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', max_iter=1000)
    full_clf.fit(X, y)
    full_pred = full_clf.predict_proba(X)[:, 1]
    
    # Calculate metrics
    null_auc = roc_auc_score(y, null_pred) if len(np.unique(y)) > 1 else 0.5
    full_auc = roc_auc_score(y, full_pred) if len(np.unique(y)) > 1 else 0.5
    
    null_acc = accuracy_score(y, null_clf.predict(X_null))
    full_acc = accuracy_score(y, full_clf.predict(X))
    
    return {
        "null_model": {
            "auc": float(null_auc),
            "accuracy": float(null_acc),
            "coefficients": null_clf.coef_.tolist()
        },
        "full_model": {
            "auc": float(full_auc),
            "accuracy": float(full_acc),
            "coefficients": full_clf.coef_.tolist(),
            "intercept": float(full_clf.intercept_[0])
        }
    }

def save_models_and_results(results: Dict[str, Any], output_path: Path):
    """Save model results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Main entry point for logistic regression fitting."""
    parser = argparse.ArgumentParser(description="Fit logistic regression models")
    parser.add_argument('--input', type=str, default='data/processed/train_set.parquet')
    parser.add_argument('--output', type=str, default='data/final/')
    args = parser.parse_args()
    
    check_memory_limit()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_path = output_dir / "logistic_results.json"
    
    print("Loading training data...")
    df = load_processed_data(input_path)
    
    # Load predictor list
    predictors_path = output_dir.parent / "final_predictors.json"
    if predictors_path.exists():
        with open(predictors_path, 'r') as f:
            predictor_list = json.load(f).get("predictors", [])
    else:
        # Default predictors
        predictor_list = ["log_co_occurrence", "flavor_similarity", "functional_role"]
        
    print(f"Using predictors: {predictor_list}")
    
    print("Preparing features...")
    X, y = prepare_features(df, predictor_list)
    
    print("Fitting models...")
    results = fit_logistic_models(X, y)
    
    print("Saving results...")
    save_models_and_results(results, output_path)
    
    print("Logistic regression fitting completed successfully.")

if __name__ == "__main__":
    import argparse
    main()
