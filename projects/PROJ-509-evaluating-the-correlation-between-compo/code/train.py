import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib

# Project-relative imports handling
try:
    from config import load_paths
    from utils.logging import get_logger
except ImportError:
    # Fallback for direct execution if path setup is missing
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import load_paths
    from utils.logging import get_logger

def load_data() -> pd.DataFrame:
    """
    Loads the processed dataset with computed descriptors.
    Returns the DataFrame containing features and target.
    """
    paths = load_paths()
    input_path = paths["data_processed"] / "computed_descriptors.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger = get_logger()
    logger.info(f"Loaded dataset with shape: {df.shape}")
    return df

def perform_stratified_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs an 80/20 stratified split by 'Crystal System' to ensure structural diversity.
    Returns (train_df, val_df).
    """
    logger = get_logger()
    
    if "Crystal System" not in df.columns:
        raise ValueError("Column 'Crystal System' not found in dataset for stratification.")
    
    # Handle potential NaNs in stratification column
    if df["Crystal System"].isna().any():
        logger.warning("NaNs found in 'Crystal System', dropping those rows for split.")
        df = df.dropna(subset=["Crystal System"])

    train_df, val_df = train_test_split(
        df, 
        test_size=test_size, 
        stratify=df["Crystal System"], 
        random_state=random_state
    )
    
    logger.info(f"Split complete. Train: {len(train_df)}, Val: {len(val_df)}")
    return train_df, val_df

def train_models(train_df: pd.DataFrame, target_col: str = "formation_energy_per_atom") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Trains Random Forest and Gradient Boosting Regressors on the training split.
    
    Random Forest: n_estimators=200, max_depth=20
    Gradient Boosting: n_estimators=100
    
    Returns a tuple of (models_dict, metrics_dict).
    """
    logger = get_logger()
    
    # Define feature columns (exclude target and non-feature metadata)
    exclude_cols = ["formation_energy_per_atom", "Crystal System", "formula", "material_id"]
    feature_cols = [col for col in train_df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found after excluding target and metadata.")
    
    X = train_df[feature_cols]
    y = train_df[target_col]
    
    logger.info(f"Training on {len(feature_cols)} features: {feature_cols}")
    
    # 1. Train Random Forest
    logger.info("Training Random Forest Regressor...")
    rf_model = RandomForestRegressor(
        n_estimators=200, 
        max_depth=20, 
        n_jobs=-1, 
        random_state=42
    )
    rf_model.fit(X, y)
    
    # 2. Train Gradient Boosting (Task T022)
    logger.info("Training Gradient Boosting Regressor...")
    gb_model = GradientBoostingRegressor(
        n_estimators=100,
        random_state=42,
        learning_rate=0.1,
        max_depth=5,
        subsample=0.8
    )
    gb_model.fit(X, y)
    
    models = {
        "random_forest": rf_model,
        "gradient_boosting": gb_model
    }
    
    # Return models and empty metrics placeholder (metrics calculated in evaluate.py)
    # The task specifically asks to train, but we return the structure needed for saving
    return models, {}

def save_artifacts(models: Dict[str, Any], metrics: Dict[str, Any], val_df: pd.DataFrame = None):
    """
    Saves trained models to data/evaluation/trained_models.pkl
    and initializes the metrics structure in data/evaluation/model_metrics.json.
    """
    paths = load_paths()
    models_dir = paths["data_evaluation"]
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / "trained_models.pkl"
    metrics_path = models_dir / "model_metrics.json"
    
    logger = get_logger()
    
    # Save models
    joblib.dump(models, model_path)
    logger.info(f"Saved models to {model_path}")
    
    # Initialize/Update metrics file
    # If metrics are passed (e.g., from a combined run), save them. 
    # Otherwise, create the structure if it doesn't exist.
    if metrics:
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Saved metrics to {metrics_path}")
    else:
        # Create a placeholder structure indicating models are trained but not yet evaluated
        placeholder_metrics = {
            "random_forest": {"status": "trained", "metrics_pending": True},
            "gradient_boosting": {"status": "trained", "metrics_pending": True},
            "split_info": {
                "stratified_by": "Crystal System",
                "test_size": 0.2
            }
        }
        with open(metrics_path, 'w') as f:
            json.dump(placeholder_metrics, f, indent=2)
        logger.info(f"Initialized metrics placeholder at {metrics_path}")

def main():
    """
    Main entry point for the training pipeline.
    1. Load data
    2. Stratified split
    3. Train RF and GB models
    4. Save artifacts
    """
    logger = get_logger()
    logger.info("Starting training pipeline...")
    
    try:
        # Load data
        df = load_data()
        
        # Split
        train_df, val_df = perform_stratified_split(df)
        
        # Train models
        models, metrics = train_models(train_df)
        
        # Save artifacts
        save_artifacts(models, metrics, val_df)
        
        logger.info("Training pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()