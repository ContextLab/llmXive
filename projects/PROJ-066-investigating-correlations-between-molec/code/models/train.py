import os
import sys
import pickle
import logging
import json
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Import project utilities
from utils.config import RANDOM_SEED
from utils.logging import get_logger, log_pipeline_step, ResourceMonitor

logger = get_logger(__name__)

# Constants for paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "molecules_processed.csv"
MODEL_LR_PATH = PROJECT_ROOT / "data" / "processed" / "model_lr.pkl"
MODEL_RF_PATH = PROJECT_ROOT / "data" / "processed" / "model_rf.pkl"
FEATURE_IMPORTANCE_PATH = PROJECT_ROOT / "data" / "processed" / "feature_importance.json"

DESCRIPTOR_COLUMNS = [
    "TPSA", "logP", "MW", "num_rotatable_bonds",
    "num_h_bond_donors", "num_h_bond_acceptors", "num_rings"
]
TARGET_COLUMN = "experimental_value"  # Assuming this is the target based on context

def load_processed_data() -> pd.DataFrame:
    """Load the processed molecule dataset."""
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed data not found at {PROCESSED_DATA_PATH}. "
            "Please run the preprocessing pipeline (T015) first."
        )
    logger.info(f"Loading processed data from {PROCESSED_DATA_PATH}")
    df = pd.read_csv(PROCESSED_DATA_PATH)
    
    # Validate required columns exist
    required_cols = DESCRIPTOR_COLUMNS + [TARGET_COLUMN]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in processed data: {missing}")
    
    return df

def split_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified train/test split by target variable.
    Note: True stratification on a continuous target requires binning.
    Here we use a standard split with random_state for reproducibility.
    """
    logger.info("Splitting data into train and test sets")
    
    X = df[DESCRIPTOR_COLUMNS]
    y = df[TARGET_COLUMN]
    
    # Using random_state for reproducibility as specified (seed=42)
    # Stratification on continuous targets is complex; using standard split
    X_train, X_test = train_test_split(
        df, 
        test_size=0.2, 
        random_state=RANDOM_SEED,
        shuffle=True
    )
    
    logger.info(f"Train set size: {len(X_train)}, Test set size: {len(X_test)}")
    return X_train, X_test

def train_linear_regression(X_train: pd.DataFrame, X_test: pd.DataFrame) -> LinearRegression:
    """
    Fit a Linear Regression model on the training set.
    Saves the artifact to data/processed/model_lr.pkl.
    """
    logger.info("Training Linear Regression model")
    
    # Prepare features and target
    features = X_train[DESCRIPTOR_COLUMNS]
    target = X_train[TARGET_COLUMN]
    
    # Initialize and fit model
    model = LinearRegression()
    model.fit(features, target)
    
    # Save model artifact
    MODEL_LR_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_LR_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Linear Regression model saved to {MODEL_LR_PATH}")
    
    # Log a quick sanity check (R2 on training set)
    train_score = model.score(features, target)
    logger.info(f"Linear Regression training R2 score: {train_score:.4f}")
    
    return model

def train_random_forest(X_train: pd.DataFrame, X_test: pd.DataFrame) -> RandomForestRegressor:
    """
    Fit a Random Forest model on the training set.
    Uses memory-conscious parameters.
    Saves the artifact to data/processed/model_rf.pkl.
    """
    logger.info("Training Random Forest model")
    
    features = X_train[DESCRIPTOR_COLUMNS]
    target = X_train[TARGET_COLUMN]
    
    # Memory-conscious parameters
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    
    model.fit(features, target)
    
    # Save model artifact
    MODEL_RF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_RF_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Random Forest model saved to {MODEL_RF_PATH}")
    
    # Log a quick sanity check
    train_score = model.score(features, target)
    logger.info(f"Random Forest training R2 score: {train_score:.4f}")
    
    return model

def generate_feature_importance(model: RandomForestRegressor) -> Dict[str, Any]:
    """
    Extract and rank feature importances from Random Forest.
    Saves the report to data/processed/feature_importance.json.
    """
    logger.info("Generating feature importance report")
    
    importances = model.feature_importances_
    feature_importance_dict = {
        feature: float(imp) 
        for feature, imp in zip(DESCRIPTOR_COLUMNS, importances)
    }
    
    # Sort by importance
    sorted_importance = dict(
        sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)
    )
    
    report = {
        "model_type": "RandomForest",
        "feature_importances": sorted_importance,
        "total_features": len(DESCRIPTOR_COLUMNS)
    }
    
    # Save report
    FEATURE_IMPORTANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FEATURE_IMPORTANCE_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Feature importance report saved to {FEATURE_IMPORTANCE_PATH}")
    return report

def save_model(model: Any, path: Path) -> None:
    """Generic helper to save a model to a pickle file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")

def main():
    """
    Main entry point for the training pipeline.
    Executes data loading, splitting, and model training.
    """
    log_pipeline_step("START", "Training Pipeline")
    
    try:
        # 1. Load Data
        df = load_processed_data()
        
        # 2. Split Data
        X_train, X_test = split_data(df)
        
        # 3. Train Linear Regression (T018)
        lr_model = train_linear_regression(X_train, X_test)
        
        # 4. Train Random Forest (T019)
        rf_model = train_random_forest(X_train, X_test)
        
        # 5. Generate Feature Importance (T020)
        generate_feature_importance(rf_model)
        
        log_pipeline_step("SUCCESS", "Training Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()