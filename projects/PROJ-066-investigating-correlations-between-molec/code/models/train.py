"""
Model training pipeline for molecular descriptor analysis.
Implements data splitting, model training, and feature importance generation.
"""
import os
import sys
import pickle
import logging
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error

# Import project utilities
from utils.logging import get_logger, log_pipeline_step, log_resource_usage
from utils.config import RANDOM_SEED, MAX_MEMORY_GB
from utils.update_state import compute_file_hash, update_state

logger = get_logger(__name__)

def load_processed_data(filepath: str) -> pd.DataFrame:
    """
    Load the processed molecules dataset.
    
    Args:
        filepath: Path to the processed CSV file.
        
    Returns:
        DataFrame containing molecular descriptors and target values.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    
    logger.info(f"Loading processed data from {filepath}")
    df = pd.read_csv(filepath)
    
    required_columns = ['SMILES', 'experimental_value'] + [
        'TPSA', 'logP', 'MW', 'rotatable_bonds', 
        'h_bond_donors', 'h_bond_acceptors', 'ring_count'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in processed data: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} molecules with {len(df.columns)} columns")
    return df

def split_data(
    df: pd.DataFrame,
    target_column: str = 'experimental_value',
    test_size: float = 0.2,
    stratify: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified train/test split on the processed dataset.
    
    Stratification is performed on the target variable (experimental_value)
    by binning the continuous values into quantiles to ensure distribution
    similarity between train and test sets.
    
    Args:
        df: The full processed DataFrame.
        target_column: Name of the column to use for the target variable.
        test_size: Proportion of the dataset to include in the test split (default 0.2).
        stratify: If True, perform stratified splitting based on target quantiles.
        
    Returns:
        Tuple containing (X_train, X_test, y_train, y_test) as DataFrames/Series.
    """
    log_pipeline_step(logger, "split_data", "Starting stratified data split")
    
    # Ensure random seed is used
    seed = RANDOM_SEED
    logger.info(f"Using random seed: {seed}")
    
    # Separate features (X) and target (y)
    feature_columns = [col for col in df.columns if col not in ['SMILES', target_column]]
    X = df[feature_columns]
    y = df[target_column]
    
    logger.info(f"Features: {feature_columns}")
    logger.info(f"Target: {target_column}")
    logger.info(f"Total samples: {len(df)}")
    
    if stratify:
        # For continuous targets, stratify by binning into quantiles
        # This ensures the distribution of experimental values is similar in train/test
        n_bins = 10
        try:
            # Create bins based on quantiles of the target variable
            y_binned = pd.qcut(y, q=n_bins, labels=False, duplicates='drop')
            logger.info(f"Stratifying by {n_bins} quantile bins of target variable")
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=seed, stratify=y_binned
            )
        except ValueError as e:
            # Fallback if not enough unique values for stratification
            logger.warning(f"Stratification failed ({e}), falling back to random split")
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=seed
            )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=seed
        )
    
    logger.info(f"Train set size: {len(X_train)} ({len(X_train)/len(df)*100:.1f}%)")
    logger.info(f"Test set size: {len(X_test)} ({len(X_test)/len(df)*100:.1f}%)")
    
    # Log resource usage after split
    log_resource_usage(logger, "data_split")
    
    return X_train, X_test, y_train, y_test

def train_linear_regression(X_train: pd.DataFrame, y_train: pd.Series) -> LinearRegression:
    """
    Train a Linear Regression model on the training data.
    
    Args:
        X_train: Training features DataFrame.
        y_train: Training target Series.
        
    Returns:
        Fitted LinearRegression model.
    """
    log_pipeline_step(logger, "train_linear_regression", "Training Linear Regression model")
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    logger.info(f"Linear Regression model trained. Coefficients: {len(model.coef_)} features")
    return model

def train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    max_depth: int = 10,
    n_estimators: int = 100
) -> RandomForestRegressor:
    """
    Train a Random Forest model on the training data.
    
    Uses memory-conscious parameters for CPU runner constraints.
    
    Args:
        X_train: Training features DataFrame.
        y_train: Training target Series.
        max_depth: Maximum depth of the tree (default 10).
        n_estimators: Number of trees in the forest (default 100).
        
    Returns:
        Fitted RandomForestRegressor model.
    """
    log_pipeline_step(logger, "train_random_forest", "Training Random Forest model")
    
    # Log memory constraints
    logger.info(f"Training with max_depth={max_depth}, n_estimators={n_estimators}")
    logger.info(f"Max memory constraint: {MAX_MEMORY_GB} GB")
    
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=RANDOM_SEED,
        n_jobs=-1,  # Use all available cores
        verbose=0
    )
    
    model.fit(X_train, y_train)
    
    logger.info(f"Random Forest model trained. Trees: {n_estimators}, Depth: {max_depth}")
    
    # Log resource usage after training
    log_resource_usage(logger, "rf_training")
    
    return model

def generate_feature_importance(model: RandomForestRegressor, feature_names: list) -> Dict[str, Any]:
    """
    Extract and rank feature importances from the Random Forest model.
    
    Args:
        model: Fitted RandomForestRegressor.
        feature_names: List of feature column names.
        
    Returns:
        Dictionary containing ranked feature importances.
    """
    log_pipeline_step(logger, "generate_feature_importance", "Generating feature importance report")
    
    importances = model.feature_importances_
    
    # Create a DataFrame for sorting
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    # Convert to list of dictionaries
    importance_list = importance_df.to_dict(orient='records')
    
    result = {
        'model_type': 'Random Forest',
        'feature_count': len(feature_names),
        'importances': importance_list
    }
    
    logger.info(f"Feature importance generated. Top feature: {importance_list[0]['feature']}")
    return result

def save_model(model: Any, filepath: str) -> str:
    """
    Save a trained model to a pickle file.
    
    Args:
        model: The trained model object.
        filepath: Path to save the model.
        
    Returns:
        Path to the saved model file.
    """
    if not os.path.exists(os.dirname(filepath)):
        os.makedirs(os.dirname(filepath))
    
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Model saved to {filepath}")
    return filepath

def main():
    """
    Main entry point for the training pipeline.
    Loads processed data, splits it, and trains models.
    """
    log_pipeline_step(logger, "main", "Starting model training pipeline")
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    processed_data_path = project_root / "data" / "processed" / "molecules_processed.csv"
    lr_model_path = project_root / "data" / "processed" / "model_lr.pkl"
    rf_model_path = project_root / "data" / "processed" / "model_rf.pkl"
    importance_path = project_root / "data" / "processed" / "feature_importance.json"
    
    try:
        # Load data
        df = load_processed_data(str(processed_data_path))
        
        # Split data
        X_train, X_test, y_train, y_test = split_data(df)
        
        # Train models
        lr_model = train_linear_regression(X_train, y_train)
        rf_model = train_random_forest(X_train, y_train)
        
        # Save models
        save_model(lr_model, str(lr_model_path))
        save_model(rf_model, str(rf_model_path))
        
        # Generate and save feature importance
        feature_names = list(X_train.columns)
        importance_result = generate_feature_importance(rf_model, feature_names)
        
        with open(importance_path, 'w') as f:
            json.dump(importance_result, f, indent=2)
        
        logger.info("Training pipeline completed successfully")
        
        # Update state with new artifacts
        artifacts = [
            str(lr_model_path),
            str(rf_model_path),
            str(importance_path)
        ]
        update_state(artifacts, project_root / "state" / "projects" / "PROJ-066-investigating-correlations-between-molec.yaml")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
