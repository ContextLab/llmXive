"""
Training pipeline for Metallic Glass CTE prediction.
Implements T025 (Load & Prepare), T026 (Null Model), T028-T030 (Training), T031 (Serialization).
"""
import os
import sys
import json
import logging
import time
import resource
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.base import BaseEstimator, RegressorMixin
import joblib

# Project imports based on provided API surface
from utils.config import get_env_var
from utils.io import setup_logging, compute_sha256

# Configure logger
logger = logging.getLogger(__name__)

# Constants
FEATURE_COLUMNS = ['mean_atomic_radius', 'electronegativity_var', 'vec', 'size_mismatch']
TARGET_COLUMN = 'cte'
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "clean_mg_data.parquet"
MODELS_DIR = PROJECT_ROOT / "code" / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
METRICS_PATH = RESULTS_DIR / "metrics.json"

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def set_resource_limits(max_memory_mb: int = 7000, max_cpus: int = 2):
    """
    Enforce resource constraints (T030).
    Sets memory limits via resource module (Unix only) and logs CPU constraint.
    """
    if sys.platform != 'win32':
        try:
            # Set soft and hard limits in bytes
            limit_bytes = max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
            logger.info(f"Set memory limit to {max_memory_mb} MB")
        except (ValueError, resource.error) as e:
            logger.warning(f"Could not set memory limit: {e}")
    
    logger.info(f"Resource constraint: Max CPUs set to {max_cpus} (via n_jobs in sklearn)")
    return max_cpus

