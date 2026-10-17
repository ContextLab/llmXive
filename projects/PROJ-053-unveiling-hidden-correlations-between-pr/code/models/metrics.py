import os
import json
import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

from config import (
    get_processed_data_dir,
    get_results_dir,
    ensure_directories,
    get_logger,
)

logger = get_logger(__name__)

def _calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
    """
    Compute R², RMSE, and MAE.
    """
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    return r2, rmse, mae

def main():
    """
    Entry point for metric calculation.
    Loads the test set and the trained GPR and baseline models,
    computes performance metrics on the test set, and writes them to
    <project>/results/metrics.json.
    """
    logger.info("Calculating and saving model performance metrics...")

    processed_dir = Path(get_processed_data_dir())
    test_path = processed_dir / "test.csv"

    if not test_path.exists():
        raise FileNotFoundError("Test CSV not found for metrics calculation.")

    test_df = pd.read_csv(test_path)

    # Determine target columns (use the first available)
    target_cols = [c for c in ["yield_strength", "ductility"] if c in test_df.columns]
    if not target_cols:
        raise ValueError("No target columns found in test data.")
    target = target_cols[0]

    feature_cols = [c for c in test_df.columns if c not in target_cols]

    X_test = test_df[feature_cols].values
    y_test = test_df[target].values

    # Load trained models
    model_dir = Path(get_results_dir()) / "model"
    gpr_path = model_dir / "gpr_model.joblib"
    baseline_path = model_dir / "baseline_model.joblib"

    if not gpr_path.exists() or not baseline_path.exists():
        raise FileNotFoundError("Trained model files not found for metric calculation.")

    gpr_model = joblib.load(gpr_path)
    baseline_model = joblib.load(baseline_path)

    # Predictions
    gpr_pred = gpr_model.predict(X_test)
    baseline_pred = baseline_model.predict(X_test)

    # Compute metrics
    gpr_r2, gpr_rmse, gpr_mae = _calculate_metrics(y_test, gpr_pred)
    baseline_r2, baseline_rmse, baseline_mae = _calculate_metrics(y_test, baseline_pred)

    delta_r2 = gpr_r2 - baseline_r2

    # RMSE as a percentage of the observed target range
    range_val = np.max(y_test) - np.min(y_test)
    rmse_percentage_range = (gpr_rmse / range_val) * 100 if range_val != 0 else 0.0

    metrics = {
        "gpr_r2": gpr_r2,
        "gpr_rmse": gpr_rmse,
        "gpr_mae": gpr_mae,
        "baseline_r2": baseline_r2,
        "baseline_rmse": baseline_rmse,
        "baseline_mae": baseline_mae,
        "gpr_vs_baseline_delta": delta_r2,
        "rmse_percentage_range": rmse_percentage_range,
    }

    # Save metrics
    results_dir = Path(get_results_dir())
    ensure_directories([results_dir])
    metrics_path = results_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

if __name__ == "__main__":
    main()
