"""
Modeling module for US3: Regression Modeling and Validation.

Implements stratified split, model training, cross-validation, and validation checks.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import (
    train_test_split, 
    RepeatedStratifiedKFold, 
    cross_val_score,
    StratifiedKFold
)
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.utils.validation import check_is_fitted

# Import local utilities and config
from env_config import get_processed_data_path, get_reports_path, get_state_path, ensure_dirs, setup_logger
from utils import PipelineError, DataIntegrityError, setup_logger as utils_setup_logger
from utils.metrics import calculate_mae, calculate_rmse, calculate_r2, bootstrap_confidence_interval

# Setup logging
logger = setup_logger(__name__)

# Constants
TARGET_COLUMN = "yield_strength"
RANDOM_STATE = 42
N_FOLDS = 5
N_REPEATS = 3
BOOTSTRAP_RESAMPLES = 100

def load_split_data(split_type: str) -> pd.DataFrame:
    """
    Load the train or test split from the processed data directory.
    
    Args:
        split_type: Either 'train' or 'test'
        
    Returns:
        DataFrame containing the split data.
        
    Raises:
        FileNotFoundError: If the split file does not exist.
        PipelineError: If the split type is invalid.
    """
    if split_type not in ['train', 'test']:
        raise PipelineError(f"Invalid split_type: {split_type}. Must be 'train' or 'test'.")
    
    file_path = get_processed_data_path() / f"{split_type}_split.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Split file not found: {file_path}")
    
    logger.info(f"Loading {split_type} split from {file_path}")
    return pd.read_csv(file_path)

def validate_split_integrity(df: pd.DataFrame, split_name: str, min_samples_per_bin: int = 1) -> None:
    """
    Pre-flight check to verify that the split contains at least min_samples_per_bin 
    samples per class/bin before attempting CV.
    
    This satisfies T047 requirement: verify train/test splits have sufficient data 
    distribution before CV.
    
    Args:
        df: The DataFrame to validate.
        split_name: Name of the split (e.g., 'train', 'test') for logging.
        min_samples_per_bin: Minimum number of samples required per bin/class.
        
    Raises:
        DataIntegrityError: If any bin has fewer than min_samples_per_bin samples.
    """
    if df.empty:
        raise DataIntegrityError(f"Split '{split_name}' is empty. Cannot proceed with modeling.")
    
    # We need to check the distribution of the target variable.
    # Since yield_strength is continuous, we bin it into quantiles to simulate classes 
    # for stratification purposes, matching the logic in T033_impl.
    if TARGET_COLUMN not in df.columns:
        raise DataIntegrityError(f"Target column '{TARGET_COLUMN}' not found in {split_name} split.")
    
    target_values = df[TARGET_COLUMN].dropna()
    
    if len(target_values) == 0:
        raise DataIntegrityError(f"No valid target values in {split_name} split.")
    
    # Determine number of bins based on sample size (at least 5, max 10)
    n_bins = min(10, max(5, len(target_values) // 10))
    
    # Create bins
    try:
        bins = pd.qcut(target_values, q=n_bins, duplicates='drop')
    except ValueError:
        # Fallback to equal width if quantiles fail (e.g., too many duplicates)
        bins = pd.cut(target_values, bins=n_bins)
    
    value_counts = bins.value_counts()
    
    min_count = value_counts.min()
    min_bin_label = value_counts.idxmin()
    
    logger.info(f"Validation for {split_name} split: Min samples per bin = {min_count} (Bin: {min_bin_label})")
    
    if min_count < min_samples_per_bin:
        raise DataIntegrityError(
            f"Data integrity check failed for {split_name} split: "
            f"Bin '{min_bin_label}' has only {min_count} sample(s), "
            f"which is less than the required minimum of {min_samples_per_bin}. "
            f"Cannot proceed with Cross-Validation."
        )
    
    logger.info(f"Validation passed for {split_name} split.")

def perform_stratified_split(df: pd.DataFrame, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified train-test split based on quantile bins of yield strength.
    
    Note: This function is provided for completeness if splits don't exist, 
    but the primary flow loads existing splits from T033_impl.
    """
    if TARGET_COLUMN not in df.columns:
        raise PipelineError(f"Target column '{TARGET_COLUMN}' missing for splitting.")
    
    # Create stratification labels
    n_bins = min(10, max(5, len(df) // 10))
    try:
        strat_labels = pd.qcut(df[TARGET_COLUMN], q=n_bins, labels=False, duplicates='drop')
    except ValueError:
        strat_labels = pd.cut(df[TARGET_COLUMN], bins=n_bins, labels=False)
    
    train_df, test_df = train_test_split(
        df, 
        test_size=test_size, 
        random_state=RANDOM_STATE, 
        stratify=strat_labels
    )
    
    return train_df, test_df

def train_models(X: np.ndarray, y: np.ndarray, cv) -> Dict[str, Any]:
    """
    Train Random Forest, Gradient Boosting, and Ridge Regression models.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        cv: Cross-validation splitter.
        
    Returns:
        Dictionary containing trained models and their CV scores.
    """
    models = {
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=100, random_state=RANDOM_STATE),
        "Ridge": Ridge(alpha=1.0)
    }
    
    results = {}
    
    for name, model in models.items():
        logger.info(f"Training {name}...")
        try:
            scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
            results[name] = {
                "model": model,
                "cv_scores": scores.tolist(),
                "mean_r2": float(scores.mean()),
                "std_r2": float(scores.std())
            }
            logger.info(f"{name} Mean R²: {scores.mean():.4f} (+/- {scores.std():.4f})")
        except Exception as e:
            logger.error(f"Error training {name}: {e}")
            raise
    
    return results

def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate a trained model on the test set.
    
    Args:
        model: Trained sklearn model.
        X_test: Test features.
        y_test: Test targets.
        
    Returns:
        Dictionary of metrics (R², MAE, RMSE).
    """
    y_pred = model.predict(X_test)
    return {
        "r2": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }

def main():
    """
    Main entry point for the modeling pipeline (US3).
    
    1. Loads train and test splits.
    2. Performs pre-flight integrity checks (T047).
    3. Trains models with CV.
    4. Evaluates on test set.
    5. Saves results.
    """
    ensure_dirs()
    logger.info("Starting Modeling Pipeline (US3)...")
    
    try:
        # Step 1: Load splits
        logger.info("Loading train and test splits...")
        train_df = load_split_data('train')
        test_df = load_split_data('test')
        
        # Step 2: Pre-flight check (T047)
        # Verify that splits have at least 1 sample per bin before CV
        logger.info("Running pre-flight integrity checks (T047)...")
        validate_split_integrity(train_df, "train", min_samples_per_bin=1)
        validate_split_integrity(test_df, "test", min_samples_per_bin=1)
        
        # Prepare data
        X_train = train_df.drop(columns=[TARGET_COLUMN]).values
        y_train = train_df[TARGET_COLUMN].values
        X_test = test_df.drop(columns=[TARGET_COLUMN]).values
        y_test = test_df[TARGET_COLUMN].values
        
        if len(X_train) == 0 or len(X_test) == 0:
            raise DataIntegrityError("Train or Test set is empty after feature selection.")
        
        # Step 3: Setup CV
        # Repeated Stratified K-Fold
        strat_kf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
        
        # Create stratification labels for CV based on train targets
        n_bins_cv = min(10, max(5, len(y_train) // 10))
        try:
            cv_strat_labels = pd.qcut(y_train, q=n_bins_cv, labels=False, duplicates='drop')
        except ValueError:
            cv_strat_labels = pd.cut(y_train, bins=n_bins_cv, labels=False)
        
        cv = RepeatedStratifiedKFold(
            n_splits=N_FOLDS, 
            n_repeats=N_REPEATS, 
            random_state=RANDOM_STATE,
            stratify=cv_strat_labels
        )
        
        # Step 4: Train models
        logger.info("Training models with Repeated Stratified K-Fold CV...")
        model_results = train_models(X_train, y_train, cv)
        
        # Step 5: Evaluate best model (or all) on test set
        # For simplicity, we evaluate all and report
        evaluation_results = {}
        for name, res in model_results.items():
            metrics = evaluate_model(res["model"], X_test, y_test)
            evaluation_results[name] = metrics
            logger.info(f"{name} Test Metrics: R²={metrics['r2']:.4f}, MAE={metrics['mae']:.4f}, RMSE={metrics['rmse']:.4f}")
        
        # Step 6: Save results
        report_path = get_reports_path() / "model_comparison_report.json"
        report_data = {
            "cv_results": {k: {kk: vv for kk, vv in v.items() if kk != "model"} for k, v in model_results.items()},
            "test_evaluation": evaluation_results,
            "metadata": {
                "n_train": len(X_train),
                "n_test": len(X_test),
                "random_state": RANDOM_STATE,
                "n_folds": N_FOLDS,
                "n_repeats": N_REPEATS
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Model comparison report saved to {report_path}")
        logger.info("Modeling pipeline completed successfully.")
        
    except DataIntegrityError as e:
        logger.error(f"Data Integrity Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File Not Found Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in modeling pipeline: {e}")
        raise

if __name__ == "__main__":
    main()