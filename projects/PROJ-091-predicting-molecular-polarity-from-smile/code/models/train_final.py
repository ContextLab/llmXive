"""
Train the final model on the full training set and save to data/processed/model.pkl.

This script loads the pre-processed descriptors and the data split information,
retrains the LightGBM model on the combined training data (train + validation),
and persists the final model artifact.

Dependencies:
- data/processed/descriptors.parquet (from T018)
- data/processed/splits.pkl (from T022)
- code/config.yaml (for hyperparameters from T025)
"""
import os
import sys
import logging
import pickle
import gc
from pathlib import Path

import pandas as pd
import numpy as np
import lightgbm as lgb

# Project relative imports
from utils.config import load_hyperparameters, get_config_summary
from utils.logging_config import get_logger, set_log_level

# Ensure project root is in path for relative imports if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def load_training_data():
    """
    Loads the descriptors and splits, then combines train and validation sets
    to form the full training dataset for the final model.
    
    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: (X_full, y_full, feature_names)
    """
    logger = get_logger(__name__)
    
    # Paths
    descriptors_path = Path("data/processed/descriptors.parquet")
    splits_path = Path("data/processed/splits.pkl")
    
    if not descriptors_path.exists():
        raise FileNotFoundError(f"Descriptors file not found: {descriptors_path}. "
                                "Run T018 to generate it.")
    if not splits_path.exists():
        raise FileNotFoundError(f"Splits file not found: {splits_path}. "
                                "Run T022 to generate it.")
    
    logger.info(f"Loading descriptors from {descriptors_path}")
    df = pd.read_parquet(descriptors_path)
    
    # Separate features and target
    # Assuming the target column is named 'target' or similar based on data-model.md
    # We need to identify the target column. Usually it's the last one or explicitly named.
    # Based on standard pipelines, let's assume 'dipole_moment' or 'target'.
    # Let's inspect columns. The loader usually outputs 'smiles', 'target', and descriptors.
    # We need to drop non-numeric columns.
    
    feature_cols = [col for col in df.columns if col not in ['smiles', 'target', 'smiles_idx']]
    if 'target' not in df.columns:
        # Fallback: if target column has a different name, we might need to infer it.
        # But based on T007/T014, 'target' is the standard name.
        raise ValueError("Expected 'target' column in descriptors parquet file.")
        
    X = df[feature_cols].values
    y = df['target'].values
    feature_names = feature_cols
    
    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features.")
    
    # Load splits to identify which rows are in the training set (including validation)
    # T022 split_data.py saves a dict with 'train_indices', 'val_indices', 'test_indices'
    with open(splits_path, 'rb') as f:
        splits = pickle.load(f)
    
    train_indices = splits['train_indices']
    val_indices = splits['val_indices']
    
    # Combine train and validation for final training
    final_train_indices = np.concatenate([train_indices, val_indices])
    
    X_final = X[final_train_indices]
    y_final = y[final_train_indices]
    
    logger.info(f"Combined training set size: {len(final_train_indices)} samples.")
    
    # Clean up memory
    del df, X, y
    gc.collect()
    
    return X_final, y_final, feature_names

def train_final_model(X, y, feature_names):
    """
    Trains the final LightGBM model using hyperparameters from config.
    
    Args:
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names
        
    Returns:
        lgb.Booster: The trained model
    """
    logger = get_logger(__name__)
    
    # Load hyperparameters
    # T025 updates config.yaml with optimal params
    params = load_hyperparameters()
    
    # Ensure specific training parameters are set
    train_params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'verbose': -1,
        'seed': 42, # Hardcoded seed from T004
        **params
    }
    
    logger.info("Training final model with parameters:")
    for k, v in train_params.items():
        logger.info(f"  {k}: {v}")
    
    # Create dataset
    train_data = lgb.Dataset(X, label=y, feature_name=feature_names)
    
    # Train
    # num_boost_round is a critical parameter, ensure it's in params or default
    num_boost_round = train_params.get('num_boost_round', 1000)
    
    model = lgb.train(
        train_params,
        train_data,
        num_boost_round=num_boost_round,
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)] if 'num_boost_round' in params else None
    )
    
    logger.info("Final model training complete.")
    return model

def save_model(model, output_path):
    """
    Saves the trained model to the specified path using pickle.
    
    Args:
        model: The trained LightGBM booster
        output_path: Path to save the model
    """
    logger = get_logger(__name__)
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving model to {output_path}")
    
    # We wrap the booster in a dict to store metadata if needed later,
    # or just save the booster directly. The task says save to model.pkl.
    # Standard practice is to save the booster or a dict containing it.
    # Let's save the booster directly as per common pickle usage in this context.
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
        
    logger.info("Model saved successfully.")

def main():
    """Main entry point for T026."""
    # Setup logging
    set_log_level(logging.INFO)
    logger = get_logger(__name__)
    
    logger.info("Starting T026: Train Final Model")
    
    try:
        # 1. Load Data
        X, y, feature_names = load_training_data()
        
        # 2. Train Model
        model = train_final_model(X, y, feature_names)
        
        # 3. Save Model
        output_path = "data/processed/model.pkl"
        save_model(model, output_path)
        
        logger.info(f"T026 completed successfully. Model saved to {output_path}")
        
    except Exception as e:
        logger.error(f"T026 failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
