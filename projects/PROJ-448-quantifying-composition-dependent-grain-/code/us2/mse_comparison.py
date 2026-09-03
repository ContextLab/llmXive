"""
Task T022: Compare MSE of interaction model vs. additive binary null hypothesis.
Requirement: Confirm cooperative effects if >10% MSE reduction is achieved.
"""
import json
import logging
import sys
import warnings
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from code.config import PROCESSED_PATH, get_logger
from code.us2.compute_mse_reduction import load_interaction_terms, prepare_data

# Ensure logger is configured
logger = get_logger(__name__)


def fit_additive_binary_model(
    X: np.ndarray, y: np.ndarray, feature_names: List[str]
) -> Tuple[LinearRegression, float]:
    """
    Fit a null hypothesis model that only includes main effects (binary contributions).
    Interaction terms (e.g., Cr_Mo) are excluded.
    
    Returns:
        model: Fitted LinearRegression object.
        mse: Mean Squared Error on the training data.
    """
    # Identify main effect columns (those without underscores, assuming interactions have underscores)
    # Based on T021a naming: Cr, Mo, V, W are main; Cr_Mo, Cr_V etc. are interactions.
    main_effect_cols = [name for name in feature_names if '_' not in name]
    
    if len(main_effect_cols) == 0:
        raise ValueError("No main effect features found. Cannot fit additive binary model.")
    
    X_main = X[:, [feature_names.index(col) for col in main_effect_cols]]
    
    model = LinearRegression()
    model.fit(X_main, y)
    
    y_pred = model.predict(X_main)
    mse = mean_squared_error(y, y_pred)
    
    logger.info(f"Fitted additive binary model using features: {main_effect_cols}")
    logger.info(f"Additive model MSE: {mse:.6f}")
    
    return model, mse


def fit_interaction_model(
    X: np.ndarray, y: np.ndarray
) -> Tuple[LinearRegression, float]:
    """
    Fit the full model including interaction terms.
    
    Returns:
        model: Fitted LinearRegression object.
        mse: Mean Squared Error on the training data.
    """
    model = LinearRegression()
    model.fit(X, y)
    
    y_pred = model.predict(X)
    mse = mean_squared_error(y, y_pred)
    
    logger.info(f"Fitted interaction model using all features")
    logger.info(f"Interaction model MSE: {mse:.6f}")
    
    return model, mse


def compute_mse_reduction(mse_null: float, mse_full: float) -> float:
    """
    Calculate the percentage reduction in MSE.
    Formula: ((MSE_null - MSE_full) / MSE_null) * 100
    """
    if mse_null == 0:
        return 0.0
    return ((mse_null - mse_full) / mse_null) * 100.0


def run_mse_comparison(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Main logic for T022:
    1. Load interaction terms and targets.
    2. Fit additive binary model (null hypothesis).
    3. Fit interaction model (alternative hypothesis).
    4. Compare MSEs.
    5. Log result and raise warning if threshold not met.
    6. Save results to JSON.
    """
    logger.info("Starting MSE comparison for cooperative effects detection (T022)...")
    
    # Load data
    data = load_interaction_terms(input_path)
    if data is None or data.empty:
        raise FileNotFoundError(f"Interaction terms file is empty or missing at {input_path}")
    
    # Prepare features and target
    X, y, feature_names = prepare_data(data)
    
    if len(X) == 0:
        raise ValueError("No data points available for regression analysis.")
    
    # Fit models
    _, mse_additive = fit_additive_binary_model(X, y, feature_names)
    _, mse_interaction = fit_interaction_model(X, y)
    
    # Compute reduction
    reduction_pct = compute_mse_reduction(mse_additive, mse_interaction)
    
    # Log required message
    threshold = 10.0
    logger.info(f"MSE reduction: {reduction_pct:.2f}% (Threshold: {threshold}%)")
    
    # Determine status
    cooperative_detected = reduction_pct > threshold
    
    if not cooperative_detected:
        warning_msg = (
            f"Cooperative effects NOT confirmed: MSE reduction ({reduction_pct:.2f}%) "
            f"is below threshold ({threshold}%)."
        )
        warnings.warn(warning_msg)
        logger.warning(warning_msg)
    else:
        logger.info("Cooperative effects CONFIRMED: MSE reduction exceeds threshold.")
    
    # Prepare results
    results = {
        "mse_additive_binary": float(mse_additive),
        "mse_interaction_model": float(mse_interaction),
        "mse_reduction_percent": float(reduction_pct),
        "threshold_percent": float(threshold),
        "cooperative_effects_detected": cooperative_detected,
        "feature_count": len(feature_names),
        "data_points": len(y)
    }
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"MSE comparison results saved to {output_path}")
    return results


def main():
    input_file = PROCESSED_PATH / "interaction_terms.csv"
    output_file = PROCESSED_PATH / "mse_comparison.json"
    
    try:
        run_mse_comparison(input_file, output_file)
    except Exception as e:
        logger.error(f"MSE comparison failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
