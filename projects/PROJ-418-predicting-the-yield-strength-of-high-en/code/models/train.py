import os
import sys
import json
import time
import traceback
from typing import Dict, Any, Tuple, Optional, List

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Import from project utilities
from utils.logging import get_logger, set_seeds, get_seed
from utils.config import get_config

logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load the processed descriptor dataset."""
    path = "data/processed/hea_descriptors.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found at {path}. Run pipeline first.")
    logger.info(f"Loading processed data from {path}")
    return pd.read_csv(path)

def prepare_features_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Separate features and target. Target is 'yield_strength_mpa'."""
    target_col = "yield_strength_mpa"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
    
    # Descriptors are all numeric columns except target and ID columns if any
    exclude_cols = [target_col]
    # Check for common ID columns to exclude
    if 'composition' in df.columns:
        exclude_cols.append('composition')
    
    feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in [np.float64, np.float32, np.int64, np.int32]]
    
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y, feature_cols

def create_stratified_split(X: np.ndarray, y: np.ndarray, feature_names: List[str], test_size=0.2, random_state=42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a strictly held-out test set using Stratified by Elemental Ratios.
    Since y is continuous, we bin y or a composite of features to create strata.
    As per Plan: Compute elemental ratios (or use target proxy) to bin alloys.
    For simplicity and robustness, we bin the target variable (yield strength) 
    into quantile bins to ensure distribution balance.
    """
    logger.info("Creating stratified split based on yield strength distribution.")
    
    # Create strata by binning the target variable into 10 bins
    n_bins = 10
    strata = pd.qcut(y, q=n_bins, labels=False, duplicates='drop')
    
    # If qcut fails due to too few samples, fallback to uniform split
    if len(np.unique(strata)) < 2:
        logger.warning("Too few samples for stratification. Falling back to random split.")
        strata = np.zeros_like(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=strata
    )
    
    # Validation: approximate disjointness check (indices are naturally disjoint)
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    return X_train, X_test, y_train, y_test

def save_split_info(train_idx: int, test_idx: int, seed: int):
    """Save split configuration to a JSON file."""
    info = {
        "train_size": train_idx,
        "test_size": test_idx,
        "random_seed": seed,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    path = "output/split_info.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(info, f, indent=2)
    logger.info(f"Saved split info to {path}")

def train_linear_regression(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Tuple[LinearRegression, Dict[str, float]]:
    """Train Linear Regression baseline."""
    logger.info("Training Linear Regression baseline...")
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    metrics = {
        "R2": float(r2_score(y_test, y_pred)),
        "MAE": float(mean_absolute_error(y_test, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }
    logger.info(f"Linear Regression Metrics: {metrics}")
    return model, metrics

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, feature_names: List[str]) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """Train Random Forest with 5-fold CV and grid search."""
    logger.info("Training Random Forest with Grid Search...")
    
    # Grid search parameters as per T018: trees 10-50, depth <= 10
    param_grid = {
        'n_estimators': [10, 20, 30, 40, 50],
        'max_depth': [5, 7, 10],
        'min_samples_split': [2, 5]
    }
    
    rf = RandomForestRegressor(random_state=get_seed(), n_jobs=-1)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=get_seed())
    
    # We need strata for RF CV too, using binned y
    n_bins = 5
    strata = pd.qcut(y_train, q=n_bins, labels=False, duplicates='drop')
    if len(np.unique(strata)) < 2:
        strata = np.zeros_like(y_train)

    grid_search = GridSearchCV(
        rf, param_grid, cv=cv, scoring='r2', n_jobs=-1, verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    logger.info(f"Best RF params: {grid_search.best_params_}")
    
    y_pred = best_model.predict(X_test)
    metrics = {
        "R2": float(r2_score(y_test, y_pred)),
        "MAE": float(mean_absolute_error(y_test, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }
    logger.info(f"Random Forest Metrics: {metrics}")
    return best_model, metrics

def train_gradient_boosting(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, feature_names: List[str]) -> Tuple[GradientBoostingRegressor, Dict[str, float]]:
    """Train Gradient Boosting with 5-fold CV and grid search."""
    logger.info("Training Gradient Boosting with Grid Search...")
    
    # Grid search parameters as per T019: trees 10-50, depth <= 10
    param_grid = {
        'n_estimators': [10, 20, 30, 40, 50],
        'max_depth': [3, 5, 7, 10],
        'learning_rate': [0.05, 0.1]
    }
    
    gb = GradientBoostingRegressor(random_state=get_seed())
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=get_seed())
    
    # Strata for CV
    n_bins = 5
    strata = pd.qcut(y_train, q=n_bins, labels=False, duplicates='drop')
    if len(np.unique(strata)) < 2:
        strata = np.zeros_like(y_train)

    grid_search = GridSearchCV(
        gb, param_grid, cv=cv, scoring='r2', n_jobs=-1, verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    logger.info(f"Best GB params: {grid_search.best_params_}")
    
    y_pred = best_model.predict(X_test)
    metrics = {
        "R2": float(r2_score(y_test, y_pred)),
        "MAE": float(mean_absolute_error(y_test, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }
    logger.info(f"Gradient Boosting Metrics: {metrics}")
    return best_model, metrics

def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute standard regression metrics."""
    return {
        "R2": float(r2_score(y_true, y_pred)),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred)))
    }

def run_training_pipeline():
    """
    Execute the full training pipeline:
    1. Load data
    2. Split
    3. Train Linear, RF, GB
    4. Evaluate
    5. Write metrics.json
    """
    start_time = time.time()
    set_seeds(42) # Ensure reproducibility
    
    try:
        # 1. Load Data
        df = load_processed_data()
        if len(df) == 0:
            raise ValueError("Dataset is empty. Cannot train models.")
        
        # 2. Prepare Features
        X, y, feature_names = prepare_features_target(df)
        
        # 3. Split Data
        X_train, X_test, y_train, y_test = create_stratified_split(X, y, feature_names)
        
        # 4. Train Models
        model_linear, metrics_linear = train_linear_regression(X_train, y_train, X_test, y_test)
        model_rf, metrics_rf = train_random_forest(X_train, y_train, X_test, y_test, feature_names)
        model_gb, metrics_gb = train_gradient_boosting(X_train, y_train, X_test, y_test, feature_names)
        
        # 5. Determine Best Model
        models_metrics = {
            "linear": metrics_linear,
            "rf": metrics_rf,
            "gb": metrics_gb
        }
        
        best_model_name = max(models_metrics, key=lambda k: models_metrics[k]["R2"])
        
        # 6. Write Output
        output_data = {
            "rf": metrics_rf,
            "gb": metrics_gb,
            "linear": metrics_linear,
            "best_model": best_model_name
        }
        
        output_path = "output/metrics.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Training complete. Best model: {best_model_name}. Metrics written to {output_path}")
        return output_data

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        traceback.print_exc()
        raise

def main():
    """Entry point for the training script."""
    run_training_pipeline()

if __name__ == "__main__":
    main()
