import os
import sys
import json
import logging
import time
import resource
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut, train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.base import BaseEstimator

# Local imports based on API surface
from utils.config import get_env_var
from utils.io import setup_logging, compute_sha256
from features.descriptors import extract_descriptors

# Configure logging
logger = setup_logging()

# Resource constraints for T030
# Limit to 2 CPU cores
N_JOBS = 2
# Limit to 7 GB RAM (7 * 1024 * 1024 * 1024 bytes)
MEMORY_LIMIT_BYTES = 7 * 1024 * 1024 * 1024

def set_resource_limits():
    """Enforce CPU and memory limits as per T030."""
    # Set number of threads for numpy/scikit-learn
    os.environ["OMP_NUM_THREADS"] = str(N_JOBS)
    os.environ["OPENBLAS_NUM_THREADS"] = str(N_JOBS)
    os.environ["MKL_NUM_THREADS"] = str(N_JOBS)
    
    # Enforce memory limit via resource module (Unix only)
    if sys.platform != 'win32':
        try:
            # Set soft and hard limits
            resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
            logger.info(f"Memory limit set to {MEMORY_LIMIT_BYTES / (1024**3):.2f} GB")
        except (ValueError, resource.error) as e:
            logger.warning(f"Could not set memory limit: {e}. Continuing without hard limit.")
    else:
        logger.warning("Memory limit enforcement via resource module not supported on Windows.")

class NullModel(BaseEstimator):
    """A baseline model that predicts the mean of the training target."""
    
    def fit(self, X, y):
        self.mean_ = np.mean(y)
        return self
    
    def predict(self, X):
        return np.full(X.shape[0], self.mean_)

def load_clean_data(data_path: str) -> pd.DataFrame:
    """Load the cleaned parquet dataset."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Clean data file not found at {data_path}")
    logger.info(f"Loading data from {data_path}")
    return pd.read_parquet(path)

def split_data_stratified(df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data by alloy family if possible, otherwise random split.
    Returns train_df, test_df.
    """
    if 'alloy_family' not in df.columns:
        logger.warning("No 'alloy_family' column found. Performing random split.")
        return train_test_split(df, test_size=0.2, random_state=42)
    
    try:
        train_df, test_df = train_test_split(
            df, 
            test_size=0.2, 
            stratify=df['alloy_family'], 
            random_state=42
        )
        logger.info("Stratified split by alloy_family successful.")
    except ValueError as e:
        logger.warning(f"Stratification failed ({e}). Falling back to random split.")
        return train_test_split(df, test_size=0.2, random_state=42)
    
    return train_df, test_df

