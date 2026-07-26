"""
Ridge Regression Analysis Module for Network Metrics vs Diffusion Rates.

Implements regularized linear regression to handle collinear predictors
in network topology data, preventing overfitting common in OLS.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

from code.src.analysis.aggregate_results import load_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RidgeRegressionError(Exception):
    """Custom exception for Ridge Regression failures."""
    pass


def load_simulation_results() -> pd.DataFrame:
    """
    Load simulation results from the aggregated analysis file.

    Returns:
        pd.DataFrame: Filtered and cleaned simulation results.

    Raises:
        RidgeRegressionError: If file is missing or data is insufficient.
    """
    input_path = Path("data/analysis/aggregated_results.json")

    if not input_path.exists():
        raise RidgeRegressionError(
            f"Input file not found: {input_path}. "
            "Ensure T037a (aggregate_results) has been executed successfully."
        )

    data = load_json_file(input_path)

    # Expecting 'ridge_results' or 'standard_regression' or 'summary_stats' in aggregated
    # However, the task T058 specifically needs the raw data points to run Ridge.
    # The aggregated file structure per T037a is:
    # { "standard_regression": ..., "ridge_results": ..., "partial_correlation": ..., "sensitivity_correlation": ..., "summary_stats": ... }
    # If we are running T058 *before* T037a, we need the raw simulation results.
    # T037a depends on T058, so T058 must read from the raw source: simulation_results.json
    # or the intermediate aggregated data if it exists but doesn't include ridge yet.
    # Let's check the dependency: T058 -> T037a.
    # T037a loads simulation_results.json, sensitivity_correlation.json, partial_correlation_results.json, ridge_results.json.
    # This implies T058 (producing ridge_results.json) runs BEFORE T037a.
    # Therefore, T058 must load from `data/analysis/simulation_results.json` directly.

    simulation_path = Path("data/analysis/simulation_results.json")
    if not simulation_path.exists():
        raise RidgeRegressionError(
            f"Required input file not found: {simulation_path}. "
            "Run T029 (simulation_results) before T058."
        )

    raw_data = load_json_file(simulation_path)

    if not isinstance(raw_data, list) or len(raw_data) == 0:
        raise RidgeRegressionError("Simulation results file is empty or invalid format.")

    df = pd.DataFrame(raw_data)

    # Filter out failed runs
    valid_statuses = ["COMPLETED", "SUCCESS"] # Adjust based on actual status strings in spec
    # From T029a schema: status (str). From T026a: [RUNTIME_EXCEEDED], [SIMULATION_DIVERGENCE]
    # We should exclude divergence and runtime exceeded.
    excluded_statuses = ["[SIMULATION_DIVERGENCE]", "[RUNTIME_EXCEEDED]", "FAILED", "ERROR"]

    if 'status' in df.columns:
        df = df[~df['status'].isin(excluded_statuses)]

    if len(df) < 5:
        raise RidgeRegressionError(
            f"Insufficient data points ({len(df)}) for regression analysis. "
            "Need at least 5 valid runs."
        )

    return df


def prepare_features_targets(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare feature matrix X and target vector y for Ridge Regression.

    Features: Network metrics (clustering_coefficient, average_path_length, degree_distribution_metrics)
    Target: diffusion_rate

    Args:
        df: DataFrame containing simulation results.

    Returns:
        Tuple of (X, y, feature_names)
    """
    # Identify potential feature columns
    feature_candidates = [
        'clustering_coefficient', 'average_path_length', 'average_degree',
        'graph_density', 'transitivity', 'assortativity_coefficient'
    ]

    # Filter to columns that actually exist
    available_features = [col for col in feature_candidates if col in df.columns]

    if not available_features:
        # Fallback to common metrics if specific ones missing, or raise error
        logger.warning("No standard network metrics found in data. Using available numeric columns.")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Exclude diffusion_rate if it's in there
        if 'diffusion_rate' in numeric_cols:
            numeric_cols.remove('diffusion_rate')
        available_features = numeric_cols

    if not available_features:
        raise RidgeRegressionError("No feature columns found for regression.")

    X = df[available_features].values
    y = df['diffusion_rate'].values if 'diffusion_rate' in df.columns else None

    if y is None:
        # Try to find a similar column
        possible_targets = [c for c in df.columns if 'diffusion' in c.lower() or 'rate' in c.lower()]
        if possible_targets:
            target_col = possible_targets[0]
            y = df[target_col].values
            logger.info(f"Using '{target_col}' as target variable.")
        else:
            raise RidgeRegressionError("Could not find target variable 'diffusion_rate' or similar.")

    return X, y, available_features


