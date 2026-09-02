"""
Training module for Random Forest and SVM models with memory-bounded execution.

This module implements grid search hyperparameter optimization for RF and SVM
regressors while enforcing strict memory limits (< 7GB RAM) through batch processing
and streaming logic.
"""

import json
import logging
import os
import sys
import time
import gc
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Import from project utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.memory_profiler import (
    start_profiling, 
    stop_profiling, 
    get_peak_memory_mb, 
    check_memory_limit,
    force_gc,
    profile_training_block,
    save_memory_profile_log
)
from modeling.memory_utils import batch_dataframe, safe_gc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/training.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
BATCH_SIZE = 5000  # Rows per batch for processing

def load_and_prepare_data(data_path: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load and prepare data for training with memory-efficient streaming.
    
    Args:
        data_path: Path to the processed parquet file
        
    Returns:
        Tuple of (features, targets, feature_names)
    """
    logger.info(f"Loading data from {data_path}")
    
    # Check memory before loading
    check_memory_limit(MEMORY_LIMIT_GB)
    
    # Load data in chunks if file is large
    file_size_mb = os.path.getsize(data_path) / (1024 * 1024)
    logger.info(f"Data file size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 2000:  # If file is > 2GB, process in batches
        logger.info("Processing data in batches due to large file size")
        features_list = []
        targets_list = []
        
        # Read in chunks
        for chunk in pd.read_parquet(data_path, engine='pyarrow', chunksize=BATCH_SIZE):
            # Extract features (fingerprint columns)
            fingerprint_cols = [col for col in chunk.columns if col.startswith('fingerprint_')]
            target_col = 'yield'
            
            # Process batch
            X_batch = chunk[fingerprint_cols].to_numpy()
            y_batch = chunk[target_col].to_numpy()
            
            features_list.append(X_batch)
            targets_list.append(y_batch)
            
            # Clean up batch
            del chunk
            safe_gc()
            
            # Check memory periodically
            if len(features_list) % 10 == 0:
                current_mem = get_peak_memory_mb()
                logger.info(f"Processed {len(features_list) * BATCH_SIZE} rows, peak memory: {current_mem:.2f} MB")
                check_memory_limit(MEMORY_LIMIT_GB)
        
        # Concatenate all batches
        X = np.vstack(features_list)
        y = np.concatenate(targets_list)
        feature_names = fingerprint_cols
    else:
        # Load entire dataset at once
        df = pd.read_parquet(data_path)
        fingerprint_cols = [col for col in df.columns if col.startswith('fingerprint_')]
        target_col = 'yield'
        
        X = df[fingerprint_cols].to_numpy()
        y = df[target_col].to_numpy()
        feature_names = fingerprint_cols
        
        del df
        safe_gc()
    
    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features")
    return X, y, feature_names

def train_random_forest_grid_search(
    X: np.ndarray, 
    y: np.ndarray, 
    param_grid: Dict[str, Any],
    cv_folds: int = 5,
    n_jobs: int = -1
) -> Tuple[Any, Dict[str, Any], Dict[str, float]]:
    """
    Train Random Forest with grid search and memory profiling.
    
    Args:
        X: Feature matrix
        y: Target values
        param_grid: Hyperparameter grid for grid search
        cv_folds: Number of CV folds
        n_jobs: Number of parallel jobs
        
    Returns:
        Tuple of (best_model, best_params, metrics)
    """
    logger.info("Starting Random Forest grid search")
    
    # Memory profiling
    start_profiling()
    initial_mem = get_peak_memory_mb()
    logger.info(f"Initial memory before RF training: {initial_mem:.2f} MB")
    
    try:
        # Create model
        rf = RandomForestRegressor(
            random_state=42,
            n_jobs=n_jobs,
            verbose=1
        )
        
        # Setup grid search with memory-aware CV
        kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
        
        grid_search = GridSearchCV(
            estimator=rf,
            param_grid=param_grid,
            cv=kfold,
            scoring='r2',
            n_jobs=n_jobs,
            verbose=2,
            refit=True
        )
        
        # Train with memory monitoring
        logger.info("Beginning grid search...")
        grid_search.fit(X, y)
        
        # Get best model and params
        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        
        # Calculate metrics on training data (for validation)
        y_pred = best_model.predict(X)
        metrics = {
            'R2': float(r2_score(y, y_pred)),
            'RMSE': float(np.sqrt(mean_squared_error(y, y_pred))),
            'MAE': float(mean_absolute_error(y, y_pred))
        }
        
        logger.info(f"Best parameters: {best_params}")
        logger.info(f"Training metrics: {metrics}")
        
        # Memory profiling after training
        peak_mem = get_peak_memory_mb()
        logger.info(f"Peak memory during RF training: {peak_mem:.2f} MB")
        
        # Force garbage collection
        force_gc()
        
        return best_model, best_params, metrics
        
    except MemoryError:
        logger.error("MemoryError during Random Forest training")
        raise
    finally:
        stop_profiling()

def train_svm_grid_search(
    X: np.ndarray, 
    y: np.ndarray, 
    param_grid: Dict[str, Any],
    cv_folds: int = 5,
    n_jobs: int = -1
) -> Tuple[Any, Dict[str, Any], Dict[str, float]]:
    """
    Train SVM with grid search and memory profiling.
    
    Args:
        X: Feature matrix
        y: Target values
        param_grid: Hyperparameter grid for grid search
        cv_folds: Number of CV folds
        n_jobs: Number of parallel jobs
        
    Returns:
        Tuple of (best_model, best_params, metrics)
    """
    logger.info("Starting SVM grid search")
    
    # Memory profiling
    start_profiling()
    initial_mem = get_peak_memory_mb()
    logger.info(f"Initial memory before SVM training: {initial_mem:.2f} MB")
    
    try:
        # Create model
        svm = SVR()
        
        # Setup grid search
        kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
        
        grid_search = GridSearchCV(
            estimator=svm,
            param_grid=param_grid,
            cv=kfold,
            scoring='r2',
            n_jobs=n_jobs,
            verbose=2,
            refit=True
        )
        
        # Train with memory monitoring
        logger.info("Beginning SVM grid search...")
        grid_search.fit(X, y)
        
        # Get best model and params
        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        
        # Calculate metrics on training data
        y_pred = best_model.predict(X)
        metrics = {
            'R2': float(r2_score(y, y_pred)),
            'RMSE': float(np.sqrt(mean_squared_error(y, y_pred))),
            'MAE': float(mean_absolute_error(y, y_pred))
        }
        
        logger.info(f"Best parameters: {best_params}")
        logger.info(f"Training metrics: {metrics}")
        
        # Memory profiling after training
        peak_mem = get_peak_memory_mb()
        logger.info(f"Peak memory during SVM training: {peak_mem:.2f} MB")
        
        # Force garbage collection
        force_gc()
        
        return best_model, best_params, metrics
        
    except MemoryError:
        logger.error("MemoryError during SVM training")
        raise
    finally:
        stop_profiling()

def run_memory_profiling(
    data_path: str,
    output_dir: str = 'data/results'
) -> Dict[str, Any]:
    """
    Run full training pipeline with memory profiling.
    
    Args:
        data_path: Path to processed data
        output_dir: Directory for output files
        
    Returns:
        Dictionary containing profiling results
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Start profiling
    start_profiling()
    profiling_start_time = time.time()
    
    results = {
        'memory_profile': [],
        'runtime_profile': {},
        'peak_memory_mb': 0,
        'memory_limit_gb': MEMORY_LIMIT_GB,
        'status': 'running'
    }
    
    try:
        # Load data
        X, y, feature_names = load_and_prepare_data(data_path)
        
        # Define hyperparameter grids
        rf_param_grid = {
            'n_estimators': [50, 100],
            'max_depth': [10, 20, None]
        }
        
        svm_param_grid = {
            'C': [0.1, 1.0],
            'kernel': ['linear', 'rbf'],
            'gamma': ['scale', 'auto']
        }
        
        # Train Random Forest
        logger.info("=" * 50)
        logger.info("Training Random Forest")
        logger.info("=" * 50)
        
        rf_model, rf_params, rf_metrics = train_random_forest_grid_search(
            X, y, rf_param_grid, cv_folds=3, n_jobs=1  # Limit parallelism for memory
        )
        
        results['random_forest'] = {
            'best_params': rf_params,
            'metrics': rf_metrics,
            'model_type': 'RandomForest'
        }
        
        # Clear memory between models
        del X, y
        force_gc()
        
        # Reload data for SVM
        X, y, feature_names = load_and_prepare_data(data_path)
        
        # Train SVM
        logger.info("=" * 50)
        logger.info("Training SVM")
        logger.info("=" * 50)
        
        svm_model, svm_params, svm_metrics = train_svm_grid_search(
            X, y, svm_param_grid, cv_folds=3, n_jobs=1
        )
        
        results['svm'] = {
            'best_params': svm_params,
            'metrics': svm_metrics,
            'model_type': 'SVM'
        }
        
        # Final memory check
        final_peak_mem = get_peak_memory_mb()
        results['peak_memory_mb'] = final_peak_mem
        results['memory_limit_gb'] = MEMORY_LIMIT_GB
        
        # Check memory limit
        if final_peak_mem > MEMORY_LIMIT_MB:
            results['status'] = 'failed_memory_limit'
            logger.error(f"Peak memory {final_peak_mem:.2f} MB exceeds limit {MEMORY_LIMIT_MB:.2f} MB")
        else:
            results['status'] = 'success'
            logger.info(f"Memory limit satisfied: {final_peak_mem:.2f} MB < {MEMORY_LIMIT_MB:.2f} MB")
        
        # Calculate runtime
        profiling_end_time = time.time()
        results['runtime_profile'] = {
            'total_runtime_seconds': profiling_end_time - profiling_start_time,
            'peak_memory_mb': final_peak_mem,
            'memory_limit_gb': MEMORY_LIMIT_GB,
            'memory_limit_exceeded': final_peak_mem > MEMORY_LIMIT_MB
        }
        
        # Save memory profile log
        log_path = output_path / 'memory_profile.log'
        save_memory_profile_log(str(log_path))
        
        # Save runtime profile
        runtime_path = output_path / 'runtime_profile.json'
        with open(runtime_path, 'w') as f:
            json.dump(results['runtime_profile'], f, indent=2)
        
        logger.info(f"Memory profile saved to {log_path}")
        logger.info(f"Runtime profile saved to {runtime_path}")
        
        # Save full results
        full_results_path = output_path / 'training_results.json'
        with open(full_results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
        
    except Exception as e:
        logger.error(f"Error during profiling: {str(e)}")
        results['status'] = 'failed'
        results['error'] = str(e)
        raise
    finally:
        stop_profiling()
        force_gc()

def main():
    """Main entry point for training with memory profiling."""
    logger.info("Starting memory-bounded training pipeline")
    
    # Configuration
    data_path = 'data/processed/cleaned_reactions.parquet'
    output_dir = 'data/results'
    
    # Verify data exists
    if not Path(data_path).exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    # Run profiling
    results = run_memory_profiling(data_path, output_dir)
    
    # Print summary
    logger.info("=" * 50)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Status: {results['status']}")
    logger.info(f"Peak Memory: {results['peak_memory_mb']:.2f} MB")
    logger.info(f"Memory Limit: {results['memory_limit_gb']} GB")
    logger.info(f"Memory Limit Exceeded: {results['runtime_profile']['memory_limit_exceeded']}")
    
    if results['status'] == 'success':
        logger.info("Training completed successfully within memory limits")
    else:
        logger.error("Training failed or exceeded memory limits")
        sys.exit(1)

if __name__ == '__main__':
    main()
