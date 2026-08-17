import os
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import from project modules
from config import get_config, validate_config, ensure_directories
from utils.logging import DataPipelineLog
from models.entities import ModelResult

# ML Imports
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

def _handle_oom_exception(e: Exception, model_name: str) -> Exception:
    """
    Check if exception is related to OOM/GPU issues and re-raise with a clear message.
    If not an OOM/GPU issue, re-raise the original exception.
    """
    error_str = str(e).lower()
    
    # Common OOM/GPU related keywords
    oom_keywords = [
        "out of memory", "oom", "cuda out of memory", 
        "gpu memory", "resource temporarily unavailable",
        "failed to allocate", "no space left on device"
    ]
    
    is_oom = any(keyword in error_str for keyword in oom_keywords)
    
    if is_oom:
        raise RuntimeError(
            f"Critical Error: {model_name} training failed due to Out of Memory (OOM) or GPU resource constraints. "
            f"Original error: {str(e)}. "
            f"Action: Reduce batch size, decrease model complexity (n_estimators/depth), or use a machine with more RAM."
        ) from e
    else:
        raise e

def train_knn_baseline(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    distance_matrix: np.ndarray,
    logger: DataPipelineLog
) -> Tuple[KNeighborsClassifier, ModelResult]:
    """
    Train KNN Baseline using the provided phylogenetic distance matrix.
    
    Args:
        X_train: Training features (not used directly for KNN with custom metric, but kept for interface)
        y_train: Training labels
        distance_matrix: Pre-computed phylogenetic distance matrix
        logger: Logger instance
        
    Returns:
        Tuple of (trained model, ModelResult)
    """
    model_name = "KNN_Baseline_Phylo"
    logger.info(f"Starting training for {model_name}")
    
    try:
        # KNN with custom metric using precomputed distance matrix
        # Note: sklearn KNeighborsClassifier supports 'precomputed' metric
        knn = KNeighborsClassifier(
            n_neighbors=5,
            metric='precomputed',
            algorithm='brute' # Must use brute for precomputed
        )
        
        # The distance matrix for training needs to be the subset of the full matrix
        # corresponding to the training indices. 
        # Assuming X_train shape matches the rows of distance_matrix passed in.
        # If distance_matrix is full N x N, we need to slice it.
        # For this function signature, we assume distance_matrix passed is already the N_train x N_train subset.
        
        knn.fit(distance_matrix, y_train)
        
        # Evaluate on train set for immediate feedback (optional, but good for logging)
        # Note: For precomputed, we need the train-train distance matrix again
        y_train_pred = knn.predict(distance_matrix)
        train_auc = roc_auc_score(y_train, y_train_pred) if len(np.unique(y_train)) > 1 else 0.0
        
        metrics = {
            "model_name": model_name,
            "train_auc": float(train_auc),
            "n_neighbors": 5,
            "metric": "precomputed"
        }
        
        result = ModelResult(
            model_name=model_name,
            metrics=metrics,
            hyperparameters={"n_neighbors": 5, "metric": "precomputed"},
            feature_importance={} # KNN doesn't have feature importance in the same way
        )
        
        logger.info(f"{model_name} training completed. Train AUC: {train_auc:.4f}")
        return knn, result

    except Exception as e:
        _handle_oom_exception(e, model_name)
        raise

