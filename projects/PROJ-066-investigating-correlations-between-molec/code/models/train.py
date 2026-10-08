"""
Model Training Pipeline for Molecular Descriptor Analysis.

This module handles data splitting, model training (Linear Regression, Random Forest),
and feature importance generation.
"""

import os
import sys
import pickle
import logging
import json
from pathlib import Path
from typing import Tuple, Dict, Any

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib

# Project-relative imports
try:
    from utils.config import RANDOM_SEED, MAX_MEMORY_GB
    from utils.logging import get_logger, log_pipeline_step, log_resource_usage
    from utils.update_state import update_state, compute_file_hash
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.config import RANDOM_SEED, MAX_MEMORY_GB
    from utils.logging import get_logger, log_pipeline_step, log_resource_usage
    from utils.update_state import update_state, compute_file_hash

logger = get_logger(__name__)

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "molecules_processed.csv"
MODEL_LR_PATH = PROJECT_ROOT / "data" / "processed" / "model_lr.pkl"
MODEL_RF_PATH = PROJECT_ROOT / "data" / "processed" / "model_rf.pkl"
FEATURE_IMPORTANCE_PATH = PROJECT_ROOT / "data" / "processed" / "feature_importance.json"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-066-investigating-correlations-between-molec.yaml"

# Target column name (assumed to be 'Experimental_Value' or similar based on schema)
TARGET_COLUMN = "Experimental_Value"
DESCRIPTOR_COLUMNS = [
    "TPSA", "logP", "MW", "NumRotatableBonds", 
    "NumHDonors", "NumHAcceptors", "RingCount"
]

# --- Helper Functions ---

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load the processed CSV data."""
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    logger.info(f"Loading processed data from {data_path}")
    return pd.read_csv(data_path)

def split_data(df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Perform stratified train/test split.
    
    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        
    Returns:
        X_train, X_test, y_train, y_test
    """
    logger.info("Splitting data...")
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    X = df[DESCRIPTOR_COLUMNS]
    y = df[target_col]
    
    # Stratified split requires categorical target, but for regression we often just use random split
    # unless we bin the target. For this task, we use random split with seed for reproducibility.
    # If 'Target' (category) exists, we can stratify by that.
    strat_col = "Target" if "Target" in df.columns else None
    
    if strat_col:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=df[strat_col]
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=RANDOM_SEED
        )
    
    logger.info(f"Data split complete. Train: {len(X_train)}, Test: {len(X_test)}")
    return X_train, X_test, y_train, y_test

def train_linear_regression(X_train: pd.DataFrame, y_train: pd.Series) -> LinearRegression:
    """
    Train a Linear Regression model.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        
    Returns:
        Trained model.
    """
    logger.info("Training Linear Regression model...")
    model = LinearRegression()
    model.fit(X_train, y_train)
    logger.info("Linear Regression training complete.")
    return model

def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestRegressor:
    """
    Train a Random Forest model with memory-conscious parameters.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        
    Returns:
        Trained model.
    """
    logger.info("Training Random Forest model...")
    
    # Memory-conscious parameters
    n_estimators = 100
    max_depth = 10
    
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=RANDOM_SEED,
        n_jobs=-1 # Use all available cores
    )
    
    model.fit(X_train, y_train)
    logger.info(f"Random Forest training complete (n_estimators={n_estimators}, max_depth={max_depth}).")
    return model

def generate_feature_importance(model: RandomForestRegressor, feature_names: list) -> Dict[str, Any]:
    """
    Extract and format feature importances.
    
    Args:
        model: Trained Random Forest model.
        feature_names: List of feature names.
        
    Returns:
        Dictionary mapping feature names to importance scores.
    """
    logger.info("Generating feature importance report...")
    
    importances = model.feature_importances_
    importance_dict = {name: float(imp) for name, imp in zip(feature_names, importances)}
    
    # Sort by importance
    sorted_importance = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
    
    logger.info("Feature importance report generated.")
    return sorted_importance

def save_model(model, model_path: Path) -> None:
    """Save a model to disk using joblib."""
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")

def main():
    """
    Main entry point for the training pipeline.
    """
    logger.info("Starting Model Training Pipeline (T036 Refactor)")
    
    # 1. Load Data
    df = load_processed_data(PROCESSED_DATA_PATH)
    
    # 2. Split Data
    X_train, X_test, y_train, y_test = split_data(df, TARGET_COLUMN)
    
    # 3. Train Linear Regression
    lr_model = train_linear_regression(X_train, y_train)
    save_model(lr_model, MODEL_LR_PATH)
    
    # 4. Train Random Forest
    rf_model = train_random_forest(X_train, y_train)
    save_model(rf_model, MODEL_RF_PATH)
    
    # 5. Generate Feature Importance
    importance_report = generate_feature_importance(rf_model, DESCRIPTOR_COLUMNS)
    
    # Save Feature Importance
    FEATURE_IMPORTANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FEATURE_IMPORTANCE_PATH, 'w') as f:
        json.dump(importance_report, f, indent=2)
    logger.info(f"Feature importance saved to {FEATURE_IMPORTANCE_PATH}")
    
    # Update State for artifacts
    update_state(artifact_path=str(MODEL_LR_PATH), state_file_path=str(STATE_FILE_PATH), artifact_type="model")
    update_state(artifact_path=str(MODEL_RF_PATH), state_file_path=str(STATE_FILE_PATH), artifact_type="model")
    update_state(artifact_path=str(FEATURE_IMPORTANCE_PATH), state_file_path=str(STATE_FILE_PATH), artifact_type="report")
    
    logger.info("Model Training Pipeline completed successfully.")

if __name__ == "__main__":
    main()