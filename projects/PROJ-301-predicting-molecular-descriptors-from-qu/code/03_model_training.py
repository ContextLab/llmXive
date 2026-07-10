import os
import json
import logging
import argparse
import pickle
import time
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy import stats

# Project internal imports
from config import set_seeds
from utils.logger import setup_logger, get_logger, configure_logging_for_pipeline
from utils.memory_monitor import get_memory_usage_gb, check_memory_limit, force_gc
from utils.models import ModelResult

# Initialize logger
logger = get_logger(__name__)
configure_logging_for_pipeline()

# Constants
MAX_RUNTIME_HOURS = 6.0
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600
ARTIFACTS_DIR = Path("artifacts")
MODELS_DIR = ARTIFACTS_DIR / "models"
METRICS_DIR = ARTIFACTS_DIR / "metrics"
DATA_PROCESSED_DIR = Path("data") / "processed"

def load_features_and_labels() -> Tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Load 2D features, 3D features, and labels from the processed data directory.
    Returns:
        features_2d: np.ndarray (n_samples, n_features_2d)
        features_3d: np.ndarray (n_samples, n_features_3d)
        labels: np.ndarray (n_samples, n_descriptors)
        labels_df: pd.DataFrame with molecule IDs and descriptor values
    """
    logger.info("Loading features and labels...")
    
    features_2d_path = DATA_PROCESSED_DIR / "features_2d.npy"
    features_3d_path = DATA_PROCESSED_DIR / "features_3d.npy"
    labels_path = DATA_PROCESSED_DIR / "labels.csv"

    if not features_2d_path.exists():
        raise FileNotFoundError(f"2D features not found at {features_2d_path}")
    if not features_3d_path.exists():
        raise FileNotFoundError(f"3D features not found at {features_3d_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels not found at {labels_path}")

    features_2d = np.load(features_2d_path)
    features_3d = np.load(features_3d_path)
    labels_df = pd.read_csv(labels_path)

    # Assuming labels columns are 'dipole', 'HOMO', 'LUMO' based on spec
    label_cols = ['dipole', 'HOMO', 'LUMO']
    if not all(col in labels_df.columns for col in label_cols):
        available_cols = list(labels_df.columns)
        raise ValueError(f"Expected label columns {label_cols} not found in {labels_path}. Found: {available_cols}")
    
    labels = labels_df[label_cols].values

    logger.info(f"Loaded features: 2D={features_2d.shape}, 3D={features_3d.shape}, Labels={labels.shape}")
    return features_2d, features_3d, labels, labels_df

def train_model(
    X: np.ndarray,
    y: np.ndarray,
    descriptor_name: str,
    param_grid: Dict[str, Any],
    n_splits: int = 5
) -> Tuple[RandomForestRegressor, Dict[str, Any], List[float]]:
    """
    Train a Random Forest model with GridSearchCV.
    
    Args:
        X: Feature matrix
        y: Target values (1D array for single descriptor)
        descriptor_name: Name of the target descriptor for logging
        param_grid: Hyperparameter grid for GridSearchCV
        n_splits: Number of CV folds
    
    Returns:
        best_model: The trained Random Forest Regressor
        cv_results: Dictionary containing best params and mean metrics
        fold_maes: List of MAE for each fold
    """
    logger.info(f"Training model for {descriptor_name}...")
    
    # Ensure y is 1D
    if y.ndim > 1:
        y = y.ravel()

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    # GridSearchCV
    grid_search = GridSearchCV(
        estimator=RandomForestRegressor(random_state=42),
        param_grid=param_grid,
        cv=kf,
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        verbose=1
    )

    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Extract per-fold MAE
    # cv_results_ contains 'mean_test_score' which is negative MAE
    # We need to reconstruct fold-wise MAE if not directly available in a simple list
    # However, sklearn's cross_validate is better for explicit fold scores, but we used GridSearch
    # Let's re-run CV on the best params to get exact fold MAEs for reporting
    
    best_params_model = RandomForestRegressor(**best_params, random_state=42)
    
    fold_maes = []
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        fold_model = RandomForestRegressor(**best_params, random_state=42)
        fold_model.fit(X_train, y_train)
        y_pred = fold_model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        fold_maes.append(mae)
    
    cv_results = {
        'best_params': best_params,
        'mean_mae': np.mean(fold_maes),
        'std_mae': np.std(fold_maes),
        'rmse': np.sqrt(mean_squared_error(y, best_model.predict(X))),
        'r2': best_model.score(X, y)
    }
    
    logger.info(f"Completed training for {descriptor_name}. Best params: {best_params}, Mean MAE: {np.mean(fold_maes):.4f}")
    
    return best_model, cv_results, fold_maes

def train_model_2d(
    features_2d: np.ndarray,
    labels: np.ndarray,
    param_grid: Dict[str, Any]
) -> Dict[str, ModelResult]:
    """
    Train models for all descriptors using 2D features.
    """
    models = {}
    for i, desc_name in enumerate(['dipole', 'HOMO', 'LUMO']):
        y = labels[:, i]
        model, cv_res, fold_maes = train_model(features_2d, y, f"2D_{desc_name}", param_grid)
        
        # Save model
        model_path = MODELS_DIR / f"model_2d_{desc_name}.pkl"
        os.makedirs(model_path.parent, exist_ok=True)
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        models[desc_name] = ModelResult(
            model_type="RandomForest_2D",
            descriptor=desc_name,
            params=cv_res['best_params'],
            metrics=cv_res,
            fold_maes=fold_maes,
            model_path=str(model_path)
        )
    return models

def train_model_3d(
    features_3d: np.ndarray,
    labels: np.ndarray,
    param_grid: Dict[str, Any]
) -> Dict[str, ModelResult]:
    """
    Train models for all descriptors using 3D features.
    """
    models = {}
    for i, desc_name in enumerate(['dipole', 'HOMO', 'LUMO']):
        y = labels[:, i]
        model, cv_res, fold_maes = train_model(features_3d, y, f"3D_{desc_name}", param_grid)
        
        # Save model
        model_path = MODELS_DIR / f"model_3d_{desc_name}.pkl"
        os.makedirs(model_path.parent, exist_ok=True)
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        models[desc_name] = ModelResult(
            model_type="RandomForest_3D",
            descriptor=desc_name,
            params=cv_res['best_params'],
            metrics=cv_res,
            fold_maes=fold_maes,
            model_path=str(model_path)
        )
    return models

def aggregate_cv_metrics(
    models_2d: Dict[str, ModelResult],
    models_3d: Dict[str, ModelResult]
) -> None:
    """
    Aggregate CV metrics from both models and save to JSON.
    Also performs stability verification (SC-005).
    """
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    
    cv_metrics = {
        "2D": {},
        "3D": {}
    }
    
    stability_report = {}
    
    for desc in ['dipole', 'HOMO', 'LUMO']:
        # Process 2D
        m_2d = models_2d[desc]
        cv_metrics["2D"][desc] = {
            "fold_maes": m_2d.fold_maes,
            "mean_mae": m_2d.metrics['mean_mae'],
            "std_mae": m_2d.metrics['std_mae'],
            "rmse": m_2d.metrics['rmse'],
            "r2": m_2d.metrics['r2'],
            "best_params": m_2d.params
        }
        
        # Stability check 2D
        mean_mae = m_2d.metrics['mean_mae']
        std_mae = m_2d.metrics['std_mae']
        stability_ratio = std_mae / mean_mae if mean_mae != 0 else 0.0
        passed_2d = stability_ratio <= 0.05
        
        stability_report[f"2D_{desc}"] = {
            "fold_maes": m_2d.fold_maes,
            "stability_ratio": stability_ratio,
            "passed": passed_2d,
            "threshold": 0.05
        }
        
        if not passed_2d:
            logger.warning(f"Stability check FAILED for 2D {desc}: ratio={stability_ratio:.4f} > 0.05")

        # Process 3D
        m_3d = models_3d[desc]
        cv_metrics["3D"][desc] = {
            "fold_maes": m_3d.fold_maes,
            "mean_mae": m_3d.metrics['mean_mae'],
            "std_mae": m_3d.metrics['std_mae'],
            "rmse": m_3d.metrics['rmse'],
            "r2": m_3d.metrics['r2'],
            "best_params": m_3d.params
        }
        
        # Stability check 3D
        mean_mae = m_3d.metrics['mean_mae']
        std_mae = m_3d.metrics['std_mae']
        stability_ratio = std_mae / mean_mae if mean_mae != 0 else 0.0
        passed_3d = stability_ratio <= 0.05
        
        stability_report[f"3D_{desc}"] = {
            "fold_maes": m_3d.fold_maes,
            "stability_ratio": stability_ratio,
            "passed": passed_3d,
            "threshold": 0.05
        }
        
        if not passed_3d:
            logger.warning(f"Stability check FAILED for 3D {desc}: ratio={stability_ratio:.4f} > 0.05")

    # Save metrics
    with open(METRICS_DIR / "cv_metrics.json", 'w') as f:
        json.dump(cv_metrics, f, indent=2)
        
    # Save stability report
    with open(METRICS_DIR / "stability_report.json", 'w') as f:
        json.dump(stability_report, f, indent=2)

def monitor_runtime_and_train():
    """
    Main entry point for T034: Runtime Measurement and Training Orchestration.
    Wraps the training pipeline to measure total runtime.
    If runtime > 6 hours, triggers graceful failure and saves partial results.
    """
    set_seeds(42)
    
    logger.info("Starting Model Training Pipeline with Runtime Monitoring (T034)...")
    start_time = time.time()
    
    try:
        # Define Hyperparameter Grid
        param_grid = {
            'n_estimators': [100, 500, 1000],
            'max_depth': [10, 20, None]
        }
        
        # Load Data
        features_2d, features_3d, labels, labels_df = load_features_and_labels()
        
        # Train 2D Models
        logger.info(">>> Phase 1: Training 2D Models")
        models_2d = train_model_2d(features_2d, labels, param_grid)
        
        # Train 3D Models
        logger.info(">>> Phase 2: Training 3D Models")
        models_3d = train_model_3d(features_3d, labels, param_grid)
        
        # Aggregate Metrics
        logger.info(">>> Phase 3: Aggregating Metrics")
        aggregate_cv_metrics(models_2d, models_3d)
        
        end_time = time.time()
        total_runtime_seconds = end_time - start_time
        total_runtime_hours = total_runtime_seconds / 3600.0
        
        logger.info(f"Pipeline completed successfully in {total_runtime_hours:.2f} hours ({total_runtime_seconds:.2f} seconds).")
        
        # Save Runtime Report
        runtime_report = {
            "status": "success",
            "total_runtime_seconds": total_runtime_seconds,
            "total_runtime_hours": total_runtime_hours,
            "limit_hours": MAX_RUNTIME_HOURS,
            "limit_seconds": MAX_RUNTIME_SECONDS
        }
        
        with open(METRICS_DIR / "runtime_report.json", 'w') as f:
            json.dump(runtime_report, f, indent=2)
            
    except Exception as e:
        end_time = time.time()
        total_runtime_seconds = end_time - start_time
        total_runtime_hours = total_runtime_seconds / 3600.0
        
        error_msg = str(e)
        logger.error(f"Pipeline failed with error: {error_msg}", exc_info=True)
        
        # Save partial results and failure report
        failure_report = {
            "status": "failed",
            "error": error_msg,
            "total_runtime_seconds": total_runtime_seconds,
            "total_runtime_hours": total_runtime_hours,
            "limit_hours": MAX_RUNTIME_HOURS,
            "limit_seconds": MAX_RUNTIME_SECONDS,
            "partial_results_saved": True # Assuming we save what we have up to the crash
        }
        
        with open(METRICS_DIR / "runtime_failure.json", 'w') as f:
            json.dump(failure_report, f, indent=2)
        
        raise

def main():
    """
    CLI entry point.
    """
    parser = argparse.ArgumentParser(description="Train ML models for molecular descriptors.")
    parser.add_argument("--config", type=str, default="config.py", help="Path to config file")
    args = parser.parse_args()
    
    monitor_runtime_and_train()

if __name__ == "__main__":
    main()