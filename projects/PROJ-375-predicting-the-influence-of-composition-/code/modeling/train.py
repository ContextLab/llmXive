"""
Training pipeline for Metallic Glass CTE prediction.

This module implements T025: Load clean data, prepare feature matrix,
and split data for model training.
"""
import os
import sys
import json
import logging
import time
import resource
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, KFold
from sklearn.metrics import r2_score, mean_absolute_error

# Project imports based on API surface
from utils.config import get_env_var
from utils.io import setup_logging, compute_sha256, fail_loud_loader
from features.dataset_models import validate_dataframe_schema

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logging()

# Feature columns required for T025
REQUIRED_FEATURES = [
    "mean_atomic_radius",
    "electronegativity_var",
    "vec",
    "size_mismatch"
]
TARGET_COLUMN = "cte"

def set_resource_limits(n_jobs: int = 2, memory_limit_mb: int = 7000) -> None:
    """
    Enforce resource constraints: n_jobs and memory limit.
    """
    logger.info(f"Setting resource limits: n_jobs={n_jobs}, memory_limit={memory_limit_mb}MB")
    # Note: n_jobs is handled by sklearn estimators, not here.
    # Memory limit is enforced via resource module on Unix.
    if sys.platform != "win32":
        try:
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit_mb * 1024 * 1024, memory_limit_mb * 1024 * 1024))
            logger.info(f"Memory limit set to {memory_limit_mb}MB")
        except (ValueError, resource.error) as e:
            logger.warning(f"Could not set memory limit: {e}")

