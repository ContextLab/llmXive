import json
import logging
import pickle
import signal
import sys
import os
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from joblib import dump

# Import project utilities
from config import RANDOM_SEED, MODELS_DIR, DATA_DIR
from utils.logging import get_logger

logger = get_logger(__name__)

# Timeout handling for GridSearch
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Model training timed out")

class TimeoutContext:
    def __init__(self, seconds: int):
        self.seconds = seconds

    def __enter__(self):
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)

def verify_data_provenance() -> bool:
    """
    T072 Implementation: Validate that data_curated/filtered.csv is derived from real data.
    
    Checks `data/curated/data_provenance.json` for `source_type == 'real'`.
    Raises SystemExit if missing, invalid, or synthetic.
    """
    provenance_path = DATA_DIR / "curated" / "data_provenance.json"
    
    if not provenance_path.exists():
        logger.error("Provenance file not found: %s", provenance_path)
        raise SystemExit(
            "Training Error: Data provenance file missing. "
            "Cannot verify data source type. Aborting training."
        )

    try:
        with open(provenance_path, 'r') as f:
            provenance = json.load(f)
    except json.JSONDecodeError:
        raise SystemExit("Training Error: Invalid JSON in data_provenance.json")

    source_type = provenance.get("source_type")
    source_url = provenance.get("source_url", "unknown")

    if source_type != "real":
        logger.error("Invalid source type: %s", source_type)
        raise SystemExit(
            f"Training Error: Cannot train on synthetic data. "
            f"Real data source required. Detected source_type: {source_type} "
            f"from URL: {source_url}"
        )

    logger.info("Data provenance verified: source_type='real'")
    return True

