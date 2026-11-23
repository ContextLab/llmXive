"""
Ridge Regression Analysis for Network Metrics vs Diffusion Rates.

This module implements Ridge Regression to handle collinear predictors
in the relationship between network topology metrics and diffusion rates.
It performs cross-validation to select the optimal alpha parameter.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

from code.src.utils.logging import log_run

logger = logging.getLogger(__name__)

class RidgeRegressionError(Exception):
    """Custom exception for Ridge Regression errors."""
    pass

def load_simulation_data() -> pd.DataFrame:
    """
    Load simulation results from the JSON file.

    Returns:
        pd.DataFrame: DataFrame containing simulation results with metrics.

    Raises:
        RidgeRegressionError: If the file is missing or malformed.
    """
    input_path = Path("data/analysis/simulation_results.json")
    if not input_path.exists():
        raise RidgeRegressionError(
            f"Required input file not found: {input_path}. "
            "Please ensure T029 (simulation results) has been executed."
        )

    try:
        with open(input_path, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            raise RidgeRegressionError("Simulation results file is empty or malformed.")

        df = pd.DataFrame(data)

        # Filter out failed runs
        valid_statuses = ['COMPLETED', 'SUCCESS']
        df = df[df['status'].isin(valid_statuses)]

        if df.empty:
            raise RidgeRegressionError("No valid simulation runs found after filtering.")

        return df
    except json.JSONDecodeError as e:
        raise RidgeRegressionError(f"Failed to parse simulation results JSON: {e}")

def prepare_features_and_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare feature matrix (X) and target vector (y) for Ridge Regression.

    Features: Clustering coefficient, Average path length, Degree distribution stats.
    Target: Diffusion rate.

    Args:
        df: DataFrame with simulation results.

    Returns:
        Tuple of (X, y, feature_names)
    """
    # Define features to use
    feature_cols = ['clustering_coefficient', 'average_path_length', 'degree_mean', 'degree_std']
    target_col = 'diffusion_rate'

    # Check for missing columns
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        # Try to infer from available columns or raise error
        available_cols = [col for col in df.columns if 'clustering' in col.lower() or 'path' in col.lower() or 'degree' in col.lower()]
        logger.warning(f"Missing expected feature columns: {missing_cols}. Available: {available_cols}")
        # Fallback to available columns if possible, otherwise strict failure
        feature_cols = [col for col in feature_cols if col in df.columns]
        if not feature_cols:
            raise RidgeRegressionError("No valid feature columns found for regression.")

    if target_col not in df.columns:
        raise RidgeRegressionError(f"Target column '{target_col}' not found in data.")

    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]

    # Drop rows where target is also missing
    mask = y.notna()
    X = X[mask]
    y = y[mask]

    if len(X) < 10:
        raise RidgeRegressionError(f"Insufficient data points for regression: {len(X)} (min 10 required).")

    return X.values, y.values, feature_cols

def run_ridge_regression(X: np.ndarray, y: np.ndarray, alphas: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Perform Ridge Regression with cross-validation.

    Args:
        X: Feature matrix (n_samples, n_features).
        y: Target vector (n_samples,).
        alphas: List of alpha values to test. Defaults to logspace range.

    Returns:
        Dictionary containing regression results.
    """
    if alphas is None:
        alphas = np.logspace(-4, 4, 20)

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Use RidgeCV for efficient cross-validation
    model = RidgeCV(alphas=alphas, store_cv_values=True, cv=5)
    model.fit(X_scaled, y)

    # Get best alpha
    best_alpha = model.alpha_

    # Refit with best alpha on full data for coefficients
    final_model = Ridge(alpha=best_alpha)
    final_model.fit(X_scaled, y)

    # Cross-validation scores (R^2)
    cv_scores = cross_val_score(
        Ridge(alpha=best_alpha), X_scaled, y, cv=5, scoring='r2'
    )

    results = {
        "best_alpha": float(best_alpha),
        "coefficients": {
            f"coef_{i}": float(c) for i, c in enumerate(final_model.coef_)
        },
        "intercept": float(final_model.intercept_),
        "cv_scores": {
            "mean_r2": float(cv_scores.mean()),
            "std_r2": float(cv_scores.std()),
            "individual_scores": [float(s) for s in cv_scores]
        },
        "r2_score": float(final_model.score(X_scaled, y)),
        "n_samples": int(len(y)),
        "n_features": int(X.shape[1])
    }

    return results

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save Ridge Regression results to a JSON file.

    Args:
        results: Dictionary of results.
        output_path: Path to save the JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Ridge regression results saved to {output_file}")

def main() -> int:
    """
    Main entry point for Ridge Regression analysis.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    setup_logging()
    logger.info("Starting Ridge Regression analysis (T058)")

    try:
        # Load data
        df = load_simulation_data()
        logger.info(f"Loaded {len(df)} valid simulation runs")

        # Prepare features and target
        X, y, feature_names = prepare_features_and_target(df)
        logger.info(f"Prepared feature matrix: {X.shape}, target vector: {y.shape}")

        # Run regression
        results = run_ridge_regression(X, y)
        results["feature_names"] = feature_names
        results["status"] = "SUCCESS"

        # Save results
        output_path = "data/analysis/ridge_results.json"
        save_results(results, output_path)

        logger.info(f"Ridge Regression completed successfully. Best Alpha: {results['best_alpha']:.6f}, R²: {results['r2_score']:.4f}")
        return 0

    except RidgeRegressionError as e:
        logger.error(f"Ridge Regression failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during Ridge Regression: {e}", exc_info=True)
        return 1

def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/run_log.json', mode='a') # Note: This might conflict with JSON logging, usually handled by utils
        ]
    )

if __name__ == "__main__":
    sys.exit(main())