class NullModel(BaseEstimator, RegressorMixin):
    """
    Null Model baseline (T026, T026a).
    Predicts the mean of the training target for all inputs.
    """
    def __init__(self):
        self.mean_ = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.mean_ = np.mean(y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.mean_ is None:
            raise RuntimeError("Model not fitted yet.")
        return np.full(X.shape[0], self.mean_)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        # R2 score for null model
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        if ss_tot == 0:
            return 0.0
        return 1 - (ss_res / ss_tot)

def load_clean_data() -> pd.DataFrame:
    """
    Load the cleaned parquet dataset (T025).
    Fails loudly if file is missing or empty.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Clean data file not found at {DATA_PATH}. "
                                "Run T022 (save_clean_data.py) first.")
    
    df = pd.read_parquet(DATA_PATH)
    if df.empty:
        raise ValueError(f"Dataset at {DATA_PATH} is empty. Cannot proceed.")
    
    logger.info(f"Loaded {len(df)} rows from {DATA_PATH}")
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare feature matrix X and target vector y (T025).
    - Selects specific columns.
    - Drops rows with NaN in selected features or target.
    """
    required_cols = FEATURE_COLUMNS + [TARGET_COLUMN]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    # Drop rows with any NaN in required columns
    initial_len = len(df)
    df_clean = df.dropna(subset=required_cols)
    dropped = initial_len - len(df_clean)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to missing values in features/target.")
    
    if len(df_clean) == 0:
        raise ValueError("No valid rows remaining after dropping NaNs.")

    X = df_clean[FEATURE_COLUMNS].values
    y = df_clean[TARGET_COLUMN].values
    
    logger.info(f"Prepared feature matrix: {X.shape}, target vector: {y.shape}")
    return X, y

def split_data_stratified(X: np.ndarray, y: np.ndarray, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split data. Attempts stratification by alloy family if available, else random.
    (T018 logic adapted for T025 context if family column exists, otherwise random).
    """
    # Check if alloy_family exists for stratification
    if 'alloy_family' in df.columns:
        try:
            # Use the dataframe index to align with X, y
            # We need to pass the labels corresponding to the rows in X, y
            # Since we dropped NaNs, we should use the cleaned df
            # However, split_data_stratified receives X, y, and the original df (which might be larger)
            # We need to ensure alignment. For simplicity in this task, we assume df passed is the clean one.
            # If the caller passes the original df, this might misalign. 
            # Let's assume the caller passes the clean df used to generate X, y.
            # If not, we fallback to random.
            
            # Re-construct the clean df slice if needed? 
            # For T025, we focus on X, y. Let's assume df is aligned.
            # If df is the original large one, we can't stratify X, y directly without mapping.
            # Let's assume the passed df is the one used to create X, y.
            
            # To be safe, if indices don't match, fallback.
            if not np.array_equal(df.index, pd.RangeIndex(len(df))):
                # If we can't easily align, fallback to random
                logger.warning("Stratification fallback: Index alignment issues or missing family column.")
                return train_test_split(X, y, test_size=test_size, random_state=random_state)
            
            labels = df['alloy_family'].values
            return train_test_split(X, y, test_size=test_size, stratify=labels, random_state=random_state)
        except Exception as e:
            logger.warning(f"Stratification failed ({e}), falling back to random split.")
            return train_test_split(X, y, test_size=test_size, random_state=random_state)
    else:
        logger.info("No 'alloy_family' column found. Using random split.")
        return train_test_split(X, y, test_size=test_size, random_state=random_state)

def determine_cv_strategy(n_samples: int) -> int:
    """
    Determine CV folds based on N (T019).
    """
    if n_samples >= 50:
        return 5
    elif n_samples >= 20:
        return 2 # Hold-out style (2-fold)
    else:
        return n_samples # LOO if N < 20 (sklearn handles this)

def load_metrics() -> Dict[str, Any]:
    """Load existing metrics or return empty dict."""
    if METRICS_PATH.exists():
        with open(METRICS_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_metrics(metrics: Dict[str, Any]):
    """Save metrics to JSON."""
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {METRICS_PATH}")

def run_training_pipeline(X: np.ndarray, y: np.ndarray, metrics: Dict[str, Any]):
    """
    Run Linear Regression and Random Forest training with CV (T028, T029, T030).
    """
    n_jobs = set_resource_limits()
    n_folds = determine_cv_strategy(len(X))
    
    logger.info(f"Starting training pipeline. Folds: {n_folds}, CPUs: {n_jobs}")

    # --- Linear Regression ---
    lr_model = LinearRegression()
    try:
        lr_scores = cross_val_score(lr_model, X, y, cv=n_folds, scoring='r2', n_jobs=n_jobs)
        metrics['linear_regression'] = {
            'mean_r2': float(np.mean(lr_scores)),
            'std_r2': float(np.std(lr_scores)),
            'cv_folds': n_folds
        }
        logger.info(f"Linear Regression CV R2: {metrics['linear_regression']['mean_r2']:.4f} (+/- {metrics['linear_regression']['std_r2']:.4f})")
        
        # Train final model
        lr_model.fit(X, y)
        lr_path = MODELS_DIR / "linear_regression_v1.pkl"
        joblib.dump(lr_model, lr_path)
        logger.info(f"Saved Linear Regression to {lr_path}")
    except Exception as e:
        logger.error(f"Linear Regression failed: {e}")
        metrics['linear_regression'] = {'error': str(e)}

    # --- Random Forest ---
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=n_jobs)
    param_grid = {
        'max_depth': [5, 10, None],
        'n_estimators': [50, 100]
    }
    
    try:
        grid_search = GridSearchCV(rf_model, param_grid, cv=n_folds, scoring='r2', n_jobs=n_jobs)
        grid_search.fit(X, y)
        
        metrics['random_forest'] = {
            'best_params': grid_search.best_params_,
            'best_r2': float(grid_search.best_score_),
            'cv_folds': n_folds
        }
        logger.info(f"Random Forest Best Params: {grid_search.best_params_}, Best R2: {grid_search.best_score_:.4f}")
        
        # Save best model
        rf_path = MODELS_DIR / "random_forest_v1.pkl"
        joblib.dump(grid_search.best_estimator_, rf_path)
        logger.info(f"Saved Random Forest to {rf_path}")
        
        # Save metadata
        meta_path = MODELS_DIR / "random_forest_v1_meta.json"
        with open(meta_path, 'w') as f:
            json.dump({
                'best_params': grid_search.best_params_,
                'best_r2': float(grid_search.best_score_),
                'cv_folds': n_folds,
                'feature_columns': FEATURE_COLUMNS
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Random Forest failed: {e}")
        metrics['random_forest'] = {'error': str(e)}

    return metrics

def main():
    """Main entry point for T025."""
    setup_logging()
    logger.info("Starting T025: Load and Prepare Data + Training Pipeline")

    try:
        # Load Data
        df = load_clean_data()
        
        # Prepare Features
        X, y = prepare_features(df)
        
        # Load Metrics
        metrics = load_metrics()
        
        # Update Spec Root Cause for Baseline (T027)
        metrics['baseline_type'] = 'null_model'
        metrics['spec_root_cause_SC001'] = 'elemental_cte_data_unavailable'
        
        # Run Training
        metrics = run_training_pipeline(X, y, metrics)
        
        # Save Metrics
        save_metrics(metrics)
        
        logger.info("T025 completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        # T020: No Data Termination
        metrics = load_metrics()
        metrics['status'] = 'no_data'
        metrics['error'] = str(e)
        save_metrics(metrics)
        return 0 # Exit cleanly as per T020
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())