def prepare_features_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, list]:
    """
    Prepare feature matrix X and target vector y from the curated dataframe.
    Expects columns: ['size_mismatch', 'electronegativity_diff', 'valence_e_diff']
    Target: 'activation_energy'
    """
    feature_cols = ['size_mismatch', 'electronegativity_diff', 'valence_e_diff']
    
    # Ensure all required columns exist
    missing_cols = [c for c in feature_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    
    if 'activation_energy' not in df.columns:
        raise ValueError("Missing target column: activation_energy")

    X = df[feature_cols].values
    y = df['activation_energy'].values
    
    return X, y, feature_cols

def save_model_and_metrics(model: Any, metrics: Dict[str, float], model_name: str):
    """Save trained model and metrics to disk."""
    model_path = MODELS_DIR / f"{model_name}.pkl"
    metrics_path = MODELS_DIR / f"{model_name}_metrics.json"

    with open(model_path, 'wb') as f:
        pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("Saved %s to %s", model_name, model_path)
    logger.info("Saved metrics to %s", metrics_path)

def train_model_with_gridsearch(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    model_class: Any, 
    param_grid: Dict, 
    model_name: str,
    timeout_seconds: int = 300
) -> Tuple[Any, Dict[str, float]]:
    """
    Train a model using GridSearchCV with a timeout guard.
    Returns the best model and its best parameters/score.
    """
    logger.info("Starting GridSearchCV for %s...", model_name)
    
    # Initialize GridSearch
    gs = GridSearchCV(
        estimator=model_class(), 
        param_grid=param_grid, 
        cv=5, 
        n_jobs=-1, 
        scoring='r2',
        verbose=1
    )
    
    try:
        with TimeoutContext(timeout_seconds):
            gs.fit(X_train, y_train)
    except TimeoutError:
        raise SystemExit(f"Training Timeout: GridSearch for {model_name} exceeded {timeout_seconds}s")
    except MemoryError:
        raise SystemExit(f"Memory Error: GridSearch for {model_name} exceeds resource limits")

    best_model = gs.best_estimator_
    best_score = gs.best_score_
    best_params = gs.best_params_
    
    metrics = {
        "best_r2": float(best_score),
        "best_params": best_params,
        "model_type": model_name
    }
    
    logger.info("Best %s R²: %.4f", model_name, best_score)
    logger.info("Best params: %s", best_params)
    
    return best_model, metrics

def train_random_forest(X: np.ndarray, y: np.ndarray) -> Tuple[Any, Dict[str, float]]:
    """Train Random Forest with GridSearch."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )
    
    param_grid = {
        'max_depth': [3, 5, 10],
        'n_estimators': [50, 100, 200]
    }
    
    model, metrics = train_model_with_gridsearch(
        X_train, y_train, RandomForestRegressor, param_grid, "rf", timeout_seconds=300
    )
    
    # Evaluate on test set
    y_pred = model.predict(X_test)
    metrics['test_r2'] = float(r2_score(y_test, y_pred))
    metrics['test_rmse'] = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    metrics['test_mae'] = float(mean_absolute_error(y_test, y_pred))
    
    return model, metrics

def train_gradient_boosting(X: np.ndarray, y: np.ndarray) -> Tuple[Any, Dict[str, float]]:
    """Train Gradient Boosting with GridSearch."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )
    
    param_grid = {
        'max_depth': [3, 5, 10],
        'n_estimators': [50, 100, 200]
    }
    
    model, metrics = train_model_with_gridsearch(
        X_train, y_train, GradientBoostingRegressor, param_grid, "gb", timeout_seconds=300
    )
    
    # Evaluate on test set
    y_pred = model.predict(X_test)
    metrics['test_r2'] = float(r2_score(y_test, y_pred))
    metrics['test_rmse'] = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    metrics['test_mae'] = float(mean_absolute_error(y_test, y_pred))
    
    return model, metrics

def train_linear_regression(X: np.ndarray, y: np.ndarray) -> Tuple[Any, Dict[str, float]]:
    """Train Linear Regression and extract coefficient/p-value for size_mismatch."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    r2 = float(r2_score(y_test, y_pred))
    
    # Extract coefficient for 'size_mismatch' (assumed index 0 based on prepare_features_target)
    coef_size_mismatch = float(model.coef_[0])
    
    # Calculate p-value manually (t-test on coefficient)
    # Residuals
    residuals = y_test - y_pred
    n = len(y_test)
    p = X_train.shape[1]
    
    # Standard error of coefficients
    # Cov = sigma^2 * (X'X)^-1
    # sigma^2 = RSS / (n - p - 1)
    rss = np.sum(residuals**2)
    dof = n - p - 1
    if dof <= 0:
        logger.warning("Degrees of freedom <= 0. Cannot compute p-value.")
        p_value = 1.0
    else:
        sigma_sq = rss / dof
        X_train_p = np.c_[np.ones(X_train.shape[0]), X_train] # Add intercept
        try:
            XtX_inv = np.linalg.inv(X_train_p.T @ X_train_p)
            se_coef = np.sqrt(sigma_sq * XtX_inv[1, 1]) # Index 1 corresponds to first feature
            t_stat = coef_size_mismatch / se_coef if se_coef != 0 else 0
            # Two-tailed p-value approximation using scipy if available, else manual
            # Since we want to avoid heavy deps, we approximate or use a simple check
            # For strict compliance without scipy import in this specific block if not present:
            # We will assume scipy is available as per standard sklearn stack or use a fallback
            try:
                from scipy import stats
                p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), dof)))
            except ImportError:
                logger.warning("scipy not found. Using rough p-value approximation.")
                p_value = 0.05 if abs(t_stat) > 1.96 else 0.10
        except np.linalg.LinAlgError:
            logger.warning("Singular matrix. Cannot compute p-value.")
            p_value = 1.0
    
    metrics = {
        "r2": r2,
        "coef_size_mismatch": coef_size_mismatch,
        "p_value": p_value
    }
    
    return model, metrics

def aggregate_metrics(rf_metrics: Dict, gb_metrics: Dict, mean_r2: float) -> Dict[str, Any]:
    """Aggregate all training metrics into a single dictionary."""
    return {
        "rf_r2": rf_metrics.get("test_r2"),
        "rf_rmse": rf_metrics.get("test_rmse"),
        "rf_mae": rf_metrics.get("test_mae"),
        "gb_r2": gb_metrics.get("test_r2"),
        "gb_rmse": gb_metrics.get("test_rmse"),
        "gb_mae": gb_metrics.get("test_mae"),
        "mean_r2": mean_r2,
        "rf_delta": rf_metrics.get("test_r2", 0) - mean_r2,
        "gb_delta": gb_metrics.get("test_r2", 0) - mean_r2
    }

def main():
    """
    Main entry point for training pipeline.
    1. Verify data provenance (T072 requirement).
    2. Load curated data.
    3. Train models.
    4. Save artifacts.
    """
    logger.info("Starting model training pipeline...")
    
    # T072: Verify data is real before proceeding
    verify_data_provenance()
    
    # Load data
    curated_path = DATA_DIR / "curated" / "filtered.csv"
    if not curated_path.exists():
        raise SystemExit(f"Curated data file not found: {curated_path}")
    
    df = pd.read_csv(curated_path)
    logger.info("Loaded %d rows from %s", len(df), curated_path)
    
    # Prepare features
    X, y, feature_cols = prepare_features_target(df)
    logger.info("Features: %s", feature_cols)
    
    # Train Mean Predictor Baseline
    mean_val = np.mean(y)
    mean_r2 = 0.0 # R^2 of mean predictor is 0 by definition on test set if mean is from train? 
    # Actually, R^2 = 1 - (SS_res / SS_tot). If pred = mean(y_train), then on test:
    # SS_res = sum((y_test - mean_train)^2)
    # SS_tot = sum((y_test - mean_test)^2)
    # We'll calculate it properly if needed, but standard baseline R^2 is often 0.
    # Let's compute it on the test split for consistency.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)
    y_pred_mean = np.full_like(y_test, np.mean(y_train))
    ss_res = np.sum((y_test - y_pred_mean)**2)
    ss_tot = np.sum((y_test - np.mean(y_test))**2)
    mean_r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    # Train RF
    rf_model, rf_metrics = train_random_forest(X, y)
    save_model_and_metrics(rf_model, rf_metrics, "final_rf")
    
    # Train GB
    gb_model, gb_metrics = train_gradient_boosting(X, y)
    save_model_and_metrics(gb_model, gb_metrics, "final_gb")
    
    # Train Linear
    lr_model, lr_metrics = train_linear_regression(X, y)
    linear_path = MODELS_DIR / "linear_coef.json"
    with open(linear_path, 'w') as f:
        json.dump({
            "coef_size_mismatch": lr_metrics["coef_size_mismatch"],
            "p_value": lr_metrics["p_value"],
            "r2": lr_metrics["r2"]
        }, f, indent=2)
    logger.info("Saved linear coefficients to %s", linear_path)
    
    # Aggregate
    final_metrics = aggregate_metrics(rf_metrics, gb_metrics, mean_r2)
    final_metrics["linear_coef"] = lr_metrics["coef_size_mismatch"]
    final_metrics["linear_p_value"] = lr_metrics["p_value"]
    
    metrics_path = MODELS_DIR / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(final_metrics, f, indent=2)
    logger.info("Aggregated metrics saved to %s", metrics_path)
    
    logger.info("Training pipeline completed successfully.")

if __name__ == "__main__":
    main()