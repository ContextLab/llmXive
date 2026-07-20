"""
Evaluation module for User Story 2: Model Training and Baseline Comparison.

This module computes absolute errors for both the XGBoost and Linear Baseline models
on the hold-out test set, performs statistical testing, and generates evaluation metrics.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score, pearsonr
from scipy.stats import shapiro, ttest_rel, wilcoxon
import joblib

# Import project utilities
from config import get_project_root, get_data_path, get_output_path
from logging_config import setup_logging, get_logger

# Ensure logging is configured
setup_logging()
logger = get_logger(__name__)


def load_test_split_metadata(split_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the metadata regarding the train/test split.
    Expects a JSON file containing indices or split information if saved.
    For this task, we assume the test set is available or can be reconstructed
    from the saved model metadata or a specific split file.

    However, per T024/T025/T026 flow, the test set data (X_test, y_test)
    should ideally be loaded from the data path or reconstructed.
    Since T026 saves the model, we assume the split metadata (indices)
    might be saved in `state/` or we need to re-load the dataset and split
    using the same random state if indices aren't persisted.

    For robustness in this pipeline, we expect `data/processed/test_set.parquet`
    or similar to exist, OR we load the full dataset and re-split.
    Given the task dependencies, let's assume the test set features and targets
    are available in `data/processed/test_X.csv` and `data/processed/test_y.csv`
    or we load the full aligned dataset and use the saved split indices.

    Let's assume T024 saved split indices to `state/split_indices.json`.
    """
    project_root = get_project_root()
    if split_path is None:
        split_path = project_root / "state" / "split_indices.json"

    if not split_path.exists():
        raise FileNotFoundError(f"Split metadata not found at {split_path}. "
                                "Ensure T024 has run and saved split indices.")

    with open(split_path, 'r') as f:
        return json.load(f)


