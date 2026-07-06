"""
Modeling module for training Random Forest regressors on aluminum alloy data.

This module handles feature loading, model training with cross-validation,
evaluation, and serialization. It includes memory optimization to stay
within the 4GB peak memory target.
"""
import logging
import pickle
import json
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error
import gc

from config import get_config
from logging_config import get_logger
from memory_utils import (
    check_memory_usage,
    optimize_dataframe_memory,
    clear_unused_memory,
    get_memory_profile_summary
)

logger = get_logger(__name__)

def load_features_and_target(
    data_path: Path,
    feature_columns: list,
    target_column: str
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load features and target from a CSV file with memory optimization.
    
    Args:
        data_path: Path to the CSV file
        feature_columns: List of column names to use as features
        target_column: Name of the target column
        
    Returns:
        Tuple of (features DataFrame, target Series)
    """
    logger.info(f"Loading features and target from {data_path}")
    
    # Check memory before loading
    check_memory_usage(warn_only=True)
    
    # Load data
    df = pd.read_csv(data_path)
    
    # Optimize memory
    df = optimize_dataframe_memory(df)
    
    # Extract features and target
    X = df[feature_columns]
    y = df[target_column]
    
    logger.info(f"Loaded {len(X)} samples with {len(feature_columns)} features")
    
    # Check memory after loading
    check_memory_usage(warn_only=True)
    
    return X, y

def train_random_forest_with_cv(
    X: pd.DataFrame,
    y: pd.Series,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    n_splits: int = 5,
    random_state: int = 42
) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """
    Train a Random Forest regressor with k-fold cross-validation.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        n_estimators: Number of trees in the forest
        max_depth: Maximum depth of trees (None for unlimited)
        n_splits: Number of CV folds
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (trained model, metrics dictionary)
    """
    logger.info(f"Training Random Forest with {n_estimators} trees, {n_splits}-fold CV")
    
    # Check memory before training
    check_memory_usage(warn_only=True)
    
    # Initialize model
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        verbose=1
    )
    
    # Perform cross-validation
    logger.info("Starting cross-validation...")
    start_time = time.time()
    
    cv_scores = cross_val_score(
        model, X, y, 
        cv=n_splits, 
        scoring='neg_mean_absolute_error',
        n_jobs=-1
    )
    
    cv_time = time.time() - start_time
    cv_mae = -cv_scores.mean()
    cv_std = cv_scores.std()
    
    logger.info(f"CV completed in {cv_time:.2f}s. MAE: {cv_mae:.4f} (+/- {cv_std:.4f})")
    
    # Train final model on full data
    logger.info("Training final model on full dataset...")
    start_time = time.time()
    model.fit(X, y)
    train_time = time.time() - start_time
    
    logger.info(f"Training completed in {train_time:.2f}s")
    
    # Check memory after training
    check_memory_usage(warn_only=True)
    
    metrics = {
        "cv_mae": float(cv_mae),
        "cv_std": float(cv_std),
        "cv_scores": [float(score) for score in cv_scores],
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "train_time_seconds": float(train_time),
        "cv_time_seconds": float(cv_time),
        "n_samples": len(X),
        "n_features": X.shape[1]
    }
    
    return model, metrics

def evaluate_model_on_test(
    model: RandomForestRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, Any]:
    """
    Evaluate a trained model on a test set.
    
    Args:
        model: Trained Random Forest model
        X_test: Test features
        y_test: Test targets
        
    Returns:
        Dictionary with evaluation metrics
    """
    logger.info("Evaluating model on test set...")
    
    # Check memory
    check_memory_usage(warn_only=True)
    
    # Predict
    start_time = time.time()
    y_pred = model.predict(X_test)
    pred_time = time.time() - start_time
    
    # Calculate metrics
    mae = mean_absolute_error(y_test, y_pred)
    
    # Optional: R² score
    ss_res = ((y_test - y_pred) ** 2).sum()
    ss_tot = ((y_test - y_test.mean()) ** 2).sum()
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    logger.info(f"Test MAE: {mae:.4f}, R²: {r2:.4f}, Prediction time: {pred_time:.2f}s")
    
    metrics = {
        "test_mae": float(mae),
        "test_r2": float(r2),
        "n_test_samples": len(y_test),
        "prediction_time_seconds": float(pred_time)
    }
    
    return metrics

def run_modeling_pipeline(
    data_path: Path,
    model_path: Path,
    metrics_path: Path,
    feature_columns: list,
    target_column: str,
    test_size: float = 0.2,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run the complete modeling pipeline: load data, train model, evaluate, save.
    
    Args:
        data_path: Path to input CSV
        model_path: Path to save trained model
        metrics_path: Path to save metrics JSON
        feature_columns: List of feature column names
        target_column: Target column name
        test_size: Proportion of data for test set
        n_estimators: Number of trees
        max_depth: Max tree depth
        n_splits: Number of CV folds
        random_state: Random seed
        
    Returns:
        Combined metrics dictionary
    """
    logger.info("Starting modeling pipeline")
    start_time = time.time()
    
    # Load data
    X, y = load_features_and_target(data_path, feature_columns, target_column)
    
    # Split data
    logger.info(f"Splitting data (test_size={test_size})")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Train model
    model, cv_metrics = train_random_forest_with_cv(
        X_train, y_train,
        n_estimators=n_estimators,
        max_depth=max_depth,
        n_splits=n_splits,
        random_state=random_state
    )
    
    # Evaluate model
    test_metrics = evaluate_model_on_test(model, X_test, y_test)
    
    # Save model
    logger.info(f"Saving model to {model_path}")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Combine metrics
    all_metrics = {
        **cv_metrics,
        **test_metrics,
        "total_pipeline_time_seconds": time.time() - start_time,
        "feature_columns": feature_columns,
        "target_column": target_column,
        "test_size": test_size,
        "random_state": random_state
    }
    
    # Save metrics
    logger.info(f"Saving metrics to {metrics_path}")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    # Clear memory
    clear_unused_memory()
    
    # Final memory check
    profile = get_memory_profile_summary()
    logger.info(f"Final memory profile: {profile['peak_gb']:.2f}GB peak ({profile['peak_usage_pct']:.1f}% of limit)")
    
    if not profile['within_limit']:
        logger.warning("Pipeline exceeded memory limit!")
    else:
        logger.info("Pipeline completed within memory limits")
    
    return all_metrics

def evaluate_model_model_on_test(
    model_path: Path,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, Any]:
    """
    Load a saved model and evaluate it on a test set.
    
    Args:
        model_path: Path to saved model
        X_test: Test features
        y_test: Test targets
        
    Returns:
        Evaluation metrics dictionary
    """
    logger.info(f"Loading model from {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    return evaluate_model_on_test(model, X_test, y_test)

def main():
    """
    Main entry point for the modeling pipeline.
    """
    config = get_config()
    setup_logging(config)
    
    # Get paths from config
    data_path = Path(config.data_dir) / "processed" / "filtered_alloys.csv"
    model_path = Path(config.models_dir) / "rf_model.pkl"
    metrics_path = Path(config.docs_dir) / "outputs" / "model_metrics.json"
    
    # Define features and target
    # These should match the ILR-transformed features from data_cleaning.py
    feature_columns = [
        'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4',  # ILR transformed compositions
        'youngs_modulus_gpa',  # Additional feature if needed
        'bulk_modulus_gpa'     # Additional feature if needed
    ]
    target_column = 'poissons_ratio'
    
    # Run pipeline
    try:
        metrics = run_modeling_pipeline(
            data_path=data_path,
            model_path=model_path,
            metrics_path=metrics_path,
            feature_columns=feature_columns,
            target_column=target_column,
            n_estimators=100,
            n_splits=5,
            random_state=42
        )
        
        logger.info("Modeling pipeline completed successfully")
        logger.info(f"Test MAE: {metrics['test_mae']:.4f}")
        
    except MemoryError as e:
        logger.error(f"Pipeline failed due to memory error: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