def train_random_forest(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    logger: DataPipelineLog,
    n_jobs: int = 2
) -> Tuple[RandomForestClassifier, ModelResult]:
    """
    Train RandomForest with grid search over n_estimators.
    
    Args:
        X_train: Training features
        y_train: Training labels
        logger: Logger instance
        n_jobs: Number of parallel jobs
        
    Returns:
        Tuple of (trained model, ModelResult)
    """
    model_name = "RandomForest"
    logger.info(f"Starting training for {model_name}")
    
    try:
        # Base model
        rf = RandomForestClassifier(random_state=42, n_jobs=n_jobs)
        
        # Grid search parameters
        param_grid = {
            'n_estimators': [100, 200, 500]
        }
        
        # Cross-validation
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        
        grid_search = GridSearchCV(
            estimator=rf,
            param_grid=param_grid,
            cv=cv,
            scoring='roc_auc',
            n_jobs=n_jobs,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        best_score = grid_search.best_score_
        
        # Calculate feature importance
        feature_names = [f"feature_{i}" for i in range(X_train.shape[1])]
        importances = best_model.feature_importances_
        feature_importance = dict(zip(feature_names, importances.tolist()))
        
        metrics = {
            "model_name": model_name,
            "best_cv_auc": float(best_score),
            "best_params": best_params,
            "n_estimators": best_params['n_estimators']
        }
        
        result = ModelResult(
            model_name=model_name,
            metrics=metrics,
            hyperparameters=best_params,
            feature_importance=feature_importance
        )
        
        logger.info(f"{model_name} training completed. Best CV AUC: {best_score:.4f} with n_estimators={best_params['n_estimators']}")
        return best_model, result

    except Exception as e:
        _handle_oom_exception(e, model_name)
        raise

def train_xgboost(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    logger: DataPipelineLog,
    n_jobs: int = 2
) -> Tuple[XGBClassifier, ModelResult]:
    """
    Train XGBoost with grid search over n_estimators.
    
    Args:
        X_train: Training features
        y_train: Training labels
        logger: Logger instance
        n_jobs: Number of parallel jobs
        
    Returns:
        Tuple of (trained model, ModelResult)
    """
    model_name = "XGBoost"
    logger.info(f"Starting training for {model_name}")
    
    try:
        # Base model - use tree_method='hist' for speed and 'gpu_hist' if GPU available, else 'hist'
        # We force 'hist' to ensure CPU compatibility as per project constraints
        xgb = XGBClassifier(
            random_state=42,
            n_jobs=n_jobs,
            tree_method='hist',
            use_label_encoder=False,
            eval_metric='logloss'
        )
        
        # Grid search parameters
        param_grid = {
            'n_estimators': [100, 200, 500]
        }
        
        # Cross-validation
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        
        grid_search = GridSearchCV(
            estimator=xgb,
            param_grid=param_grid,
            cv=cv,
            scoring='roc_auc',
            n_jobs=n_jobs,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        best_score = grid_search.best_score_
        
        # Calculate feature importance
        feature_names = [f"feature_{i}" for i in range(X_train.shape[1])]
        importances = best_model.feature_importances_
        feature_importance = dict(zip(feature_names, importances.tolist()))
        
        metrics = {
            "model_name": model_name,
            "best_cv_auc": float(best_score),
            "best_params": best_params,
            "n_estimators": best_params['n_estimators']
        }
        
        result = ModelResult(
            model_name=model_name,
            metrics=metrics,
            hyperparameters=best_params,
            feature_importance=feature_importance
        )
        
        logger.info(f"{model_name} training completed. Best CV AUC: {best_score:.4f} with n_estimators={best_params['n_estimators']}")
        return best_model, result

    except Exception as e:
        _handle_oom_exception(e, model_name)
        raise

def save_models(
    models: Dict[str, Any], 
    results: Dict[str, ModelResult], 
    output_dir: str,
    logger: DataPipelineLog
) -> None:
    """
    Save trained models and results to disk.
    
    Args:
        models: Dictionary of model_name -> model_instance
        results: Dictionary of model_name -> ModelResult
        output_dir: Directory to save artifacts
        logger: Logger instance
    """
    ensure_directories(output_dir)
    
    for name, model in models.items():
        path = os.path.join(output_dir, f"{name}.joblib")
        joblib.dump(model, path)
        logger.info(f"Saved model {name} to {path}")
        
    for name, result in results.items():
        path = os.path.join(output_dir, f"{name}_result.json")
        # Convert ModelResult to dict for JSON serialization
        result_dict = {
            "model_name": result.model_name,
            "metrics": result.metrics,
            "hyperparameters": result.hyperparameters,
            "feature_importance": result.feature_importance
        }
        with open(path, 'w') as f:
            json.dump(result_dict, f, indent=2)
        logger.info(f"Saved result for {name} to {path}")

def main():
    """
    Main entry point for training pipeline.
    Loads data, trains models, and saves results.
    """
    config = get_config()
    validate_config(config)
    
    # Setup logging
    log_dir = os.path.join(config['paths']['data_root'], 'logs')
    ensure_directories(log_dir)
    logger = DataPipelineLog(log_path=os.path.join(log_dir, 'training.log'))
    
    logger.info("Starting model training pipeline")
    
    try:
        # Load split data
        # Assuming data is in data/processed/split_data/
        train_data_path = os.path.join(config['paths']['data_root'], 'processed', 'split_data', 'X_train.npy')
        train_labels_path = os.path.join(config['paths']['data_root'], 'processed', 'split_data', 'y_train.npy')
        test_data_path = os.path.join(config['paths']['data_root'], 'processed', 'split_data', 'X_test.npy')
        test_labels_path = os.path.join(config['paths']['data_root'], 'processed', 'split_data', 'y_test.npy')
        phylo_matrix_path = os.path.join(config['paths']['data_root'], 'processed', 'synthetic_phylo_matrix.npy')
        
        if not os.path.exists(train_data_path):
            raise FileNotFoundError(f"Training data not found at {train_data_path}. Run split.py first.")
        
        X_train = np.load(train_data_path)
        y_train = np.load(train_labels_path)
        X_test = np.load(test_data_path)
        y_test = np.load(test_labels_path)
        
        # Load phylogenetic matrix for KNN
        # We need the subset of the matrix corresponding to training indices
        # For simplicity, we assume the split indices are 0..N_train
        # In a real scenario, we would load the full matrix and slice it
        full_phylo = np.load(phylo_matrix_path)
        n_train = len(y_train)
        train_phylo_matrix = full_phylo[:n_train, :n_train]
        
        models = {}
        results = {}
        
        # Train KNN
        logger.info("Training KNN Baseline")
        try:
            knn, knn_result = train_knn_baseline(X_train, y_train, train_phylo_matrix, logger)
            models['KNN_Baseline_Phylo'] = knn
            results['KNN_Baseline_Phylo'] = knn_result
        except Exception as e:
            logger.error(f"KNN training failed: {e}")
            raise
        
        # Train Random Forest
        logger.info("Training Random Forest")
        try:
            rf, rf_result = train_random_forest(X_train, y_train, logger, n_jobs=2)
            models['RandomForest'] = rf
            results['RandomForest'] = rf_result
        except Exception as e:
            logger.error(f"Random Forest training failed: {e}")
            raise
        
        # Train XGBoost
        logger.info("Training XGBoost")
        try:
            xgb, xgb_result = train_xgboost(X_train, y_train, logger, n_jobs=2)
            models['XGBoost'] = xgb
            results['XGBoost'] = xgb_result
        except Exception as e:
            logger.error(f"XGBoost training failed: {e}")
            raise
        
        # Save models
        output_dir = os.path.join(config['paths']['data_root'], 'processed', 'models')
        save_models(models, results, output_dir, logger)
        
        logger.info("Model training pipeline completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()