def load_test_data(dataset_path: Optional[Path] = None, split_metadata: Optional[Dict] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the test set features (X) and targets (y) based on split metadata.
    """
    project_root = get_project_root()
    if dataset_path is None:
        dataset_path = project_root / "data" / "processed" / "aligned_dataset.csv"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Aligned dataset not found at {dataset_path}. "
                                "Ensure T020 has run.")

    df = pd.read_csv(dataset_path)

    if split_metadata is None:
        split_metadata = load_test_split_metadata()

    # Assuming split_metadata contains 'test_indices'
    if 'test_indices' not in split_metadata:
        raise ValueError("Split metadata must contain 'test_indices'")

    test_indices = split_metadata['test_indices']
    test_df = df.iloc[test_indices]

    # Identify target column (from T015, it is 'energy_change')
    target_col = 'energy_change'
    feature_cols = [col for col in test_df.columns if col != target_col]

    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    return X_test, y_test


def load_models(models_dir: Optional[Path] = None) -> Tuple[Any, Any]:
    """
    Load the trained Linear Baseline and XGBoost models.
    """
    project_root = get_project_root()
    if models_dir is None:
        models_dir = project_root / "code" / "models"

    if not models_dir.exists():
        raise FileNotFoundError(f"Models directory not found at {models_dir}. "
                                "Ensure T026 has run and saved models.")

    # Expecting specific filenames from T026
    linear_model_path = models_dir / "linear_baseline.joblib"
    xgb_model_path = models_dir / "best_xgboost.json" # XGBoost often saves as JSON

    if not linear_model_path.exists():
        # Fallback to .pkl if .joblib not found, though T026 should use .joblib
        linear_model_path = models_dir / "linear_baseline.pkl"
    
    if not linear_model_path.exists():
        raise FileNotFoundError(f"Linear baseline model not found at {linear_model_path}")

    if not xgb_model_path.exists():
        raise FileNotFoundError(f"XGBoost model not found at {xgb_model_path}")

    logger.info(f"Loading linear model from {linear_model_path}")
    linear_model = joblib.load(linear_model_path)

    logger.info(f"Loading XGBoost model from {xgb_model_path}")
    import xgboost as xgb
    xgb_model = xgb.Booster()
    xgb_model.load_model(str(xgb_model_path))

    return linear_model, xgb_model


def compute_absolute_errors(y_true: pd.Series, y_pred_linear: np.ndarray, y_pred_xgb: np.ndarray) -> Dict[str, pd.Series]:
    """
    Compute absolute errors for both models.
    Returns a dictionary with Series for linear and xgb absolute errors.
    """
    abs_error_linear = np.abs(y_true.values - y_pred_linear)
    abs_error_xgb = np.abs(y_true.values - y_pred_xgb)

    return {
        "linear_abs_error": pd.Series(abs_error_linear, name="linear_abs_error"),
        "xgb_abs_error": pd.Series(abs_error_xgb, name="xgb_abs_error"),
        "y_true": y_true
    }


def save_evaluation_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the evaluation results (absolute errors) to a CSV file.
    """
    project_root = get_project_root()
    if output_path is None:
        output_path = project_root / "outputs" / "evaluation_results.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to DataFrame
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Evaluation results saved to {output_path}")
    return output_path


def run_statistical_test(abs_errors: Dict[str, pd.Series]) -> Dict[str, Any]:
    """
    Perform statistical testing on the paired absolute errors.
    This implements the logic described in T028a/T028b but can be called here
    or in a subsequent task. For T027, we compute the errors. 
    However, to be complete for the evaluation step, we often compute the metrics
    and preliminary stats here.
    
    T027 specifically asks for "Compute absolute errors". 
    T028a/28b handle the statistical test. 
    We will compute the errors and return them. 
    We will also calculate basic metrics (R2, MAE) for immediate logging.
    """
    y_true = abs_errors['y_true'].values
    err_lin = abs_errors['linear_abs_error'].values
    err_xgb = abs_errors['xgb_abs_error'].values
    
    # We need predictions to compute R2, not just errors. 
    # So we assume the caller has predictions or we recompute.
    # This function is strictly for error computation as per T027.
    # But to be useful, let's return the errors.
    return {
        "paired_differences": err_xgb - err_lin, # XGB - Linear
        "linear_abs_error": err_lin,
        "xgb_abs_error": err_xgb
    }


def save_metrics(metrics: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save metrics to JSON.
    """
    project_root = get_project_root()
    if output_path is None:
        output_path = project_root / "outputs" / "metrics.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")
    return output_path


def run_evaluation() -> Dict[str, Any]:
    """
    Main evaluation pipeline for T027:
    1. Load test data.
    2. Load models.
    3. Predict.
    4. Compute absolute errors.
    5. Compute basic metrics (MAE, R2).
    6. Save results.
    """
    logger.info("Starting evaluation pipeline (T027).")

    # 1. Load Data
    X_test, y_test = load_test_data()
    logger.info(f"Loaded test set with {len(y_test)} samples.")

    # 2. Load Models
    linear_model, xgb_model = load_models()
    logger.info("Models loaded successfully.")

    # 3. Predict
    # Linear model
    y_pred_linear = linear_model.predict(X_test)

    # XGBoost model
    # XGBoost Booster expects DMatrix
    import xgboost as xgb
    dmatrix_test = xgb.DMatrix(X_test)
    y_pred_xgb = xgb_model.predict(dmatrix_test)

    # 4. Compute Absolute Errors
    abs_errors = compute_absolute_errors(y_test, y_pred_linear, y_pred_xgb)

    # 5. Compute Metrics
    mae_linear = mean_absolute_error(y_test, y_pred_linear)
    mae_xgb = mean_absolute_error(y_test, y_pred_xgb)
    r2_linear = r2_score(y_test, y_pred_linear)
    r2_xgb = r2_score(y_test, y_pred_xgb)
    
    # Pearson R
    pearson_r_linear, p_val_linear = pearsonr(y_test, y_pred_linear)
    pearson_r_xgb, p_val_xgb = pearsonr(y_test, y_pred_xgb)

    metrics = {
        "linear": {
            "mae": float(mae_linear),
            "r2": float(r2_linear),
            "pearson_r": float(pearson_r_linear),
            "p_value": float(p_val_linear)
        },
        "xgboost": {
            "mae": float(mae_xgb),
            "r2": float(r2_xgb),
            "pearson_r": float(pearson_r_xgb),
            "p_value": float(p_val_xgb)
        },
        "test_size": len(y_test)
    }

    # 6. Save Results
    save_metrics(metrics)
    
    # Save absolute errors to CSV for T028a
    errors_df = pd.DataFrame({
        "y_true": abs_errors['y_true'].values,
        "linear_abs_error": abs_errors['linear_abs_error'].values,
        "xgb_abs_error": abs_errors['xgb_abs_error'].values,
        "paired_diff": abs_errors['xgb_abs_error'].values - abs_errors['linear_abs_error'].values
    })
    errors_path = get_output_path("evaluation_errors.csv")
    errors_df.to_csv(errors_path, index=False)
    logger.info(f"Absolute errors saved to {errors_path}")

    logger.info("Evaluation pipeline completed.")
    return metrics


def main():
    """
    Entry point for the evaluation script.
    """
    try:
        metrics = run_evaluation()
        print(f"Evaluation Complete. Metrics: {metrics}")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()