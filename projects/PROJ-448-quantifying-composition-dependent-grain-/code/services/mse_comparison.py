"""
MSE Comparison Service for User Story 2.

Compares the Mean Squared Error (MSE) of a regression model with interaction terms
against an additive binary null hypothesis model. Confirms cooperative effects
only if the interaction model reduces MSE by >10% compared to the null model.
"""
import json
import logging
import sys
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from code.config import PROCESSED_PATH, get_logger
from code.models.regression import load_interaction_terms, prepare_features_and_target

logger = get_logger(__name__)

INTERACTION_COLUMNS = ['Cr_Mo', 'Cr_V', 'Mo_V', 'Cr_W', 'Mo_W', 'V_W']
ADDITIVE_COLUMNS = ['Cr', 'Mo', 'V', 'W']  # Assuming these are the base solute columns
THRESHOLD_PERCENT = 10.0

def load_regression_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Loads interaction terms and prepares features/targets for regression.
    Uses the standard loader from code/models/regression.py.
    """
    input_path = PROCESSED_PATH / "interaction_terms.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Interaction terms file not found at {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded interaction terms from {input_path} with shape {df.shape}")
    
    # Identify target column (assumed to be 'segregation_energy' or similar based on context)
    # If not present, we assume the last column is the target for this specific task flow
    # or we look for a standard name. Let's assume 'segregation_energy' based on T018 output.
    target_col = 'segregation_energy'
    if target_col not in df.columns:
        # Fallback: if the file structure is different, try to infer. 
        # For robustness, we'll raise an error if the expected target is missing.
        raise ValueError(f"Target column '{target_col}' not found in {input_path}. Columns: {df.columns.tolist()}")
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    return X, y

def fit_additive_null_model(X: pd.DataFrame, y: pd.Series) -> Tuple[LinearRegression, float]:
    """
    Fits a linear model using ONLY additive binary terms (no interactions).
    Returns the fitted model and its MSE.
    """
    # Select only additive columns that exist in X
    additive_features = [col for col in ADDITIVE_COLUMNS if col in X.columns]
    
    if not additive_features:
        raise ValueError(f"None of the expected additive columns {ADDITIVE_COLUMNS} found in dataset. Available: {X.columns.tolist()}")
    
    logger.info(f"Fitting additive null model with features: {additive_features}")
    
    X_additive = X[additive_features]
    
    model = LinearRegression()
    model.fit(X_additive, y)
    
    y_pred = model.predict(X_additive)
    mse = mean_squared_error(y, y_pred)
    
    logger.info(f"Additive null model MSE: {mse:.6f}")
    return model, mse

def fit_interaction_model(X: pd.DataFrame, y: pd.Series) -> Tuple[LinearRegression, float]:
    """
    Fits a linear model using ALL features (additive + interactions).
    Returns the fitted model and its MSE.
    """
    # Use all available features in X (assuming X contains both additive and interaction terms)
    logger.info(f"Fitting interaction model with features: {X.columns.tolist()}")
    
    model = LinearRegression()
    model.fit(X, y)
    
    y_pred = model.predict(X)
    mse = mean_squared_error(y, y_pred)
    
    logger.info(f"Interaction model MSE: {mse:.6f}")
    return model, mse

def compare_mse(mse_null: float, mse_interaction: float) -> Dict[str, Any]:
    """
    Calculates MSE reduction percentage and determines if cooperative effects are confirmed.
    """
    if mse_null == 0:
        # Avoid division by zero; if null is 0, interaction can't reduce it meaningfully
        reduction_pct = 0.0
        confirmed = False
        logger.warning("Null model MSE is 0. Cannot calculate reduction percentage.")
    else:
        reduction_pct = ((mse_null - mse_interaction) / mse_null) * 100.0
        confirmed = reduction_pct > THRESHOLD_PERCENT

    return {
        "mse_null": mse_null,
        "mse_interaction": mse_interaction,
        "mse_reduction_percent": reduction_pct,
        "threshold_percent": THRESHOLD_PERCENT,
        "cooperative_effects_confirmed": confirmed
    }

def run_mse_comparison() -> Dict[str, Any]:
    """
    Orchestrates the MSE comparison logic.
    """
    try:
        X, y = load_regression_data()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load data for MSE comparison: {e}")
        raise

    # Fit Null Model
    model_null, mse_null = fit_additive_null_model(X, y)
    
    # Fit Interaction Model
    model_interaction, mse_interaction = fit_interaction_model(X, y)
    
    # Compare
    results = compare_mse(mse_null, mse_interaction)
    
    # Log the required message
    logger.info(f"MSE reduction: {results['mse_reduction_percent']:.2f}% (Threshold: {THRESHOLD_PERCENT}%)")
    
    # Raise warning if threshold not met
    if not results['cooperative_effects_confirmed']:
        warnings.warn(
            f"MSE reduction ({results['mse_reduction_percent']:.2f}%) is not greater than "
            f"threshold ({THRESHOLD_PERCENT}%). Cooperative effects NOT confirmed for this dataset."
        )
        logger.warning(f"Cooperative effects not confirmed. Reduction: {results['mse_reduction_percent']:.2f}%")
    else:
        logger.info("Cooperative effects confirmed based on MSE reduction threshold.")

    return results

def save_results(results: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Saves the comparison results to a JSON file.
    """
    if output_path is None:
        output_path = PROCESSED_PATH / "mse_comparison.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved MSE comparison results to {output_path}")

def main():
    """
    Entry point for the MSE comparison task.
    """
    logger.info("Starting MSE comparison for cooperative effects analysis.")
    
    try:
        results = run_mse_comparison()
        save_results(results)
        logger.info("MSE comparison completed successfully.")
    except Exception as e:
        logger.error(f"MSE comparison failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()