"""
Final model training script for T026.
Trains a LightGBM model on the full training set and saves it to data/processed/model.pkl.
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
from sklearn.model_selection import train_test_split

# Project imports
from utils.config import load_hyperparameters, get_config_summary
from utils.logging_config import get_logger, set_log_level
from models.train_lightgbm import load_data_from_splits

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
CONFIG_PATH = ROOT_DIR / "code" / "config.yaml"

# Ensure output directory exists
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = DATA_PROCESSED_DIR / "model.pkl"

logger = get_logger(__name__)

def load_training_data():
    """
    Loads the preprocessed data from splits.
    Assumes T022 has already generated the split files.
    Returns X_train, y_train, X_test, y_test, feature_names.
    """
    try:
        splits = load_data_from_splits()
        # load_data_from_splits returns a dict with 'X_train', 'y_train', 'X_test', 'y_test', 'feature_names'
        if not splits:
            raise FileNotFoundError("Split data files not found. Ensure T022 has run.")
        
        X_train = splits['X_train']
        y_train = splits['y_train']
        X_test = splits['X_test']
        y_test = splits['y_test']
        feature_names = splits.get('feature_names', None)
        
        logger.info(f"Loaded training data: {X_train.shape}, {y_train.shape}")
        logger.info(f"Loaded test data: {X_test.shape}, {y_test.shape}")
        
        return X_train, y_train, X_test, y_test, feature_names
    except Exception as e:
        logger.error(f"Failed to load training data: {e}")
        raise

def train_final_model(X_train, y_train, params):
    """
    Trains the final LightGBM model on the full training set.
    """
    logger.info("Starting final model training on full training set...")
    
    # Create dataset
    train_data = lgb.Dataset(X_train, label=y_train)
    
    # Train model
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000, # Default rounds, can be tuned or early stopped
        verbose_eval=False
    )
    
    logger.info("Final model training completed.")
    return model

def save_model(model, path):
    """
    Saves the trained model to disk using pickle.
    """
    try:
        with open(path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved successfully to {path}")
    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        raise

def main():
    """
    Main entry point for T026.
    1. Load training data (from T022 splits).
    2. Load hyperparameters (from T025 config).
    3. Train final model.
    4. Save model to data/processed/model.pkl.
    """
    set_log_level(logging.INFO)
    
    logger.info("=== Starting Final Model Training (T026) ===")
    
    # 1. Load Data
    X_train, y_train, X_test, y_test, feature_names = load_training_data()
    
    # 2. Load Config
    # We expect the best params to be in config.yaml from T025
    params = load_hyperparameters(CONFIG_PATH)
    
    # Ensure we have the necessary LightGBM params
    if 'objective' not in params:
        params['objective'] = 'regression'
    if 'metric' not in params:
        params['metric'] = 'rmse'
    if 'boosting_type' not in params:
        params['boosting_type'] = 'gbdt'
        
    logger.info(f"Using hyperparameters: {params}")
    
    # 3. Train Final Model
    # Note: We train on the FULL training set (X_train, y_train) as per T026 spec.
    # We do not use early stopping here because we don't have a validation set 
    # separate from the training set for this specific step (T024 handled CV).
    # However, if X_train was created by splitting the full data, we just train on that.
    final_model = train_final_model(X_train, y_train, params)
    
    # 4. Save Model
    save_model(final_model, MODEL_PATH)
    
    logger.info("=== T026 Completed Successfully ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())