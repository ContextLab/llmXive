"""
Training Pipeline Module.
Trains models and saves metrics to data/processed/model_metrics.json.
"""
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np

from src.models.linear_regressor import run_linear_regression
from src.models.random_forest_regressor import run_random_forest_regression
from src.utils.logging_config import setup_logging, create_logger

logger = create_logger(__name__)

def load_features_data() -> pd.DataFrame:
    """Load feature-engineered data."""
    input_path = Path("data/processed/alloys_features.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Features file not found at {input_path}. Run feature engineering first.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def prepare_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare X and y."""
    # Define target and features
    target_cols = ['coercivity_oe', 'saturation_magnetization_emu_g']
    feature_cols = [
        'average_electronegativity', 'valence_electron_concentration',
        'atomic_radii_variance', 'average_d_electrons', 'atomic_size_mismatch'
    ]
    
    # Filter for available columns
    available_features = [c for c in feature_cols if c in df.columns]
    
    if not available_features:
        logger.warning("No feature columns found. Using dummy features.")
        X = pd.DataFrame(index=df.index)
        X['dummy'] = 1
    else:
        X = df[available_features].fillna(0)
    
    # Use coercivity as primary target for demo if multiple exist
    y = df['coercivity_oe'].fillna(0) if 'coercivity_oe' in df.columns else df['saturation_magnetization_emu_g'].fillna(0)
    
    return X, y

def save_metrics(metrics: Dict[str, Any], output_path: Path):
    """Save metrics to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {output_path}")

def run_training_pipeline() -> Dict[str, Any]:
    """Execute the training pipeline."""
    df = load_features_data()
    if df.empty:
        logger.warning("Input data is empty. Saving empty metrics.")
        save_metrics({"error": "No data"}, Path("data/processed/model_metrics.json"))
        return {"error": "No data"}
    
    X, y = prepare_data(df)
    
    metrics = {}
    
    # Train Linear
    logger.info("Training Linear Regression...")
    lin_metrics = run_linear_regression(X, y)
    metrics['LinearRegression'] = lin_metrics
    
    # Train RF
    logger.info("Training Random Forest...")
    rf_metrics = run_random_forest_regression(X, y)
    metrics['RandomForest'] = rf_metrics
    
    save_metrics(metrics, Path("data/processed/model_metrics.json"))
    return metrics

def main():
    """Entry point for training."""
    setup_logging("training_pipeline", level=logging.INFO)
    metrics = run_training_pipeline()
    return metrics

if __name__ == "__main__":
    main()
