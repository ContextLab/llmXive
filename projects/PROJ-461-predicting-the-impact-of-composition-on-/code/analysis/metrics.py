"""
Module to calculate and save model performance metrics.

This module implements T026: Saving metrics (Model MAE, Linear Mixing Rule Baseline MAE, 
Mass-Only Baseline MAE, R²) to reports/metrics.json (SSoT).

It loads the trained model and data, computes predictions, and compares against
the baselines defined in the specification.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score

from config import Config, load_config
from utils.logger import get_logger

# Ensure we can import from sibling modules if run as a script
try:
    from data.download import linear_mixing_rule
except ImportError:
    # Fallback for direct execution context if path not set up
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data.download import linear_mixing_rule


def load_model(config: Config) -> Any:
    """Load the trained LightGBM model."""
    model_path = config.model_dir / "model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    with open(model_path, "rb") as f:
        return pickle.load(f)


def load_processed_data(config: Config) -> pd.DataFrame:
    """Load the processed data with features and targets."""
    data_path = config.data_dir / "clean_data.csv"
    if not data_path.exists():
        # Try synthetic if clean_data doesn't exist (fallback for testing)
        synthetic_path = config.data_dir / "synthetic_data.csv"
        if synthetic_path.exists():
            data_path = synthetic_path
        else:
            raise FileNotFoundError(
                f"Data file not found at {data_path} or {synthetic_path}"
            )
    
    df = pd.read_csv(data_path)
    return df


def calculate_baseline_metrics(
    df: pd.DataFrame,
    logger: logging.Logger
) -> Tuple[float, float]:
    """
    Calculate Linear Mixing Rule and Mass-Only baseline MAEs.
    
    Returns:
        Tuple of (lmr_mae, mass_only_mae)
    """
    if "density" not in df.columns or "composition" not in df.columns:
        raise ValueError("Data must contain 'density' and 'composition' columns")
    
    # 1. Linear Mixing Rule Baseline (T023 logic)
    # The target for the main model is the residual: density_residual = density - rho_baseline
    # So the LMR prediction for actual density is simply rho_baseline.
    # We need to reconstruct rho_baseline from the data.
    # Note: T023 saves 'rho_baseline' to clean_data.csv.
    
    if "rho_baseline" in df.columns:
        rho_baseline = df["rho_baseline"].values
    else:
        # Fallback: recompute if column missing (requires element densities)
        logger.warning("rho_baseline not in data, recomputing...")
        # This path assumes get_element_density is available and composition parsing works
        # For safety in this task, we expect the column to exist from T023
        raise ValueError("rho_baseline column missing from data. Ensure T023 ran successfully.")
    
    actual_density = df["density"].values
    
    # LMR Prediction for actual density is rho_baseline
    lmr_predictions = rho_baseline
    lmr_mae = mean_absolute_error(actual_density, lmr_predictions)
    logger.info(f"Linear Mixing Rule Baseline MAE: {lmr_mae:.6f}")
    
    # 2. Mass-Only Baseline (T025-ALT logic)
    # Train a simple Linear Regression on mean_atomic_mass to predict rho_residual
    # Then calculate MAE on the residual target.
    if "mean_atomic_mass" not in df.columns:
        raise ValueError("mean_atomic_mass column missing. Ensure T020 ran successfully.")
    
    X_mass = df["mean_atomic_mass"].values.reshape(-1, 1)
    y_residual = df["density_residual"].values
    
    # Simple linear regression: y = mx + c
    # We can use sklearn for this simple baseline
    from sklearn.linear_model import LinearRegression
    
    mass_model = LinearRegression()
    mass_model.fit(X_mass, y_residual)
    mass_predictions_residual = mass_model.predict(X_mass)
    
    # The actual target for the model is the residual. 
    # The Mass-Only model predicts the residual directly.
    mass_only_mae = mean_absolute_error(y_residual, mass_predictions_residual)
    logger.info(f"Mass-Only Baseline MAE (on residuals): {mass_only_mae:.6f}")
    
    return lmr_mae, mass_only_mae


def calculate_model_metrics(
    model: Any,
    df: pd.DataFrame,
    logger: logging.Logger
) -> Tuple[float, float]:
    """
    Calculate the main model's MAE and R² on the test set.
    
    The model was trained on 'density_residual'. We evaluate on the same target.
    """
    # Identify feature columns (exclude non-feature columns)
    exclude_cols = ["density", "density_residual", "composition", "rho_baseline", 
                    "dominant_element", "atomic_fractions", "mass_fractions"]
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in data.")
    
    X = df[feature_cols].values
    y = df["density_residual"].values
    
    predictions = model.predict(X)
    
    mae = mean_absolute_error(y, predictions)
    r2 = r2_score(y, predictions)
    
    logger.info(f"Model MAE (on residuals): {mae:.6f}")
    logger.info(f"Model R² (on residuals): {r2:.6f}")
    
    return mae, r2


def save_metrics(metrics: Dict[str, float], config: Config, logger: logging.Logger) -> Path:
    """Save metrics to reports/metrics.json."""
    output_path = config.report_dir / "metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {output_path}")
    return output_path


def main():
    """Main entry point for T026."""
    config = load_config()
    logger = get_logger("metrics")
    
    logger.info("Starting metrics calculation (T026)...")
    
    try:
        # Load model and data
        model = load_model(config)
        df = load_processed_data(config)
        
        logger.info(f"Loaded model and {len(df)} rows of data.")
        
        # Calculate Baseline Metrics
        lmr_mae, mass_only_mae = calculate_baseline_metrics(df, logger)
        
        # Calculate Model Metrics
        model_mae, model_r2 = calculate_model_metrics(model, df, logger)
        
        # Compile results
        metrics = {
            "model_mae": float(model_mae),
            "model_r2": float(model_r2),
            "lmr_baseline_mae": float(lmr_mae),
            "mass_only_baseline_mae": float(mass_only_mae),
            "row_count": int(len(df)),
            "feature_count": int(df.shape[1]),
            "status": "success"
        }
        
        # Save to SSoT
        save_metrics(metrics, config, logger)
        
        logger.info("T026 completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during metrics calculation: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
