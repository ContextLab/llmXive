"""
Script to generate model_metrics.json by loading trained models and evaluating them.
This script implements task T037.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib

# Add project root to path if necessary
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import setup_logging, create_logger
from src.models.linear_regressor import load_features_data, prepare_data
from src.models.random_forest_regressor import load_features_data as load_rf_data

# Setup logging
logger = setup_logging(level=logging.INFO)

def load_model_metrics(model_path: Path) -> Optional[Any]:
    """Load a trained model from disk."""
    if not model_path.exists():
        logger.warning(f"Model file not found: {model_path}")
        return None
    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}")
        return None

def aggregate_metrics(
    linear_model: Any,
    rf_model: Any,
    features_path: Path,
    target_col: str = "coercivity_oe"
) -> Dict[str, Any]:
    """
    Evaluate models and compute metrics.
    Returns a dictionary with R2, MAE, RMSE, and CV scores.
    """
    if features_path.exists():
        df = pd.read_csv(features_path)
    else:
        # Fallback: try to load from raw features if processed file missing
        # This should ideally not happen if pipeline runs correctly
        logger.error(f"Features file not found: {features_path}")
        raise FileNotFoundError(f"Features file not found: {features_path}")

    # Prepare data using the shared utility
    # We need to identify feature columns (exclude composition, target, metadata)
    exclude_cols = ["composition", "coercivity_oe", "saturation_magnetization_emu_g", "source_type", "synthesis_method"]
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")

    X = df[feature_cols].fillna(0) # Handle any remaining NaNs
    y = df[target_col].fillna(0)

    results = {}

    # Evaluate Linear Regression
    if linear_model:
        try:
            y_pred_lin = linear_model.predict(X)
            r2_lin = r2_score(y, y_pred_lin)
            mae_lin = mean_absolute_error(y, y_pred_lin)
            rmse_lin = np.sqrt(mean_squared_error(y, y_pred_lin))
            # CV score is usually stored in the model's best_score_ if GridSearchCV was used
            cv_lin = getattr(linear_model, 'best_score_', None)
            if cv_lin is None and hasattr(linear_model, 'cv_results_'):
                cv_lin = max([r['mean_test_score'] for r in linear_model.cv_results_['params']])
            
            results["LinearRegression"] = {
                "r2": float(r2_lin),
                "mae": float(mae_lin),
                "rmse": float(rmse_lin),
                "cv_score": float(cv_lin) if cv_lin is not None else None
            }
        except Exception as e:
            logger.error(f"Error evaluating Linear Regression: {e}")
            results["LinearRegression"] = {"error": str(e)}
    else:
        results["LinearRegression"] = {"error": "Model not loaded"}

    # Evaluate Random Forest
    if rf_model:
        try:
            y_pred_rf = rf_model.predict(X)
            r2_rf = r2_score(y, y_pred_rf)
            mae_rf = mean_absolute_error(y, y_pred_rf)
            rmse_rf = np.sqrt(mean_squared_error(y, y_pred_rf))
            cv_rf = getattr(rf_model, 'best_score_', None)
            if cv_rf is None and hasattr(rf_model, 'cv_results_'):
                cv_rf = max([r['mean_test_score'] for r in rf_model.cv_results_['params']])

            results["RandomForest"] = {
                "r2": float(r2_rf),
                "mae": float(mae_rf),
                "rmse": float(rmse_rf),
                "cv_score": float(cv_rf) if cv_rf is not None else None
            }
        except Exception as e:
            logger.error(f"Error evaluating Random Forest: {e}")
            results["RandomForest"] = {"error": str(e)}
    else:
        results["RandomForest"] = {"error": "Model not loaded"}

    return results

def main():
    """Main entry point for generating model metrics."""
    # Define paths relative to project root
    models_dir = project_root / "code" / "models"
    features_path = project_root / "data" / "processed" / "alloys_features.csv"
    output_path = project_root / "data" / "processed" / "model_metrics.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting model metrics generation (T037)...")

    # Load models
    linear_model_path = models_dir / "linear_regression_model.joblib"
    rf_model_path = models_dir / "random_forest_model.joblib"

    linear_model = load_model_metrics(linear_model_path)
    rf_model = load_model_metrics(rf_model_path)

    if not linear_model and not rf_model:
        logger.error("No models found to evaluate. Exiting.")
        # Write a failure report
        with open(output_path, 'w') as f:
            json.dump({"error": "No models found", "models_checked": [str(linear_model_path), str(rf_model_path)]}, f, indent=2)
        return

    # Load features and compute metrics
    try:
        metrics = aggregate_metrics(linear_model, rf_model, features_path)
        
        # Write results
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Model metrics saved to {output_path}")
        logger.info(f"Linear Regression R2: {metrics.get('LinearRegression', {}).get('r2', 'N/A')}")
        logger.info(f"Random Forest R2: {metrics.get('RandomForest', {}).get('r2', 'N/A')}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        with open(output_path, 'w') as f:
            json.dump({"error": "Data file missing", "details": str(e)}, f, indent=2)
    except Exception as e:
        logger.error(f"Unexpected error during metrics generation: {e}")
        with open(output_path, 'w') as f:
            json.dump({"error": "Unexpected error", "details": str(e)}, f, indent=2)

if __name__ == "__main__":
    main()