class NullModel:
    """
    Baseline model that predicts the mean of the training target.
    """
    def __init__(self):
        self.mean_cte = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "NullModel":
        self.mean_cte = np.mean(y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.mean_cte is None:
            raise ValueError("Model not fitted. Call fit() first.")
        return np.full(X.shape[0], self.mean_cte)

def load_clean_data(filepath: str) -> pd.DataFrame:
    """
    Load the cleaned metallic glass dataset from parquet.
    
    Args:
        filepath: Path to the parquet file.
        
    Returns:
        DataFrame with cleaned data.
        
    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If schema validation fails.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Clean data file not found: {filepath}")
    
    logger.info(f"Loading clean data from {filepath}")
    df = pd.read_parquet(path)
    
    # Validate schema
    required_cols = REQUIRED_FEATURES + [TARGET_COLUMN]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare feature matrix X and target vector y.
    
    - Selects required feature columns.
    - Drops rows with any NaN values in features or target.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Tuple of (X, y) as numpy arrays.
    """
    logger.info("Preparing feature matrix and target vector")
    
    # Select columns
    feature_cols = REQUIRED_FEATURES
    target_col = TARGET_COLUMN
    
    # Check for NaNs
    initial_len = len(df)
    mask = df[feature_cols + [target_col]].notna().all(axis=1)
    df_clean = df[mask].copy()
    
    dropped = initial_len - len(df_clean)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to missing values in features or target.")
    
    if len(df_clean) == 0:
        raise ValueError("No valid data remaining after dropping NaNs.")
        
    X = df_clean[feature_cols].values
    y = df_clean[target_col].values
    
    logger.info(f"Prepared X shape: {X.shape}, y shape: {y.shape}")
    return X, y

def split_data_stratified(X: np.ndarray, y: np.ndarray, 
                          df: pd.DataFrame, 
                          test_size: float = 0.2,
                          random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split data into train and test sets.
    
    Attempts stratified split by 'alloy_family' if available, otherwise random split.
    """
    logger.info("Splitting data into train and test sets")
    
    # Check if alloy_family exists for stratification
    if "alloy_family" in df.columns and len(df["alloy_family"].unique()) > 1:
        try:
            # Map to indices to keep alignment
            df_split = df.reset_index(drop=True)
            X_df = pd.DataFrame(X, columns=REQUIRED_FEATURES)
            y_df = pd.Series(y)
            
            # Re-align
            X_train, X_test, y_train, y_test = train_test_split(
                X_df.values, y_df.values,
                test_size=test_size,
                random_state=random_state,
                stratify=df_split["alloy_family"]
            )
            logger.info("Split data using stratification by alloy_family")
        except Exception as e:
            logger.warning(f"Stratification failed ({e}), falling back to random split")
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
    else:
        logger.info("No alloy_family column or insufficient classes; using random split")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
    logger.info(f"Train set: {X_train.shape}, Test set: {X_test.shape}")
    return X_train, X_test, y_train, y_test

def determine_cv_strategy(n_samples: int) -> Any:
    """
    Determine cross-validation strategy based on sample size.
    
    - N >= 50: 5-fold
    - 20 <= N < 50: Hold-Out (simulated via train_test_split logic later)
    - N < 20: Leave-One-Out (not implemented here, just returns KFold(1) as placeholder)
    """
    if n_samples >= 50:
        logger.info(f"Using 5-fold CV (N={n_samples})")
        return KFold(n_splits=5, shuffle=True, random_state=42)
    elif n_samples >= 20:
        logger.info(f"Using Hold-Out strategy (N={n_samples})")
        return None # Handled in training logic
    else:
        logger.warning(f"Using minimal CV strategy (N={n_samples})")
        return KFold(n_splits=1, shuffle=False)

def load_metrics(filepath: str) -> Dict[str, Any]:
    """Load existing metrics file if it exists."""
    path = Path(filepath)
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_metrics(metrics: Dict[str, Any], filepath: str) -> None:
    """Save metrics to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {filepath}")

def run_training_pipeline(X_train: np.ndarray, y_train: np.ndarray,
                          X_test: np.ndarray, y_test: np.ndarray,
                          metrics_path: str) -> Dict[str, Any]:
    """
    Run the training pipeline including Null Model baseline.
    
    Implements T026, T026a, T027, T028, T029, T030.
    """
    logger.info("Starting training pipeline")
    
    metrics = load_metrics(metrics_path)
    
    # 1. Null Model Baseline (T026, T026a, T027)
    logger.info("Training Null Model baseline")
    null_model = NullModel()
    null_model.fit(X_train, y_train)
    y_pred_null = null_model.predict(X_test)
    
    null_r2 = r2_score(y_test, y_pred_null)
    null_mae = mean_absolute_error(y_test, y_pred_null)
    
    logger.info(f"Null Model - R2: {null_r2:.4f}, MAE: {null_mae:.4f}")
    
    # Record Spec-Root Cause for SC-001
    metrics["baseline_type"] = "null_model"
    metrics["spec_root_cause_SC001"] = "elemental_cte_data_unavailable"
    metrics["null_model_r2"] = null_r2
    metrics["null_model_mae"] = null_mae
    
    # 2. Linear Regression (T028)
    from sklearn.linear_model import LinearRegression
    logger.info("Training Linear Regression")
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred_lr = lr.predict(X_test)
    
    lr_r2 = r2_score(y_test, y_pred_lr)
    lr_mae = mean_absolute_error(y_test, y_pred_lr)
    
    logger.info(f"Linear Regression - R2: {lr_r2:.4f}, MAE: {lr_mae:.4f}")
    metrics["linear_regression_r2"] = lr_r2
    metrics["linear_regression_mae"] = lr_mae
    
    # 3. Random Forest (T029, T030)
    from sklearn.ensemble import RandomForestRegressor
    logger.info("Training Random Forest with n_jobs=2")
    rf = RandomForestRegressor(
        n_estimators=100, 
        max_depth=10, 
        n_jobs=2, 
        random_state=42
    )
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    
    rf_r2 = r2_score(y_test, y_pred_rf)
    rf_mae = mean_absolute_error(y_test, y_pred_rf)
    
    logger.info(f"Random Forest - R2: {rf_r2:.4f}, MAE: {rf_mae:.4f}")
    metrics["random_forest_r2"] = rf_r2
    metrics["random_forest_mae"] = rf_mae
    metrics["random_forest_n_jobs"] = 2
    
    # Save metrics
    save_metrics(metrics, metrics_path)
    
    return {
        "null": {"r2": null_r2, "mae": null_mae},
        "linear": {"r2": lr_r2, "mae": lr_mae},
        "random_forest": {"r2": rf_r2, "mae": rf_mae}
    }

def main():
    """
    Main entry point for T025.
    Loads clean data, prepares features, splits data, and runs training.
    """
    start_time = time.time()
    
    # Set resource limits
    set_resource_limits(n_jobs=2, memory_limit_mb=7000)
    
    # Paths
    clean_data_path = PROCESSED_DIR / "clean_mg_data.parquet"
    metrics_path = RESULTS_DIR / "metrics.json"
    
    try:
        # 1. Load Data (T025)
        df = load_clean_data(str(clean_data_path))
        
        # 2. Prepare Features (T025)
        X, y = prepare_features(df)
        
        # 3. Split Data
        X_train, X_test, y_train, y_test = split_data_stratified(X, y, df)
        
        # 4. Run Training Pipeline
        results = run_training_pipeline(X_train, y_train, X_test, y_test, str(metrics_path))
        
        # 5. Efficiency Check (T047)
        end_time = time.time()
        runtime = end_time - start_time
        if sys.platform != "win32":
            peak_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 # KB to MB
        else:
            peak_mem = 0
            
        logger.info(f"Pipeline completed in {runtime:.2f}s, Peak Memory: {peak_mem:.2f}MB")
        
        # Update metrics with efficiency
        metrics = load_metrics(str(metrics_path))
        metrics["runtime_seconds"] = runtime
        metrics["peak_memory_mb"] = peak_mem
        save_metrics(metrics, str(metrics_path))
        
        logger.info("Training pipeline finished successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        # T020: No Data Termination
        metrics = load_metrics(str(metrics_path))
        metrics["status"] = "no_data"
        save_metrics(metrics, str(metrics_path))
        return 0
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())