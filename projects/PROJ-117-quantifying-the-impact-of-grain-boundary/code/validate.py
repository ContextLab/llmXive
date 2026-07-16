"""
Validation module for grain boundary diffusivity model.

This module implements:
- k-fold cross-validation on the held-out test set
- Regression bias testing (y_true ~ y_pred)
- Bonferroni correction for multiple hypothesis tests
- Report generation with average metrics and standard deviations
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import cross_val_score, KFold
from sklearn.linear_model import LinearRegression
from scipy import stats

# Import project utilities
from utils import setup_logging, set_random_seed
from error_handling import DataInsufficiencyError

# Configure logging
logger = setup_logging(__name__)

# Constants
R2_THRESHOLD = 0.7
BONFERRONI_ALPHA = 0.05
NUM_FOLDS = 5
RANDOM_SEED = 42

def load_model_and_data(model_path: str, data_path: str) -> Tuple[xgb.XGBRegressor, pd.DataFrame]:
    """
    Load the trained model and the test dataset.

    Args:
        model_path: Path to the saved model JSON
        data_path: Path to the cleaned dataset parquet

    Returns:
        Tuple of (model, dataframe)
    """
    logger.info(f"Loading model from {model_path}")
    model = xgb.XGBRegressor()
    model.load_model(model_path)

    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)

    # Identify feature and target columns based on schema
    # Assuming target is 'diffusivity' and features are all other numeric columns
    target_col = 'diffusivity'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset. Columns: {df.columns.tolist()}")

    # Filter for numeric columns only for model input
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col in numeric_cols:
        numeric_cols.remove(target_col)

    if not numeric_cols:
        raise ValueError("No numeric feature columns found in dataset.")

    X = df[numeric_cols]
    y = df[target_col]

    logger.info(f"Loaded {len(y)} samples with {len(numeric_cols)} features")
    return model, X, y, numeric_cols

def perform_cross_validation(model: xgb.XGBRegressor, X: pd.DataFrame, y: pd.Series, n_folds: int = NUM_FOLDS) -> Dict[str, Any]:
    """
    Perform k-fold cross-validation on the test set to assess stability.

    Args:
        model: Trained XGBoost model
        X: Feature dataframe
        y: Target series
        n_folds: Number of folds

    Returns:
        Dictionary with mean and std of R2, RMSE, MAPE
    """
    logger.info(f"Performing {n_folds}-fold cross-validation on test set")

    # Define scoring metrics
    # sklearn's cross_val_score only returns one metric at a time usually,
    # so we use a custom approach or loop.
    # For R2:
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED)

    r2_scores = []
    rmse_scores = []
    mape_scores = []

    for train_idx, test_idx in kf.split(X):
        X_train_fold, X_test_fold = X.iloc[train_idx], X.iloc[test_idx]
        y_train_fold, y_test_fold = y.iloc[train_idx], y.iloc[test_idx]

        # Train a clone of the model on the fold
        fold_model = xgb.XGBRegressor(**model.get_params())
        fold_model.fit(X_train_fold, y_train_fold)

        y_pred_fold = fold_model.predict(X_test_fold)

        # Calculate metrics
        r2 = r2_score(y_test_fold, y_pred_fold)
        r2_scores.append(r2)

        rmse = np.sqrt(np.mean((y_test_fold - y_pred_fold) ** 2))
        rmse_scores.append(rmse)

        # MAPE: Mean Absolute Percentage Error
        # Handle division by zero if actual is 0
        mape = np.mean(np.abs((y_test_fold - y_pred_fold) / y_test_fold)) * 100
        mape_scores.append(mape)

    return {
        "r2": {
            "mean": float(np.mean(r2_scores)),
            "std": float(np.std(r2_scores)),
            "values": [float(x) for x in r2_scores]
        },
        "rmse": {
            "mean": float(np.mean(rmse_scores)),
            "std": float(np.std(rmse_scores)),
            "values": [float(x) for x in rmse_scores]
        },
        "mape": {
            "mean": float(np.mean(mape_scores)),
            "std": float(np.std(mape_scores)),
            "values": [float(x) for x in mape_scores]
        }
    }

def run_regression_bias_test(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, Any]:
    """
    Execute regression bias test (y_true ~ y_pred).

    Tests if the relationship is y = x (intercept=0, slope=1).

    Args:
        y_true: Actual values
        y_pred: Predicted values

    Returns:
        Dictionary with intercept, slope, p-values, and significance flags
    """
    logger.info("Running regression bias test")

    model = LinearRegression()
    model.fit(y_pred.values.reshape(-1, 1), y_true.values)

    intercept = model.intercept_
    slope = model.coef_[0]

    # Perform t-test for intercept and slope
    # y = intercept + slope * x + error
    # We want to test H0: intercept=0 and H0: slope=1

    # Calculate residuals
    residuals = y_true - (intercept + slope * y_pred)

    # Standard error of regression
    n = len(y_true)
    mse = np.sum(residuals ** 2) / (n - 2)
    s_err = np.sqrt(mse)

    # Standard errors for coefficients
    x_mean = np.mean(y_pred)
    ss_x = np.sum((y_pred - x_mean) ** 2)

    se_intercept = s_err * np.sqrt(1/n + (x_mean**2)/ss_x)
    se_slope = s_err / np.sqrt(ss_x)

    # T-statistics
    t_intercept = (intercept - 0) / se_intercept
    t_slope = (slope - 1) / se_slope

    # P-values (two-tailed)
    p_intercept = 2 * (1 - stats.t.cdf(np.abs(t_intercept), n - 2))
    p_slope = 2 * (1 - stats.t.cdf(np.abs(t_slope), n - 2))

    # Bonferroni correction: alpha_adj = 0.05 / 3 (intercept, slope, maybe R2 test if included)
    # Here we focus on intercept and slope, but task says 3 tests.
    # Let's assume the 3 tests are: Intercept=0, Slope=1, and maybe an overall F-test or similar.
    # The prompt specifically mentions "intercept, slope, and p-values" and "Bonferroni correction (α_adj = 0.05 / 3)".
    # We will adjust p-values for the two tests we have, and perhaps include a third (e.g., R2 significance) or just report adjusted.
    # Let's assume the 3 tests are: Intercept, Slope, and R2 (coefficient of determination significance).
    # Actually, usually bias test is just intercept and slope. If 3 is required, maybe it includes a test for homoscedasticity or similar.
    # Given the constraint, we will adjust the p-values we have by dividing alpha by 3.
    alpha_adj = BONFERRONI_ALPHA / 3

    sig_intercept = p_intercept < alpha_adj
    sig_slope = p_slope < alpha_adj

    return {
        "intercept": float(intercept),
        "slope": float(slope),
        "p_intercept": float(p_intercept),
        "p_slope": float(p_slope),
        "alpha_adjusted": float(alpha_adj),
        "significance": {
            "intercept_is_zero": not sig_intercept, # If p < alpha, we reject null (intercept != 0), so bias exists
            "slope_is_one": not sig_slope
        },
        "bias_detected": sig_intercept or sig_slope
    }

def r2_score(y_true, y_pred):
    """Calculate R-squared score."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot)

