"""
Train_fallback module for the Solar Irradiance Reconstruction pipeline.

This module implements the Cycle-Agnostic fallback model training (Task T019).
It trains a Random Forest model on GSN data only (no Cycle ID features) using
the satellite-era dataset (2003–present) to serve as a fallback for cycles
not present in the primary training set.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import joblib
import numpy as np

from config import ensure_directories
from env_config import get_processed_data_path, get_models_artifacts_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SAT_EPOCH_START = 2003
FALLBACK_MODEL_PATH = "fallback_model.joblib"
FALLBACK_FEATURES = ["gsn"]  # Cycle-agnostic: only GSN, no Cycle ID

def load_preprocessed_data() -> pd.DataFrame:
    """
    Load the preprocessed data from the processed data directory.
    
    Returns:
        pd.DataFrame: The preprocessed dataset containing GSN and TSI data.
        
    Raises:
        FileNotFoundError: If the preprocessed data file does not exist.
    """
    data_path = get_processed_data_path()
    file_path = data_path / "preprocessed_data.parquet"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Preprocessed data file not found at {file_path}. "
            "Please ensure T014c (preprocessing) has been completed."
        )
    
    logger.info(f"Loading preprocessed data from {file_path}")
    df = pd.read_parquet(file_path)
    
    # Ensure required columns exist
    required_cols = ['date', 'gsn', 'tsi', 'cycle_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in preprocessed data: {missing_cols}")
    
    return df

def prepare_fallback_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare features and target for the fallback model.
    
    Filters the dataset to the satellite era (>= 2003) and selects only
    GSN as the feature (Cycle-Agnostic).
    
    Args:
        df (pd.DataFrame): The full preprocessed dataset.
        
    Returns:
        Tuple[pd.DataFrame, pd.Series]: Features (GSN only) and target (TSI).
    """
    logger.info(f"Filtering data to satellite era (>= {SAT_EPOCH_START})")
    
    # Extract year from date column if it's a datetime or string
    if pd.api.types.is_datetime64_any_dtype(df['date']):
        df = df.copy()
        df['year'] = df['date'].dt.year
    else:
        # Try to parse as datetime
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['year'] = df['date'].dt.year
    
    # Filter for satellite era
    satellite_mask = df['year'] >= SAT_EPOCH_START
    satellite_df = df[satellite_mask].copy()
    
    if satellite_df.empty:
        raise ValueError(f"No data found for satellite era (>= {SAT_EPOCH_START}).")
    
    logger.info(f"Satellite era data shape: {satellite_df.shape}")
    logger.info(f"Date range: {satellite_df['date'].min()} to {satellite_df['date'].max()}")
    
    # Prepare features: GSN only (Cycle-Agnostic)
    X = satellite_df[FALLBACK_FEATURES].copy()
    y = satellite_df['tsi']
    
    # Drop rows with missing values
    mask = X.notna().all(axis=1) & y.notna()
    X_clean = X[mask]
    y_clean = y[mask]
    
    logger.info(f"Final training set size (after dropping NaNs): {X_clean.shape[0]}")
    
    if X_clean.empty:
        raise ValueError("No valid data points remaining after cleaning.")
        
    return X_clean, y_clean

def train_fallback_model(X: pd.DataFrame, y: pd.Series) -> object:
    """
    Train the Cycle-Agnostic fallback model.
    
    Uses a Random Forest regressor with parameters optimized for robustness
    and CPU-only execution (max_depth=10, n_estimators=100).
    
    Args:
        X (pd.DataFrame): Feature matrix (GSN only).
        y (pd.Series): Target vector (TSI).
        
    Returns:
        object: The trained Random Forest model.
    """
    logger.info("Training Cycle-Agnostic fallback model (Random Forest)...")
    logger.info(f"Model parameters: max_depth=10, n_estimators=100, random_state=42")
    
    from sklearn.ensemble import RandomForestRegressor
    
    model = RandomForestRegressor(
        max_depth=10,
        n_estimators=100,
        random_state=42,
        n_jobs=-1  # Use all available CPU cores
    )
    
    model.fit(X, y)
    
    # Calculate training metrics for logging
    y_pred = model.predict(X)
    mse = np.mean((y - y_pred) ** 2)
    rmse = np.sqrt(mse)
    r2 = 1 - (np.sum((y - y_pred) ** 2) / np.sum((y - y.mean()) ** 2))
    
    logger.info(f"Training RMSE: {rmse:.4f} W/m²")
    logger.info(f"Training R²: {r2:.4f}")
    
    return model

def save_model_artifact(model: object, output_path: Path) -> None:
    """
    Save the trained model to disk.
    
    Args:
        model (object): The trained model instance.
        output_path (Path): The path where the model artifact will be saved.
    """
    logger.info(f"Saving fallback model to {output_path}")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(model, output_path)
    
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Model saved successfully. Size: {size_mb:.2f} MB")
    else:
        raise RuntimeError(f"Failed to save model to {output_path}")

def run_fallback_training_pipeline() -> Dict[str, Any]:
    """
    Execute the full fallback model training pipeline.
    
    Steps:
        1. Load preprocessed data.
        2. Prepare features (GSN only) and target (TSI) for satellite era.
        3. Train the Cycle-Agnostic Random Forest model.
        4. Save the model artifact.
        
    Returns:
        Dict[str, Any]: A dictionary containing training metrics and paths.
    """
    ensure_directories()
    
    try:
        # 1. Load Data
        df = load_preprocessed_data()
        
        # 2. Prepare Features
        X, y = prepare_fallback_features(df)
        
        # 3. Train Model
        model = train_fallback_model(X, y)
        
        # 4. Save Artifact
        artifacts_dir = get_models_artifacts_path()
        model_path = artifacts_dir / FALLBACK_MODEL_PATH
        save_model_artifact(model, model_path)
        
        # 5. Return Summary
        summary = {
            "status": "success",
            "model_path": str(model_path),
            "model_type": "RandomForestRegressor",
            "parameters": {
                "max_depth": 10,
                "n_estimators": 100,
                "features": FALLBACK_FEATURES,
                "satellite_era_start": SAT_EPOCH_START
            },
            "training_samples": int(X.shape[0]),
            "message": "Cycle-Agnostic fallback model trained and saved successfully."
        }
        
        logger.info("Fallback training pipeline completed successfully.")
        return summary
        
    except Exception as e:
        logger.error(f"Fallback training pipeline failed: {e}")
        raise

def main():
    """Main entry point for the fallback training script."""
    logger.info("Starting Fallback Model Training (Task T019)...")
    
    try:
        result = run_fallback_training_pipeline()
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        # Re-raise to ensure the runner knows the task failed
        raise

if __name__ == "__main__":
    main()