"""
Machine Learning Model Training Module.

Implements training for Random Forest, Gradient Boosting, and Ridge Regression
models with Grid Search hyperparameter tuning.
"""
import os
import sys
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Import project configuration and utilities
# Assuming config.py is in the parent code directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATA_PROCESSED, DATA_MODELS, RANDOM_SEED

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_training_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the preprocessed training dataset.
    Expects 'data/processed/train.csv' to exist (output of T017).
    
    Returns:
        Tuple of (features_df, target_series)
    """
    train_path = Path(DATA_PROCESSED) / "train.csv"
    if not train_path.exists():
        raise FileNotFoundError(f"Training data not found at {train_path}. "
                                "Please ensure T017 (Stratified Split) has been completed.")
    
    df = pd.read_csv(train_path)
    
    # Define target and feature columns based on data-model.md and entities
    # Target: yield_strength_mpa
    # Features: encoded elemental fractions, strain_rate, grain_size, etc.
    # Assuming 'encoded_features.csv' from T016 contains the feature matrix
    # We need to merge or ensure the train.csv has these features.
    # Based on T017 description, train.csv should contain the split data.
    # We assume T016 added the encoded features to the dataset before splitting.
    
    target_col = 'yield_strength_mpa'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in training data.")
    
    # Identify feature columns (exclude target and metadata like 'alloy_family' if not encoded)
    # We assume numeric encoded columns are features.
    feature_cols = [col for col in df.columns if col != target_col and col != 'alloy_family']
    # If 'alloy_family' is present, we might need to one-hot encode it or drop it if already handled.
    # For this implementation, we assume T016 handled all feature encoding.
    # Let's filter for numeric columns to be safe, or specific known feature columns.
    # A robust approach: use all numeric columns except target.
    feature_cols = df.select_dtypes(include=[np.number]).columns.drop(target_col).tolist()
    
    if not feature_cols:
        raise ValueError("No feature columns found in training data.")
    
    X = df[feature_cols]
    y = df[target_col]
    
    logger.info(f"Loaded training data: {X.shape[0]} samples, {X.shape[1]} features.")
    return X, y

def train_random_forest(X: pd.DataFrame, y: pd.Series) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a Random Forest Regressor with Grid Search.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        
    Returns:
        Tuple of (trained_model, metrics_dict)
    """
    logger.info("Training Random Forest Model...")
    
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [10, 20, None],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }
    
    base_model = RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1)
    
    # Use a subset of data for grid search if dataset is large to save time,
    # or full CV. Here we use full CV as per standard practice for this scope.
    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=5,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Evaluate on the training set (or use cross-val score if preferred, 
    # but task asks for model training and saving, metrics usually on test or CV)
    # Since we don't have a separate test split here (it's in train.csv),
    # we'll calculate metrics on the data used for training to show fit,
    # but note that for real evaluation, we should use the test set from T017.
    # However, T017 split the data. The 'train.csv' is the training set.
    # We should ideally evaluate on a held-out set, but for this task,
    # we will report the CV score from GridSearchCV and train on the full X.
    
    metrics = {
        'best_params': best_params,
        'cv_r2_mean': grid_search.best_score_,
        'model_type': 'RandomForest'
    }
    
    logger.info(f"Random Forest trained. Best CV R²: {metrics['cv_r2_mean']:.4f}")
    logger.info(f"Best parameters: {best_params}")
    
    return best_model, metrics

def train_gradient_boosting(X: pd.DataFrame, y: pd.Series) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a Gradient Boosting Regressor with Grid Search.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        
    Returns:
        Tuple of (trained_model, metrics_dict)
    """
    logger.info("Training Gradient Boosting Model...")
    
    param_grid = {
        'n_estimators': [100, 200],
        'learning_rate': [0.05, 0.1],
        'max_depth': [3, 5],
        'min_samples_split': [2, 5]
    }
    
    base_model = GradientBoostingRegressor(random_state=RANDOM_SEED)
    
    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=5,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    metrics = {
        'best_params': best_params,
        'cv_r2_mean': grid_search.best_score_,
        'model_type': 'GradientBoosting'
    }
    
    logger.info(f"Gradient Boosting trained. Best CV R²: {metrics['cv_r2_mean']:.4f}")
    logger.info(f"Best parameters: {best_params}")
    
    return best_model, metrics

def train_ridge(X: pd.DataFrame, y: pd.Series) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a Ridge Regression model with Grid Search.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        
    Returns:
        Tuple of (trained_model, metrics_dict)
    """
    logger.info("Training Ridge Regression Model...")
    
    param_grid = {
        'alpha': [0.1, 1.0, 10.0, 100.0]
    }
    
    base_model = Ridge(random_state=RANDOM_SEED)
    
    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=5,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    metrics = {
        'best_params': best_params,
        'cv_r2_mean': grid_search.best_score_,
        'model_type': 'Ridge'
    }
    
    logger.info(f"Ridge Regression trained. Best CV R²: {metrics['cv_r2_mean']:.4f}")
    logger.info(f"Best parameters: {best_params}")
    
    return best_model, metrics

def save_model(model: Any, model_name: str, metrics: Dict[str, Any]) -> str:
    """
    Save the trained model and its metrics to disk.
    
    Args:
        model: The trained sklearn model.
        model_name: Name of the model (e.g., 'ml_rf', 'ml_gb').
        metrics: Dictionary of metrics and parameters.
        
    Returns:
        Path to the saved model file.
    """
    output_dir = Path(DATA_MODELS)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = output_dir / f"{model_name}.pkl"
    metrics_path = output_dir / f"{model_name}_metrics.json"
    
    with open(model_path, 'wb') as f:
        pickle.dump({'model': model, 'metrics': metrics}, f)
    
    # Save metrics as JSON if possible (convert non-serializable items)
    import json
    serializable_metrics = {}
    for k, v in metrics.items():
        if isinstance(v, (int, float, str, bool, type(None))):
            serializable_metrics[k] = v
        elif isinstance(v, dict):
            serializable_metrics[k] = v
        else:
            serializable_metrics[k] = str(v)
    
    with open(metrics_path, 'w') as f:
        json.dump(serializable_metrics, f, indent=2)
        
    logger.info(f"Saved {model_name} model to {model_path}")
    return str(model_path)

def main():
    """
    Main entry point for training ML models.
    """
    try:
        X, y = load_training_data()
        
        # Train models
        rf_model, rf_metrics = train_random_forest(X, y)
        save_model(rf_model, 'ml_rf', rf_metrics)
        
        gb_model, gb_metrics = train_gradient_boosting(X, y)
        save_model(gb_model, 'ml_gb', gb_metrics)
        
        ridge_model, ridge_metrics = train_ridge(X, y)
        save_model(ridge_model, 'ml_ridge', ridge_metrics)
        
        logger.info("All ML models trained and saved successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data loading error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()