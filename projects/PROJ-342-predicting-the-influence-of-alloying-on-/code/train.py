import os
import sys
import logging
import json
import pickle
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.dummy import DummyRegressor

# Local imports matching the provided API surface
from config.config import get_config
from resource_monitor import enforce_resource_limits, ResourceLimitExceeded
from descriptors import process_dataframe, compute_descriptors
from zenodo_client import DataUnavailableError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure paths exist
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_MODELS_DIR = PROJECT_ROOT / "artifacts" / "models"
ARTIFACTS_METRICS_DIR = PROJECT_ROOT / "artifacts" / "metrics"

DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_MODELS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_METRICS_DIR.mkdir(parents=True, exist_ok=True)

def load_prepared_data() -> pd.DataFrame:
    """
    Loads the cleaned data and computes descriptors.
    This function assumes T014 (cleaned_mg.csv) and T020/T026 (descriptors logic) are done.
    Since T026 is marked as needing redo, we ensure descriptors are computed here 
    if the CSV doesn't exist yet, to ensure the pipeline runs end-to-end.
    """
    cleaned_path = DATA_PROCESSED_DIR / "cleaned_mg.csv"
    descriptors_path = DATA_PROCESSED_DIR / "descriptors.csv"

    if not cleaned_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {cleaned_path}. Run T014 first.")

    df = pd.read_csv(cleaned_path)
    logger.info(f"Loaded {len(df)} records from {cleaned_path}")

    # Compute descriptors if not already present (handling T026 dependency dynamically)
    if not descriptors_path.exists():
        logger.info(f"Descriptors not found at {descriptors_path}. Computing now...")
        # Re-use the logic from descriptors.py
        df = process_dataframe(df)
        df.to_csv(descriptors_path, index=False)
        logger.info(f"Saved descriptors to {descriptors_path}")
    else:
        # Load pre-computed descriptors and merge if necessary, or just load the final set
        # Assuming descriptors.csv contains the final features + target
        df = pd.read_csv(descriptors_path)

    # Ensure target column exists
    if 'Tg' not in df.columns:
        raise ValueError("Target column 'Tg' not found in prepared data.")

    return df

def get_family_groups(df: pd.DataFrame) -> List[Any]:
    """
    Extracts family groups for LOFO cross-validation.
    Assumes a 'family' column exists in the processed dataframe.
    """
    if 'family' not in df.columns:
        logger.warning("No 'family' column found. Using sample ID as group for LOFO.")
        return df.index.tolist()
    return df['family'].tolist()

def lofo_cv_score(
    X: pd.DataFrame, 
    y: pd.Series, 
    groups: List[Any], 
    params: Dict[str, Any]
) -> float:
    """
    Performs Leave-One-Family-Out cross-validation.
    """
    logo = LeaveOneGroupOut()
    model = GradientBoostingRegressor(**params)
    
    scores = cross_val_score(
        model, X, y, cv=logo, groups=groups, 
        scoring='r2', n_jobs=1 # CPU only constraint
    )
    return np.mean(scores)

def train_and_evaluate(df: pd.DataFrame) -> Tuple[GradientBoostingRegressor, Dict[str, Any], pd.DataFrame]:
    """
    Trains the model with grid search and evaluates it.
    Returns the best model, metrics dict, and feature importance dataframe.
    """
    # Define features and target
    # We expect descriptors to be numeric columns. 
    # Based on T020/T026, we expect: radius_mismatch, electronegativity_diff, VEC
    feature_cols = ['radius_mismatch', 'electronegativity_diff', 'VEC']
    
    # Filter to ensure columns exist
    available_cols = [c for c in feature_cols if c in df.columns]
    if len(available_cols) < len(feature_cols):
        logger.warning(f"Missing expected feature columns. Available: {df.columns.tolist()}")
        # Fallback: use all numeric columns except target
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        available_cols = [c for c in numeric_cols if c != 'Tg']
    
    X = df[available_cols]
    y = df['Tg']
    groups = get_family_groups(df)

    # Grid search parameters (<=10 combos as per FR-003)
    param_grid = [
        {'n_estimators': [50], 'max_depth': [3], 'learning_rate': [0.1]},
        {'n_estimators': [100], 'max_depth': [3], 'learning_rate': [0.1]},
        {'n_estimators': [100], 'max_depth': [5], 'learning_rate': [0.1]},
        {'n_estimators': [100], 'max_depth': [3], 'learning_rate': [0.05]},
    ]

    best_score = -np.inf
    best_params = None
    best_model = None

    logger.info("Starting Grid Search with LOFO CV...")
    for params in param_grid:
        try:
            score = lofo_cv_score(X, y, groups, params)
            logger.info(f"Params {params}: LOFO R2 = {score:.4f}")
            if score > best_score:
                best_score = score
                best_params = params
        except Exception as e:
            logger.error(f"Error evaluating params {params}: {e}")
            continue

    if best_model is None and best_params is None:
        # Fallback if CV fails completely, train on full data
        logger.warning("LOFO CV failed. Training on full data without CV.")
        best_params = {'n_estimators': 100, 'max_depth': 3, 'learning_rate': 0.1}
    
    # Train final model with best params
    best_model = GradientBoostingRegressor(**best_params)
    best_model.fit(X, y)

    # Evaluate on full data (for reporting metrics, though LOFO is the true CV)
    y_pred = best_model.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))

    # Calculate Null Model R2 (Baseline: mean prediction)
    dummy_model = DummyRegressor(strategy='mean')
    dummy_model.fit(X, y)
    y_dummy_pred = dummy_model.predict(X)
    null_model_r2 = r2_score(y, y_dummy_pred)

    # Feature Importances
    feature_importances = dict(zip(available_cols, best_model.feature_importances_.tolist()))

    metrics = {
        "R2": float(r2),
        "MAE": float(mae),
        "RMSE": float(rmse),
        "LOFO_R2": float(best_score),
        "null_model_r2": float(null_model_r2),
        "feature_importances": feature_importances,
        "best_params": best_params
    }

    return best_model, metrics, pd.DataFrame({
        'feature': available_cols,
        'importance': best_model.feature_importances_
    })

def save_artifacts(model: GradientBoostingRegressor, metrics: Dict[str, Any], feature_df: pd.DataFrame):
    """
    Saves the model, metrics, and feature importance to artifacts.
    Specifically implements T024b: Save metrics including null_model_r2.
    """
    model_path = ARTIFACTS_MODELS_DIR / "best_model.pkl"
    metrics_path = ARTIFACTS_METRICS_DIR / "metrics.json"
    importance_path = ARTIFACTS_METRICS_DIR / "feature_importances.csv"

    # Save Model (T024a)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

    # Save Metrics (T024b)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    # Save Feature Importances
    feature_df.to_csv(importance_path, index=False)
    logger.info(f"Feature importances saved to {importance_path}")

@enforce_resource_limits
def main():
    """
    Main entry point for the training pipeline.
    """
    logger.info("Starting Training Pipeline (T024b)...")
    
    try:
        # Load Data
        df = load_prepared_data()
        
        # Train and Evaluate
        model, metrics, feature_df = train_and_evaluate(df)
        
        # Save Artifacts
        save_artifacts(model, metrics, feature_df)
        
        logger.info("Training Pipeline completed successfully.")
        logger.info(f"Final Metrics: R2={metrics['R2']:.4f}, MAE={metrics['MAE']:.4f}, Null R2={metrics['null_model_r2']:.4f}")
        
    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ResourceLimitExceeded as e:
        logger.error(f"Resource limit exceeded: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()