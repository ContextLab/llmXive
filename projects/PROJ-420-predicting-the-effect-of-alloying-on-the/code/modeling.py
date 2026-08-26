"""
Modeling module for Random Forest training and evaluation.
Implements T021, T022, T023c, T023d, T024, T025.
"""
import logging
import pickle
import json
import time
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_predict, KFold, RepeatedKFold
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from config import get_config
from logging_config import get_logger, log_operation

logger = get_logger(__name__)

def load_features_and_target(data_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """Load features and target from the cleaned dataset."""
    config = get_config()
    if data_path is None:
        data_path = str(config.data_processed_dir / "alloys_clean.parquet")
    
    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)
    
    # Features: ILR transformed composition
    feature_cols = [col for col in df.columns if col.startswith('ilr_')]
    X = df[feature_cols]
    
    # Target: Poisson's ratio
    y = df['poisson_ratio']
    
    return X, y

def train_random_forest_with_cv(
    X: pd.DataFrame,
    y: pd.Series,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    random_state: int = 42,
    n_splits: int = 5,
    n_repeats: int = 10
) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """
    T021: Train Random Forest with repeated k-fold cross-validation.
    Returns model and CV metrics.
    """
    log_operation("train_random_forest_with_cv", status="started")
    
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1
    )
    
    # Repeated K-Fold
    rkf = RepeatedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=random_state)
    
    # Get cross-validated predictions
    cv_predictions = cross_val_predict(model, X, y, cv=rkf, n_jobs=-1)
    
    # Calculate MAE
    cv_mae = mean_absolute_error(y, cv_predictions)
    
    # Calculate confidence interval (95%)
    residuals = y - cv_predictions
    ci_lower = np.percentile(residuals, 2.5)
    ci_upper = np.percentile(residuals, 97.5)
    
    metrics = {
        'cv_mae': float(cv_mae),
        'cv_ci_lower': float(ci_lower),
        'cv_ci_upper': float(ci_upper)
    }
    
    # Train final model on full data
    model.fit(X, y)
    
    log_operation("train_random_forest_with_cv", status="completed", cv_mae=cv_mae)
    
    return model, metrics

def evaluate_model_on_test(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 100,
    max_depth: Optional[int] = None
) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """
    T025: Train and evaluate on held-out test set.
    Returns model and test metrics.
    """
    log_operation("evaluate_model_on_test", status="started")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # Train model
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = model.predict(X_test)
    test_mae = mean_absolute_error(y_test, y_pred)
    
    metrics = {
        'test_mae': float(test_mae),
        'test_size': len(y_test),
        'train_size': len(y_train)
    }
    
    log_operation("evaluate_model_on_test", status="completed", test_mae=test_mae)
    
    return model, metrics

def save_model_metrics(cv_metrics: Dict[str, float], test_metrics: Dict[str, float], output_path: Optional[str] = None):
    """
    T023d: Save combined model metrics to JSON.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.results_dir / "model_metrics.json")
    
    # Ensure results directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    combined_metrics = {
        **cv_metrics,
        **test_metrics
    }
    
    with open(output_path, 'w') as f:
        json.dump(combined_metrics, f, indent=2)
    
    logger.info(f"Saved model metrics to {output_path}")

def check_mae_threshold(cv_mae: float, threshold: float = 0.05) -> bool:
    """
    T023c: Check if CV MAE exceeds threshold.
    Returns True if threshold is exceeded.
    """
    return cv_mae > threshold

def write_methodological_flags(cv_mae: float, threshold: float = 0.05, output_path: Optional[str] = None):
    """
    T023c: Write methodological flags based on MAE threshold.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.results_dir / "methodological_flags.json")
    
    # Ensure results directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    mae_flag = check_mae_threshold(cv_mae, threshold)
    
    flags = {
        'mae_threshold_exceeded': mae_flag,
        'cv_mae': cv_mae,
        'threshold': threshold,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(output_path, 'w') as f:
        json.dump(flags, f, indent=2)
    
    logger.info(f"Saved methodological flags to {output_path}")

def save_model(model: RandomForestRegressor, model_path: Optional[str] = None):
    """
    T024: Serialize trained model.
    """
    config = get_config()
    if model_path is None:
        model_path = str(config.models_dir / "rf_model.pkl")
    
    # Ensure models directory exists
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f, protocol=3)
    
    logger.info(f"Saved model to {model_path}")

def save_model_metrics_combined(cv_metrics: Dict[str, float], test_metrics: Dict[str, float]):
    """Combined metrics saving."""
    save_model_metrics(cv_metrics, test_metrics)

def run_modeling_pipeline():
    """
    Main function to run the full modeling pipeline.
    """
    log_operation("run_modeling_pipeline", status="started")
    
    # Load data
    X, y = load_features_and_target()
    
    # Train with CV (T021, T022)
    model_cv, cv_metrics = train_random_forest_with_cv(X, y)
    
    # Evaluate on test set (T025)
    model_test, test_metrics = evaluate_model_on_test(X, y)
    
    # Save model (T024)
    save_model(model_test)
    
    # Save metrics (T023d)
    save_model_metrics(cv_metrics, test_metrics)
    
    # Write methodological flags (T023c)
    write_methodological_flags(cv_metrics['cv_mae'])
    
    log_operation("run_modeling_pipeline", status="completed")
    
    return model_test, cv_metrics, test_metrics

def main():
    """Entry point for modeling script."""
    run_modeling_pipeline()

if __name__ == "__main__":
    main()
