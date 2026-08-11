"""Modeling module for training and evaluating Random Forest models."""
import logging
import pickle
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error
from config import get_config
from logging_config import setup_logging, get_logger

# Initialize logger
logger = setup_logging()
if logger is None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def load_features_and_target(data_path: Optional[Path] = None):
    """
    Load features (ILR-transformed) and target (Poisson's ratio) from cleaned data.
    
    Args:
        data_path: Path to the cleaned parquet file
        
    Returns:
        Tuple of (X, y) where X is the feature matrix and y is the target
    """
    config = get_config()
    
    if data_path is None:
        data_path = config.data_processed_dir / "alloys_clean.parquet"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}. Run cleaning pipeline first.")
    
    df = pd.read_parquet(data_path)
    
    # ILR feature columns
    ilr_features = ['ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']
    
    # Check if required columns exist
    if not all(col in df.columns for col in ilr_features):
        raise ValueError(f"ILR features not found in data. Columns: {df.columns.tolist()}")
    
    if 'poisson_ratio' not in df.columns:
        raise ValueError("poisson_ratio column not found in data")
    
    X = df[ilr_features]
    y = df['poisson_ratio']
    
    logger.info(f"Loaded {len(X)} samples with {len(ilr_features)} features")
    
    return X, y

def train_random_forest_with_cv(X: pd.DataFrame, y: pd.Series, n_estimators: int = 100, 
                                max_depth: Optional[int] = None, random_state: int = 42, 
                                n_folds: int = 5) -> Tuple[Any, Dict[str, float]]:
    """
    Train Random Forest with k-fold cross-validation.
    
    Args:
        X: Feature matrix
        y: Target vector
        n_estimators: Number of trees in the forest
        max_depth: Maximum depth of trees
        random_state: Random seed
        n_folds: Number of CV folds
        
    Returns:
        Tuple of (trained_model, cv_metrics)
    """
    logger.info(f"Training Random Forest with {n_estimators} estimators...")
    
    # Initialize model
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1
    )
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=n_folds, scoring='neg_mean_absolute_error')
    cv_mae = -np.mean(cv_scores)
    cv_std = np.std(cv_scores)
    
    logger.info(f"CV MAE: {cv_mae:.4f} (+/- {cv_std:.4f})")
    
    # Train on full data
    model.fit(X, y)
    
    cv_metrics = {
        'cv_mae': float(cv_mae),
        'cv_std': float(cv_std),
        'n_folds': n_folds
    }
    
    return model, cv_metrics

def evaluate_model_on_test(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """
    Evaluate model on test set.
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test targets
        
    Returns:
        Dictionary of evaluation metrics
    """
    y_pred = model.predict(X_test)
    test_mae = mean_absolute_error(y_test, y_pred)
    
    logger.info(f"Test MAE: {test_mae:.4f}")
    
    return {
        'test_mae': float(test_mae),
        'test_size': len(y_test)
    }

def save_model(model: Any, model_path: Optional[Path] = None):
    """
    Save trained model to disk.
    
    Args:
        model: Trained model
        model_path: Path to save model
    """
    config = get_config()
    
    if model_path is None:
        model_path = config.models_dir / "rf_model.pkl"
    
    # Ensure directory exists
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f, protocol=3)
    
    logger.info(f"Model saved to {model_path}")

def save_model_metrics(cv_metrics: Dict[str, float], test_metrics: Dict[str, float], 
                      mae_flag: bool, output_path: Optional[Path] = None):
    """
    Save model metrics to JSON.
    
    Args:
        cv_metrics: Cross-validation metrics
        test_metrics: Test set metrics
        mae_flag: Whether CV MAE exceeds threshold
        output_path: Path to save metrics
    """
    config = get_config()
    
    if output_path is None:
        output_path = config.data_processed_dir / "model_metrics.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    metrics = {
        'cv_mae': cv_metrics['cv_mae'],
        'cv_std': cv_metrics['cv_std'],
        'test_mae': test_metrics['test_mae'],
        'test_size': test_metrics['test_size'],
        'mae_flag': mae_flag
    }
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Model metrics saved to {output_path}")

def run_modeling_pipeline(data_path: Optional[Path] = None, 
                         model_path: Optional[Path] = None,
                         metrics_path: Optional[Path] = None):
    """
    Run the full modeling pipeline.
    
    Steps:
    1. Load features and target
    2. Train/test split
    3. Train Random Forest with CV
    4. Evaluate on test set
    5. Check MAE threshold
    6. Save model and metrics
    
    Args:
        data_path: Path to cleaned data
        model_path: Path to save model
        metrics_path: Path to save metrics
    """
    config = get_config()
    
    if data_path is None:
        data_path = config.data_processed_dir / "alloys_clean.parquet"
    
    if model_path is None:
        model_path = config.models_dir / "rf_model.pkl"
    
    if metrics_path is None:
        metrics_path = config.data_processed_dir / "model_metrics.json"
    
    logger.info("Starting modeling pipeline")
    
    # Load data
    X, y = load_features_and_target(data_path)
    
    # Train/test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=config.random_seed
    )
    
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Train model with CV
    model, cv_metrics = train_random_forest_with_cv(X_train, y_train)
    
    # Evaluate on test set
    test_metrics = evaluate_model_on_test(model, X_test, y_test)
    
    # Check MAE threshold
    mae_flag = cv_metrics['cv_mae'] > config.mae_threshold
    if mae_flag:
        logger.warning(f"Methodological Concern: CV MAE ({cv_metrics['cv_mae']:.4f}) exceeds threshold ({config.mae_threshold})")
    
    # Save model
    save_model(model, model_path)
    
    # Save metrics
    save_model_metrics(cv_metrics, test_metrics, mae_flag, metrics_path)
    
    logger.info("Modeling pipeline completed successfully")
    
    return {
        'model': model,
        'cv_metrics': cv_metrics,
        'test_metrics': test_metrics,
        'mae_flag': mae_flag
    }

def main():
    """Main entry point for modeling."""
    logger.info("Starting modeling pipeline")
    
    try:
        results = run_modeling_pipeline()
        logger.info("Modeling pipeline completed successfully")
        return results
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()