def run_ridge_regression(
    X: np.ndarray,
    y: np.ndarray,
    alphas: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Execute Ridge Regression with cross-validation to select optimal alpha.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        alphas: List of alpha values to test. Defaults to [0.01, 0.1, 1.0, 10.0, 100.0]

    Returns:
        Dictionary containing regression results, coefficients, best alpha, and CV scores.
    """
    if alphas is None:
        alphas = [0.01, 0.1, 1.0, 10.0, 100.0]

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Use RidgeCV to find best alpha efficiently
    # cv=5 for 5-fold cross-validation
    ridge_cv = RidgeCV(alphas=alphas, cv=5, store_cv_values=True)
    ridge_cv.fit(X_scaled, y)

    best_alpha = ridge_cv.alpha_

    # Get coefficients for the best model
    # RidgeCV coefficients correspond to the scaled features
    coefficients = ridge_cv.coef_

    # Calculate R^2 and MSE on the full dataset using the best model
    y_pred = ridge_cv.predict(X_scaled)
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)

    # Cross-validation scores (R^2) for each alpha
    cv_scores = ridge_cv.cv_values_.mean(axis=1) # Mean across folds for each alpha

    # Map alphas to scores
    alpha_scores = dict(zip(alphas, cv_scores))

    # Detailed CV scores per fold (optional, but useful for diagnostics)
    # ridge_cv.cv_values_ shape: (n_alphas, n_folds)

    return {
        "best_alpha": float(best_alpha),
        "coefficients": coefficients.tolist(),
        "r2_score": float(r2),
        "mse": float(mse),
        "alpha_scores": alpha_scores,
        "feature_names": [], # Will be filled by caller
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist()
    }


def aggregate_results(
    df: pd.DataFrame,
    results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate regression results with metadata for final output.

    Args:
        df: Original DataFrame used for regression.
        results: Raw regression results from run_ridge_regression.

    Returns:
        Dictionary ready for JSON serialization.
    """
    feature_names = list(df.columns[df.columns.isin(
        ['clustering_coefficient', 'average_path_length', 'average_degree',
         'graph_density', 'transitivity', 'assortativity_coefficient']
    )])

    # Ensure we only include features that were actually used
    # The run_ridge_regression function handles feature selection internally if needed,
    # but here we map the coefficients back to the specific columns used.
    # Note: run_ridge_regression currently uses all available features from the list.
    # We need to ensure the order matches.

    # Re-run feature selection logic to get exact order
    feature_candidates = [
        'clustering_coefficient', 'average_path_length', 'average_degree',
        'graph_density', 'transitivity', 'assortativity_coefficient'
    ]
    available_features = [col for col in feature_candidates if col in df.columns]

    results["feature_names"] = available_features
    results["sample_size"] = len(df)
    results["timestamp"] = datetime.now().isoformat()

    # Add summary statistics of input data
    results["input_summary"] = {
        "mean_diffusion_rate": float(df['diffusion_rate'].mean()) if 'diffusion_rate' in df else None,
        "std_diffusion_rate": float(df['diffusion_rate'].std()) if 'diffusion_rate' in df else None,
        "min_diffusion_rate": float(df['diffusion_rate'].min()) if 'diffusion_rate' in df else None,
        "max_diffusion_rate": float(df['diffusion_rate'].max()) if 'diffusion_rate' in df else None
    }

    return results


def main():
    """
    Main entry point for Ridge Regression analysis.
    Executes the full pipeline: load data -> prepare -> run -> save.
    """
    logger.info("Starting Ridge Regression Analysis (T058)")

    try:
        # 1. Load Data
        logger.info("Loading simulation results...")
        df = load_simulation_results()
        logger.info(f"Loaded {len(df)} valid records.")

        # 2. Prepare Features and Targets
        logger.info("Preparing features and targets...")
        X, y, feature_names = prepare_features_targets(df)
        logger.info(f"Features: {feature_names}")

        # 3. Run Ridge Regression
        logger.info("Running Ridge Regression with cross-validation...")
        raw_results = run_ridge_regression(X, y)

        # 4. Aggregate Results
        logger.info("Aggregating results...")
        final_results = aggregate_results(df, raw_results)

        # 5. Save Output
        output_path = Path("data/analysis/ridge_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2)

        logger.info(f"Ridge Regression results saved to {output_path}")
        logger.info(f"Best Alpha: {final_results['best_alpha']:.4f}")
        logger.info(f"R^2 Score: {final_results['r2_score']:.4f}")

    except RidgeRegressionError as e:
        logger.error(f"Ridge Regression failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during Ridge Regression: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
