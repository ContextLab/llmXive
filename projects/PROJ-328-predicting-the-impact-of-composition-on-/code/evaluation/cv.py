"""
Cross-validation module for solder hardness prediction models.

Implements k-fold cross-validation for both XGBoost and Linear Regression models,
computing metrics (R², RMSE) for each fold and aggregating results.
"""

import os
import sys
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union

from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error, make_scorer
from sklearn.base import clone

# Import from project modules
from config import get_data_processed_dir, get_models_dir, get_cv_folds, get_log_level, get_log_format
from utils.logging_config import get_logger
from seed import init_reproducibility
from models.linear_trainer import LinearRegressionTrainer
from models.xgboost_trainer import XGBoostTrainer

# Initialize logger
logger = get_logger(__name__)

def calculate_fold_metrics(
    y_true: np.ndarray, 
    y_pred: np.ndarray
) -> Dict[str, float]:
    """
    Calculate metrics for a single fold.
    
    Args:
        y_true: True target values
        y_pred: Predicted target values
        
    Returns:
        Dictionary with R² and RMSE metrics
    """
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    return {
        'r2': float(r2),
        'rmse': float(rmse)
    }

def run_kfold_cv(
    X: np.ndarray,
    y: np.ndarray,
    model: Any,
    model_name: str,
    n_folds: Optional[int] = None,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run k-fold cross-validation on a given model.
    
    Args:
        X: Feature matrix
        y: Target vector
        model: Scikit-learn compatible model instance
        model_name: Name of the model for logging
        n_folds: Number of folds (defaults to config)
        random_state: Random state for reproducibility
        
    Returns:
        Dictionary containing fold results and aggregated metrics
    """
    if n_folds is None:
        n_folds = get_cv_folds()
    
    logger.info(f"Running {n_folds}-fold cross-validation for {model_name}")
    
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    fold_results = []
    all_r2 = []
    all_rmse = []
    
    for fold_idx, (train_idx, val_idx) in enumerate(kf.split(X)):
        logger.debug(f"Processing fold {fold_idx + 1}/{n_folds}")
        
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        # Clone model to ensure fresh state for each fold
        fold_model = clone(model)
        
        # Train the model
        try:
            fold_model.fit(X_train, y_train)
        except Exception as e:
            logger.error(f"Error training {model_name} on fold {fold_idx + 1}: {e}")
            raise
        
        # Predict on validation set
        y_pred = fold_model.predict(X_val)
        
        # Calculate metrics
        metrics = calculate_fold_metrics(y_val, y_pred)
        
        fold_result = {
            'fold': fold_idx + 1,
            'r2': metrics['r2'],
            'rmse': metrics['rmse'],
            'n_train': len(y_train),
            'n_val': len(y_val)
        }
        fold_results.append(fold_result)
        
        all_r2.append(metrics['r2'])
        all_rmse.append(metrics['rmse'])
    
    # Calculate aggregated metrics
    aggregated = {
        'model_name': model_name,
        'n_folds': n_folds,
        'mean_r2': float(np.mean(all_r2)),
        'std_r2': float(np.std(all_r2)),
        'mean_rmse': float(np.mean(all_rmse)),
        'std_rmse': float(np.std(all_rmse)),
        'fold_results': fold_results
    }
    
    logger.info(f"{model_name} CV Results: R² = {aggregated['mean_r2']:.4f} ± {aggregated['std_r2']:.4f}, "
               f"RMSE = {aggregated['mean_rmse']:.4f} ± {aggregated['std_rmse']:.4f}")
    
    return aggregated

def run_cross_validation_for_all_models(
    X: np.ndarray,
    y: np.ndarray,
    random_state: Optional[int] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Run cross-validation for both XGBoost and Linear Regression models.
    
    Args:
        X: Feature matrix
        y: Target vector
        random_state: Random state for reproducibility
        
    Returns:
        Dictionary with CV results for each model
    """
    init_reproducibility(random_state)
    
    results = {}
    
    # Run for Linear Regression
    logger.info("Starting cross-validation for Linear Regression")
    linear_trainer = LinearRegressionTrainer()
    # Get the base estimator from the trainer
    linear_model = linear_trainer._get_model()
    linear_results = run_kfold_cv(
        X, y, linear_model, "LinearRegression", 
        n_folds=get_cv_folds(), random_state=random_state
    )
    results['LinearRegression'] = linear_results
    
    # Run for XGBoost
    logger.info("Starting cross-validation for XGBoost")
    xgb_trainer = XGBoostTrainer()
    # Get the base estimator from the trainer (using best params or default)
    xgb_model = xgb_trainer._get_model()
    xgb_results = run_kfold_cv(
        X, y, xgb_model, "XGBoost", 
        n_folds=get_cv_folds(), random_state=random_state
    )
    results['XGBoost'] = xgb_results
    
    return results

def save_cv_results(results: Dict[str, Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Save cross-validation results to a JSON file.
    
    Args:
        results: Dictionary of CV results from run_cross_validation_for_all_models
        output_path: Optional output path (defaults to models directory)
        
    Returns:
        Path to the saved file
    """
    if output_path is None:
        output_path = get_models_dir() / "cv_results.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Cross-validation results saved to {output_path}")
    return output_path

def load_cv_results(input_path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load cross-validation results from a JSON file.
    
    Args:
        input_path: Optional input path (defaults to models directory)
        
    Returns:
        Dictionary of CV results
    """
    if input_path is None:
        input_path = get_models_dir() / "cv_results.json"
    
    if not input_path.exists():
        raise FileNotFoundError(f"CV results file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        return json.load(f)

def main():
    """
    Main entry point for running cross-validation.
    
    Loads the validated dataset, runs CV for both models, and saves results.
    """
    # Initialize reproducibility
    init_reproducibility()
    
    # Load validated data
    data_dir = get_data_processed_dir()
    data_path = data_dir / "solder_hardness_validated.csv"
    
    if not data_path.exists():
        logger.error(f"Validated data not found at {data_path}. "
                    "Please run the ingestion pipeline first (T016).")
        sys.exit(1)
    
    logger.info(f"Loading validated data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Identify feature columns (all numeric except target)
    # Assuming 'Vickers_Hardness' is the target column based on context
    target_col = 'Vickers_Hardness'
    if target_col not in df.columns:
        # Try to find a similar column name
        possible_targets = [col for col in df.columns if 'hardness' in col.lower()]
        if possible_targets:
            target_col = possible_targets[0]
            logger.warning(f"Using '{target_col}' as target column")
        else:
            logger.error(f"Target column '{target_col}' not found in data. "
                        f"Available columns: {list(df.columns)}")
            sys.exit(1)
    
    # Get feature columns (exclude target and non-numeric)
    feature_cols = [col for col in df.columns if col != target_col and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if len(feature_cols) == 0:
        logger.error("No feature columns found in the dataset.")
        sys.exit(1)
    
    logger.info(f"Using {len(feature_cols)} feature columns for training")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Handle missing values if any
    if np.any(np.isnan(X)) or np.any(np.isnan(y)):
        logger.warning("NaN values detected. Dropping rows with missing values.")
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        logger.info(f"Remaining samples after dropping NaN: {len(y)}")
    
    if len(y) < get_cv_folds():
        logger.error(f"Insufficient samples ({len(y)}) for {get_cv_folds()}-fold cross-validation.")
        sys.exit(1)
    
    # Run cross-validation
    cv_results = run_cross_validation_for_all_models(X, y)
    
    # Save results
    output_path = save_cv_results(cv_results)
    
    logger.info("Cross-validation completed successfully.")
    return cv_results

if __name__ == "__main__":
    main()