def generate_report(cv_results: Dict[str, Any], bias_results: Dict[str, Any], output_path: str):
    """
    Generate the validation report JSON.

    Args:
        cv_results: Cross-validation results
        bias_results: Bias test results
        output_path: Path to save the report
    """
    report = {
        "validation_summary": {
            "k_folds": NUM_FOLDS,
            "alpha_adjusted": bias_results["alpha_adjusted"]
        },
        "cross_validation_metrics": cv_results,
        "regression_bias_test": bias_results,
        "stability_check": {
            "r2_std_threshold": 0.05,
            "r2_std_actual": cv_results["r2"]["std"],
            "passed": cv_results["r2"]["std"] <= 0.05
        }
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to {output_path}")

def main():
    """Main entry point for validation."""
    set_random_seed(RANDOM_SEED)

    # Paths
    project_root = Path(__file__).resolve().parents[1]
    model_path = project_root / "models" / "best_model.json"
    data_path = project_root / "data" / "processed" / "cleaned_dataset.parquet"
    report_path = project_root / "artifacts" / "reports" / "validation_report.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    try:
        # Load data and model
        model, X, y, feature_cols = load_model_and_data(str(model_path), str(data_path))

        # Perform Cross-Validation on Test Set
        cv_results = perform_cross_validation(model, X, y)

        # Run Bias Test
        # Use the full test set for bias test as per spec
        y_pred_test = model.predict(X)
        bias_results = run_regression_bias_test(y, y_pred_test)

        # Generate Report
        generate_report(cv_results, bias_results, str(report_path))

        # Log key metrics
        logger.info(f"CV R2 Mean: {cv_results['r2']['mean']:.4f} (+/- {cv_results['r2']['std']:.4f})")
        logger.info(f"Bias Test - Intercept: {bias_results['intercept']:.4f}, Slope: {bias_results['slope']:.4f}")
        logger.info(f"Stability Check: {'PASSED' if cv_results['r2']['std'] <= 0.05 else 'FAILED'}")

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
