"""
Train a Cycle-Agnostic fallback model for TSI reconstruction.

This module implements Task T019:
1. Trains a single Random Forest model on GSN data only (no Cycle ID features).
2. Calculates per-cycle baseline offsets (mean residuals) for satellite-era cycles.
3. Saves the model and offsets to disk.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Import project configuration and data utilities
# Note: Using relative imports compatible with the project structure
try:
    from config import ensure_directories
    from data.preprocessing import load_raw_data
except ImportError:
    # Fallback for direct execution if path setup differs
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from config import ensure_directories
    from data.preprocessing import load_raw_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
GAP_FILL_THRESHOLD_YEARS = 1.0
RANDOM_SEED = 42
RF_MAX_DEPTH = 10
RF_N_ESTIMATORS = 100


def load_preprocessed_data() -> pd.DataFrame:
    """
    Load the preprocessed dataset containing GSN, TSI, and Cycle ID.
    Expects `data/processed/preprocessed_data.parquet` to exist (output of T014/T015).
    """
    data_path = Path("data/processed/preprocessed_data.parquet")
    if not data_path.exists():
        raise FileNotFoundError(
            f"Preprocessed data not found at {data_path}. "
            "Please run the preprocessing pipeline (Task T014) first."
        )
    logger.info(f"Loading preprocessed data from {data_path}")
    df = pd.read_parquet(data_path)
    return df


def prepare_fallback_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare features for the Cycle-Agnostic model.
    Features: GSN only.
    Target: TSI.
    Filters to satellite-era data (approx 2003-present) where TSI is available.
    """
    # Filter for satellite era (where TSI measurements exist)
    # Assuming TSI column is present and non-null in satellite era
    satellite_mask = df['tsi'].notna()
    df_sat = df[satellite_mask].copy()

    if df_sat.empty:
        raise ValueError("No satellite-era data found for training fallback model.")

    # Features: Only GSN (Cycle-Agnostic)
    # We assume 'gsn' is the preprocessed sunspot number column
    feature_cols = ['gsn']
    X = df_sat[feature_cols]
    y = df_sat['tsi']

    # Handle any remaining NaNs in GSN (should be filled by T014, but safety check)
    if X.isnull().any().any():
        logger.warning("NaN values found in GSN features. Dropping rows.")
        valid_mask = ~X.isnull().any(axis=1)
        X = X[valid_mask]
        y = y[valid_mask]

    logger.info(f"Prepared {len(X)} samples for fallback model training.")
    return X, y


def calculate_cycle_offsets(df: pd.DataFrame, model: RandomForestRegressor) -> Dict[str, float]:
    """
    Calculate the mean residual (baseline offset) for each cycle.
    This quantifies the systematic bias of the global model per cycle.
    """
    # Ensure we have cycle information
    if 'cycle_id' not in df.columns:
        raise ValueError("Dataset missing 'cycle_id' column required for offset calculation.")

    # Filter to satellite era for offset calculation
    satellite_mask = df['tsi'].notna()
    df_sat = df[satellite_mask].copy()

    # Predict using the global fallback model
    X_pred = df_sat[['gsn']]
    # Drop rows with NaN GSN if any
    valid_pred_mask = ~X_pred.isnull().any(axis=1)
    X_pred = X_pred[valid_pred_mask]
    y_true = df_sat.loc[valid_pred_mask, 'tsi']
    cycle_ids = df_sat.loc[valid_pred_mask, 'cycle_id']

    y_pred = model.predict(X_pred)
    residuals = y_true - y_pred

    # Group by cycle_id and calculate mean residual
    offsets = residuals.groupby(cycle_ids).mean()

    # Convert to dictionary, handling potential NaN cycle_ids if any
    result = {}
    for cycle_id, offset in offsets.items():
        if pd.notna(cycle_id):
            result[str(cycle_id)] = float(offset)

    logger.info(f"Calculated offsets for {len(result)} cycles.")
    return result


def train_fallback_model(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    """
    Train a Random Forest regressor on GSN data only.
    """
    logger.info(f"Training Cycle-Agnostic Random Forest (max_depth={RF_MAX_DEPTH}, n_estimators={RF_N_ESTIMATORS})...")
    
    model = RandomForestRegressor(
        n_estimators=RF_N_ESTIMATORS,
        max_depth=RF_MAX_DEPTH,
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    
    model.fit(X, y)
    
    # In-sample evaluation for logging
    y_pred = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    
    logger.info(f"Training complete. In-sample RMSE: {rmse:.4f}, R²: {r2:.4f}")
    return model


def run_fallback_training_pipeline() -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """
    Orchestrates the full fallback training pipeline:
    1. Load data.
    2. Prepare features.
    3. Train model.
    4. Calculate offsets.
    5. Save artifacts.
    """
    # Ensure output directories exist
    ensure_directories()

    # 1. Load Data
    df = load_preprocessed_data()

    # 2. Prepare Features (GSN only)
    X, y = prepare_fallback_features(df)

    # 3. Train Model
    model = train_fallback_model(X, y)

    # 4. Calculate Offsets
    # We need the original df with cycle_ids to calculate offsets correctly
    # The df from load_preprocessed_data includes cycle_id
    offsets = calculate_cycle_offsets(df, model)

    # 5. Save Artifacts
    model_path = Path("code/models/artifacts/fallback_model.joblib")
    offsets_path = Path("data/processed/cycle_specific_coefficients.json")

    # Save model
    os.makedirs(model_path.parent, exist_ok=True)
    joblib.dump(model, model_path)
    logger.info(f"Saved fallback model to {model_path}")

    # Save offsets
    os.makedirs(offsets_path.parent, exist_ok=True)
    with open(offsets_path, 'w') as f:
        json.dump(offsets, f, indent=2)
    logger.info(f"Saved cycle offsets to {offsets_path}")

    return model, offsets


def main():
    """Entry point for the fallback training script."""
    try:
        model, offsets = run_fallback_training_pipeline()
        logger.info("T019 Fallback Training Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"T019 Fallback Training Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()