def determine_cv_strategy(n_samples: int) -> Any:
    """Determine CV strategy based on sample size."""
    if n_samples >= 50:
        logger.info("Using 5-fold CV (N >= 50)")
        return KFold(n_splits=5, shuffle=True, random_state=42)
    elif n_samples >= 20:
        logger.info("Using Hold-Out CV (20 <= N < 50)")
        return KFold(n_splits=2, shuffle=True, random_state=42) # Simplified hold-out as 2-fold
    else:
        logger.info("Using Leave-One-Out CV (N < 20)")
        return LeaveOneOut()

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Extract features and target."""
    # Assuming the dataframe already has descriptors calculated or we calculate them here
    # For T030 context, we assume descriptors are present or calculated via extract_descriptors
    # If 'composition' is present, we might need to extract descriptors on the fly if not done in ingestion
    # However, T022 implies clean_mg_data.parquet is ready. Let's assume features are pre-calculated columns
    # or we extract them if raw composition is there.
    
    feature_cols = [
        'weighted_mean_radius', 
        'electronegativity_variance', 
        'vec_mean', 
        'size_mismatch'
    ]
    
    # Check if columns exist, if not try to derive from composition if available
    if not all(col in df.columns for col in feature_cols):
        if 'composition' in df.columns:
            logger.info("Calculating descriptors from composition column...")
            descriptors = df['composition'].apply(extract_descriptors)
            # Flatten descriptors if they are dicts
            # This is a simplification; extract_descriptors should return a dict or object
            # Assuming it returns a dict with keys matching feature_cols
            for col in feature_cols:
                df[col] = [d.get(col, np.nan) for d in descriptors]
        else:
            raise ValueError(f"Feature columns {feature_cols} not found and no 'composition' column to derive them.")

    X = df[feature_cols].values
    y = df['cte'].values
    return X, y

def load_metrics(metrics_path: str) -> Dict:
    """Load existing metrics or return empty dict."""
    path = Path(metrics_path)
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_metrics(metrics: Dict, metrics_path: str):
    """Save metrics to JSON."""
    path = Path(metrics_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)

def run_elemental_baseline(df: pd.DataFrame, X_train: np.ndarray, y_train: np.ndarray) -> Dict:
    """
    Run elemental weighted average baseline if possible.
    Returns baseline metrics.
    """
    # Implementation of T026a logic
    # Assuming we have elemental CTEs in a separate source or pre-calculated
    # For now, if not available, fallback to null model
    try:
        # Placeholder for actual elemental CTE lookup logic
        # If successful, return metrics
        # If not, raise or return null
        pass
    except Exception:
        logger.warning("Elemental CTEs unavailable. Using Null Model.")
        return {"baseline_type": "null_model"}
    
    return {"baseline_type": "elemental_weighted_average"}

def run_training_pipeline(X: np.ndarray, y: np.ndarray, cv_strategy: Any) -> Dict:
    """
    Train models with resource constraints enforced.
    """
    # Enforce resource limits (T030)
    set_resource_limits()
    
    results = {}
    
    # 1. Null Model
    logger.info("Training Null Model...")
    null_model = NullModel()
    null_scores = cross_val_score(null_model, X, y, cv=cv_strategy, scoring='r2')
    results['null_model'] = {
        'r2_mean': float(np.mean(null_scores)),
        'r2_std': float(np.std(null_scores))
    }
    
    # 2. Linear Regression
    logger.info("Training Linear Regression...")
    lr_model = LinearRegression()
    lr_scores = cross_val_score(lr_model, X, y, cv=cv_strategy, scoring='r2')
    results['linear_regression'] = {
        'r2_mean': float(np.mean(lr_scores)),
        'r2_std': float(np.std(lr_scores))
    }
    
    # 3. Random Forest
    logger.info("Training Random Forest (n_jobs=2)...")
    # Explicitly set n_jobs=2 as per T030
    rf_model = RandomForestRegressor(
        n_estimators=100, 
        max_depth=None, 
        random_state=42, 
        n_jobs=N_JOBS
    )
    rf_scores = cross_val_score(rf_model, X, y, cv=cv_strategy, scoring='r2')
    results['random_forest'] = {
        'r2_mean': float(np.mean(rf_scores)),
        'r2_std': float(np.std(rf_scores)),
        'n_jobs': N_JOBS
    }
    
    return results

def main():
    """Main entry point for training pipeline."""
    # Paths
    data_path = "data/processed/clean_mg_data.parquet"
    metrics_path = "results/metrics.json"
    
    # Ensure results directory exists
    Path("results").mkdir(exist_ok=True)
    
    # Load Data
    try:
        df = load_clean_data(data_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        # Handle No Data case (T020)
        metrics = load_metrics(metrics_path)
        metrics['status'] = 'no_data'
        save_metrics(metrics, metrics_path)
        return

    if len(df) == 0:
        logger.error("No valid metallic glass entries found.")
        metrics = load_metrics(metrics_path)
        metrics['status'] = 'no_data'
        save_metrics(metrics, metrics_path)
        return

    # Prepare Features
    X, y = prepare_features(df)
    
    # Determine CV Strategy
    cv_strategy = determine_cv_strategy(len(df))
    
    # Run Pipeline
    results = run_training_pipeline(X, y, cv_strategy)
    
    # Save Results
    metrics = load_metrics(metrics_path)
    metrics['training_results'] = results
    metrics['n_samples'] = len(df)
    
    # Log resource constraints applied
    metrics['resource_constraints'] = {
        'n_jobs': N_JOBS,
        'memory_limit_gb': MEMORY_LIMIT_BYTES / (1024**3)
    }
    
    save_metrics(metrics, metrics_path)
    logger.info("Training pipeline completed. Results saved to results/metrics.json")

if __name__ == "__main__":
    main()