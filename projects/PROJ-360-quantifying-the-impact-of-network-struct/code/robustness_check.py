import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analyze import setup_analysis_logger, load_metrics_csv, calculate_vif, log_vif_results, verify_vif_scope, filter_features
from config import Config, initialize_environment

def setup_robustness_logger():
    logger = logging.getLogger("robustness_check")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_filtered_features() -> pd.DataFrame:
    """Load the filtered features dataset produced by T020b."""
    path = Path("data/processed/filtered_features.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required input file missing: {path}")
    
    logger = logging.getLogger("robustness_check")
    logger.info(f"Loading filtered features from {path}")
    df = pd.read_csv(path)
    
    # Verify required columns exist
    required_cols = ["material_id", "thermal_conductivity_scalar", 
                     "average_degree", "average_path_length", "clustering_coefficient",
                     "unit_cell_volume", "total_atom_count", "mean_atomic_mass"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in filtered_features.csv: {missing}")
    
    return df

def run_robustness_regression(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, Any]:
    """
    Perform multiple regression on filtered features to predict thermal conductivity.
    This serves as a robustness check controlling for physical confounders.
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score, mean_squared_error

    logger.info("Preparing data for multiple regression...")
    
    # Define features (network metrics + physical descriptors)
    feature_cols = [
        "average_degree", 
        "average_path_length", 
        "clustering_coefficient",
        "unit_cell_volume", 
        "total_atom_count", 
        "mean_atomic_mass"
    ]
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, "thermal_conductivity_scalar"]
    
    # Handle any remaining NaNs in target
    valid_mask = ~y.isna()
    X = X[valid_mask]
    y = y[valid_mask]
    
    if len(X) < 5:
        logger.warning(f"Insufficient data points for regression after filtering: {len(X)}")
        return {
            "model_r2": None,
            "model_rmse": None,
            "feature_coefficients": {},
            "error": "Insufficient data"
        }

    logger.info(f"Running regression on {len(X)} samples with {len(feature_cols)} features.")
    
    model = LinearRegression()
    model.fit(X, y)
    
    y_pred = model.predict(X)
    
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    
    coefficients = dict(zip(feature_cols, model.coef_))
    intercept = model.intercept_
    
    logger.info(f"Regression complete. R²: {r2:.4f}, RMSE: {rmse:.4f}")
    
    return {
        "model_r2": float(r2),
        "model_rmse": float(rmse),
        "feature_coefficients": {k: float(v) for k, v in coefficients.items()},
        "intercept": float(intercept),
        "n_samples": int(len(X)),
        "n_features": int(len(feature_cols))
    }

def save_robustness_results(results: Dict[str, Any], logger: logging.Logger):
    """Save results to results/robustness_check.json."""
    output_path = Path("results/robustness_check.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved robustness check results to {output_path}")

def main():
    logger = setup_robustness_logger()
    initialize_environment()
    
    try:
        # Load data
        df = load_filtered_features()
        
        # Run regression
        results = run_robustness_regression(df, logger)
        
        # Save results
        save_robustness_results(results, logger)
        
        logger.info("Robustness check completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
