import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import pickle

# Import local utilities
from config import load_paths, load_env
from utils.logging import setup_logging, get_logger

# Ensure project root is in path for imports if run as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def load_data() -> pd.DataFrame:
    """Load the processed dataset with computed descriptors."""
    paths = load_paths()
    input_path = paths['processed_descriptors']
    logger = get_logger()
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input data file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def perform_stratified_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform an 80/20 stratified split by Crystal System.
    
    Args:
        df: The full dataset.
        test_size: Proportion of data to hold out for validation.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, val_df)
    """
    logger = get_logger()
    
    # Identify the target variable and features
    target_col = 'formation_energy_per_atom'
    stratify_col = 'crystal_system'
    
    if stratify_col not in df.columns:
        logger.warning(f"Column '{stratify_col}' not found. Falling back to random split.")
        train_df, val_df = train_test_split(
            df, test_size=test_size, random_state=random_state
        )
    else:
        # Check if there are enough classes for stratification
        if df[stratify_col].nunique() < 2:
            logger.warning(f"Not enough unique values in '{stratify_col}' for stratification. Falling back to random split.")
            train_df, val_df = train_test_split(
                df, test_size=test_size, random_state=random_state
            )
        else:
            train_df, val_df = train_test_split(
                df, 
                test_size=test_size, 
                random_state=random_state, 
                stratify=df[stratify_col]
            )
    
    logger.info(f"Split completed: Train={len(train_df)}, Val={len(val_df)}")
    return train_df, val_df

def train_models(train_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Train Random Forest and Gradient Boosting models.
    
    Args:
        train_df: Training data with features and target.
        
    Returns:
        Dictionary containing the trained model objects.
    """
    logger = get_logger()
    
    target_col = 'formation_energy_per_atom'
    feature_cols = [col for col in train_df.columns if col not in [target_col, 'material_id', 'crystal_system', 'formula']]
    
    if not feature_cols:
        raise ValueError("No feature columns found for training.")
    
    X = train_df[feature_cols]
    y = train_df[target_col]
    
    logger.info(f"Training on {len(X)} samples with {len(feature_cols)} features.")
    logger.info(f"Features: {feature_cols}")
    
    # Initialize Random Forest
    logger.info("Training Random Forest Regressor (n_estimators=200, max_depth=20)...")
    rf_model = RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1)
    rf_model.fit(X, y)
    logger.info("Random Forest training complete.")
    
    # Initialize and train Gradient Boosting (T022 Implementation)
    logger.info("Training Gradient Boosting Regressor (n_estimators=100)...")
    gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    gb_model.fit(X, y)
    logger.info("Gradient Boosting training complete.")
    
    return {
        'random_forest': rf_model,
        'gradient_boosting': gb_model,
        'feature_columns': feature_cols
    }

def save_artifacts(models: Dict[str, Any], output_path: str):
    """Save trained models and feature columns to disk."""
    logger = get_logger()
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving models to {output_path}")
    with open(output_path, 'wb') as f:
        pickle.dump(models, f)
    
    logger.info("Model artifacts saved successfully.")

def main():
    """Main entry point for the training pipeline."""
    # Setup logging
    setup_logging()
    logger = get_logger()
    logger.info("Starting model training pipeline.")
    
    try:
        # Load data
        df = load_data()
        
        # Split data
        train_df, val_df = perform_stratified_split(df)
        
        # Train models (includes T021 RF and T022 GB)
        models = train_models(train_df)
        
        # Save artifacts
        paths = load_paths()
        output_path = paths['trained_models']
        save_artifacts(models, output_path)
        
        logger.info("Training pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
