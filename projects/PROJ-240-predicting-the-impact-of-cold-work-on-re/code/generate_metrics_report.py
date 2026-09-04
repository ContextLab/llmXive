"""
T028: Generate training metrics report.

Loads the trained model and the final dataset to compute/retrieve
Cross-Validation scores and Test Set metrics (MAE, R²),
then writes them to artifacts/reports/training_metrics.json.

This script assumes T027 (model saved) and T020 (final dataset) are complete.
It re-calculates metrics to ensure the report is consistent with the saved model
and data, or loads them if the training pipeline explicitly saved them.
"""
import json
import os
import sys
import pickle
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_random_seed, get_data_split_ratio
from train import load_final_dataset, split_data, train_model

def main():
    # Paths
    data_path = project_root / "data" / "processed" / "final_dataset.csv"
    model_path = project_root / "artifacts" / "models" / "kinetic_model.pkl"
    report_path = project_root / "artifacts" / "reports" / "training_metrics.json"

    # Verify prerequisites
    if not data_path.exists():
        raise FileNotFoundError(f"Required dataset not found: {data_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Required model not found: {model_path}")

    # Load data
    df = load_final_dataset(data_path)
    target_col = "time_to_peak_minutes"
    feature_cols = [c for c in df.columns if c != target_col]

    X = df[feature_cols].values
    y = df[target_col].values

    # Load model
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    # Calculate metrics
    # 1. Cross-Validation Scores (R²)
    # Use 5-fold CV as per US2 spec
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    mean_cv_r2 = float(np.mean(cv_scores))
    std_cv_r2 = float(np.std(cv_scores))

    # 2. Train/Test Split Evaluation (to match T026 logic)
    # Re-split to ensure consistency with the training phase
    seed = get_random_seed()
    split_ratio = get_data_split_ratio()
    X_train, X_test, y_train, y_test = split_data(X, y, seed, split_ratio)

    # Predict on test set
    y_pred_test = model.predict(X_test)
    test_mae = float(mean_absolute_error(y_test, y_pred_test))
    test_r2 = float(r2_score(y_test, y_pred_test))

    # Compile report
    metrics = {
        "cv_scores": {
            "mean_r2": mean_cv_r2,
            "std_r2": std_cv_r2,
            "n_folds": 5,
            "scores": [float(s) for s in cv_scores]
        },
        "test_set": {
            "mae": test_mae,
            "r2": test_r2,
            "n_samples": int(len(y_test))
        },
        "model_path": str(model_path.relative_to(project_root)),
        "dataset_path": str(data_path.relative_to(project_root))
    }

    # Ensure report directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(report_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics report generated: {report_path}")
    print(f"  CV R²: {mean_cv_r2:.4f} (+/- {std_cv_r2:.4f})")
    print(f"  Test MAE: {test_mae:.4f}")
    print(f"  Test R²: {test_r2:.4f}")

if __name__ == "__main__":
    main()