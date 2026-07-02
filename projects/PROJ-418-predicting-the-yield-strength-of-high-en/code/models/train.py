import os
import sys
import json
import time
import traceback
from typing import Dict, Any, Tuple, Optional, List

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from utils.logging import get_logger, set_seeds, get_seed
from utils.config import get_config

logger = get_logger(__name__)

# Constants for Gradient Boosting constraints (from task T019)
MAX_TREES_GB = 50
MAX_DEPTH_GB = 10

def load_processed_data(filepath: str = "data/processed/hea_descriptors.csv") -> pd.DataFrame:
    """
    Load the processed HEA dataset with calculated descriptors.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    logger.info(f"Loading processed data from {filepath}")
    df = pd.read_csv(filepath)
    return df

def prepare_features_target(df: pd.DataFrame, target_col: str = "yield_strength_mpa") -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separate features and target variable.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe. Available columns: {df.columns.tolist()}")
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    logger.info(f"Prepared features (shape: {X.shape}) and target (shape: {y.shape})")
    return X, y

def create_stratified_split(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Create stratified train/test split.
    Since y is continuous, we bin it for stratification.
    """
    if random_state is None:
        random_state = get_seed()
    
    # Bin y for stratification
    y_binned = pd.qcut(y, q=5, labels=False, duplicates='drop')
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y_binned
    )
    logger.info(f"Split data: Train={X_train.shape[0]}, Test={X_test.shape[0]}")
    return X_train, X_test, y_train, y_test

def save_split_info(split_info: Dict[str, Any], filepath: str = "output/split_info.json"):
    """
    Save split configuration to JSON.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(split_info, f, indent=2)
    logger.info(f"Saved split info to {filepath}")

def train_linear_regression(X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
    """
    Train Linear Regression baseline.
    """
    logger.info("Training Linear Regression baseline...")
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    metrics = {
        "r2": r2_score(y_test, y_pred),
        "mae": mean_absolute_error(y_test, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, y_pred))
    }
    logger.info(f"Linear Regression Metrics: R2={metrics['r2']:.4f}, MAE={metrics['mae']:.4f}, RMSE={metrics['rmse']:.4f}")
    return {"model": model, "metrics": metrics, "type": "linear"}

def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series, random_state: Optional[int] = None) -> Dict[str, Any]:
    """
    Train Random Forest with 5-fold CV and grid search (trees <= 50, depth <= 10).
    """
    if random_state is None:
        random_state = get_seed()
    
    logger.info("Training Random Forest with GridSearchCV...")
    
    from sklearn.ensemble import RandomForestRegressor
    
    param_grid = {
        'n_estimators': [10, 30, 50],
        'max_depth': [3, 5, 7, 10],
        'min_samples_split': [2, 5]
    }
    
    rf_base = RandomForestRegressor(random_state=random_state)
    
    # 5-fold CV as per spec
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    # Note: RF regression doesn't strictly need stratified CV on continuous y, 
    # but we follow the instruction to use 5-fold CV. 
    # Using simple KFold for regression usually, but sticking to instruction logic:
    # If we strictly need StratifiedKFold, we need to bin y again here or use KFold.
    # Given T016 used StratifiedKFold on binned y, we can do similar here or just KFold.
    # Let's use KFold for regression to avoid potential binning issues if y range is small.
    cv_reg = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state) 
    # Actually, for regression, KFold is standard. But T016 specified Stratified.
    # Let's use KFold for RF to be safe, as stratification on continuous targets is heuristic.
    from sklearn.model_selection import KFold
    cv_reg = KFold(n_splits=5, shuffle=True, random_state=random_state)

    grid_search = GridSearchCV(
        rf_base, 
        param_grid, 
        cv=cv_reg, 
        scoring='r2', 
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    logger.info(f"Random Forest Best Params: {grid_search.best_params_}")
    
    y_pred = best_model.predict(X_test)
    metrics = {
        "r2": r2_score(y_test, y_pred),
        "mae": mean_absolute_error(y_test, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, y_pred))
    }
    logger.info(f"Random Forest Metrics: R2={metrics['r2']:.4f}, MAE={metrics['mae']:.4f}, RMSE={metrics['rmse']:.4f}")
    
    return {
        "model": best_model, 
        "metrics": metrics, 
        "type": "random_forest",
        "best_params": grid_search.best_params_
    }

def train_gradient_boosting(X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series, random_state: Optional[int] = None) -> Dict[str, Any]:
    """
    Implement Gradient Boosting trainer with 5-fold CV and grid search.
    Constraints: trees <= 50, depth <= 10.
    """
    if random_state is None:
        random_state = get_seed()
    
    logger.info("Training Gradient Boosting with GridSearchCV...")
    
    param_grid = {
        'n_estimators': [10, 30, 50],
        'max_depth': [3, 5, 7, 10],
        'learning_rate': [0.05, 0.1, 0.2],
        'min_samples_split': [2, 5]
    }
    
    gb_base = GradientBoostingRegressor(random_state=random_state)
    
    # 5-fold CV
    from sklearn.model_selection import KFold
    cv_reg = KFold(n_splits=5, shuffle=True, random_state=random_state)

    grid_search = GridSearchCV(
        gb_base, 
        param_grid, 
        cv=cv_reg, 
        scoring='r2', 
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    logger.info(f"Gradient Boosting Best Params: {grid_search.best_params_}")
    
    y_pred = best_model.predict(X_test)
    metrics = {
        "r2": r2_score(y_test, y_pred),
        "mae": mean_absolute_error(y_test, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, y_pred))
    }
    logger.info(f"Gradient Boosting Metrics: R2={metrics['r2']:.4f}, MAE={metrics['mae']:.4f}, RMSE={metrics['rmse']:.4f}")
    
    return {
        "model": best_model, 
        "metrics": metrics, 
        "type": "gradient_boosting",
        "best_params": grid_search.best_params_
    }

def evaluate_model(model_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return the metrics from a trained model result.
    """
    return model_result.get("metrics", {})

def run_training_pipeline():
    """
    Main entry point to run the full training pipeline including Gradient Boosting.
    """
    logger.info("Starting Training Pipeline...")
    start_time = time.time()
    
    try:
        # 1. Load Data
        df = load_processed_data()
        X, y = prepare_features_target(df)
        
        # 2. Split Data
        X_train, X_test, y_train, y_test = create_stratified_split(X, y)
        
        split_info = {
            "train_size": len(X_train),
            "test_size": len(X_test),
            "seed": get_seed(),
            "test_ratio": 0.2
        }
        save_split_info(split_info)
        
        # 3. Train Models
        # Linear
        lr_result = train_linear_regression(X_train, y_train, X_test, y_test)
        
        # Random Forest
        rf_result = train_random_forest(X_train, y_train, X_test, y_test)
        
        # Gradient Boosting (T019)
        gb_result = train_gradient_boosting(X_train, y_train, X_test, y_test)
        
        # 4. Compile Metrics
        all_metrics = {
            "linear_regression": lr_result["metrics"],
            "random_forest": rf_result["metrics"],
            "gradient_boosting": gb_result["metrics"]
        }
        
        # 5. Save Metrics
        os.makedirs("output", exist_ok=True)
        metrics_path = "output/metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(all_metrics, f, indent=2)
        logger.info(f"Metrics saved to {metrics_path}")
        
        elapsed = time.time() - start_time
        logger.info(f"Training pipeline completed in {elapsed:.2f} seconds")
        
        if elapsed > 3 * 3600:
            logger.warning("Training pipeline exceeded 3-hour limit.")
        
        return all_metrics
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run_training_pipeline()