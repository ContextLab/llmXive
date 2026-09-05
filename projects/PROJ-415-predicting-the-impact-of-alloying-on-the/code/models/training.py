import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

from config import MODELS_DIR, DATA_DIR, LOG_DIR
from utils.logging import get_logger

# Ensure logger is configured
logger = get_logger(__name__)

def prepare_features_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepares the feature matrix (X) and target vector (y) from the curated dataframe.
    Expects 'size_mismatch' as the primary feature and 'activation_energy_eV' as target.
    """
    if 'size_mismatch' not in df.columns:
        raise ValueError("Column 'size_mismatch' not found in dataframe. Run descriptors first.")
    if 'activation_energy_eV' not in df.columns:
        raise ValueError("Column 'activation_energy_eV' not found in dataframe.")

    X = df[['size_mismatch']]
    y = df['activation_energy_eV']
    return X, y

def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series, cv: int = 5) -> Tuple[Any, Dict[str, float]]:
    """
    Trains a Random Forest Regressor with GridSearchCV.
    Parameters:
        X_train: Training features
        y_train: Training target
        cv: Number of folds for cross-validation (default 5)
    Returns:
        trained_model: The best estimator from GridSearch
        metrics: Dictionary containing best_params and best_score
    """
    logger.info("Starting Random Forest GridSearch...")

    param_grid = {
        'max_depth': [3, 5, 7, 10],
        'n_estimators': [50, 100, 200]
    }

    rf = RandomForestRegressor(random_state=42, n_jobs=-1)

    try:
        grid_search = GridSearchCV(
            estimator=rf,
            param_grid=param_grid,
            cv=cv,
            scoring='r2',
            n_jobs=-1,
            verbose=1
        )
        grid_search.fit(X_train, y_train)
    except MemoryError:
        logger.error("Memory Error: GridSearch exceeds resource limits")
        raise SystemExit("Memory Error: GridSearch exceeds resource limits")

    logger.info(f"Best RF Params: {grid_search.best_params_}")
    logger.info(f"Best RF R2 Score: {grid_search.best_score_}")

    return grid_search.best_estimator_, {
        'best_params': grid_search.best_params_,
        'best_cv_score': float(grid_search.best_score_)
    }

def train_gradient_boosting(X_train: pd.DataFrame, y_train: pd.Series, cv: int = 5) -> Tuple[Any, Dict[str, float]]:
    """
    Trains a Gradient Boosting Regressor with GridSearchCV.
    Parameters:
        X_train: Training features
        y_train: Training target
        cv: Number of folds for cross-validation (default 5)
    Returns:
        trained_model: The best estimator from GridSearch
        metrics: Dictionary containing best_params and best_score
    """
    logger.info("Starting Gradient Boosting GridSearch...")

    param_grid = {
        'max_depth': [3, 5, 7, 10],
        'n_estimators': [50, 100, 200],
        'learning_rate': [0.05, 0.1, 0.2]
    }

    gb = GradientBoostingRegressor(random_state=42)

    try:
        grid_search = GridSearchCV(
            estimator=gb,
            param_grid=param_grid,
            cv=cv,
            scoring='r2',
            n_jobs=-1,
            verbose=1
        )
        grid_search.fit(X_train, y_train)
    except MemoryError:
        logger.error("Memory Error: GridSearch exceeds resource limits")
        raise SystemExit("Memory Error: GridSearch exceeds resource limits")

    logger.info(f"Best GB Params: {grid_search.best_params_}")
    logger.info(f"Best GB R2 Score: {grid_search.best_score_}")

    return grid_search.best_estimator_, {
        'best_params': grid_search.best_params_,
        'best_cv_score': float(grid_search.best_score_)
    }

def train_linear_regression(X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[Any, Dict[str, Any]]:
    """
    Trains a Linear Regression model.
    Returns model and coefficients info.
    """
    logger.info("Training Linear Regression...")
    model = LinearRegression()
    model.fit(X_train, y_train)

    coef = model.coef_[0]
    intercept = model.intercept_
    r2 = model.score(X_train, y_train)

    # Simple p-value approximation using t-test logic for single feature
    # residuals
    y_pred = model.predict(X_train)
    residuals = y_train - y_pred
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y_train - np.mean(y_train))**2)
    # Standard error of the coefficient
    # se_coef = sqrt(MSE / sum((x - x_mean)^2))
    mse = ss_res / (len(y_train) - 2)
    ss_x = np.sum((X_train['size_mismatch'] - np.mean(X_train['size_mismatch']))**2)
    se_coef = np.sqrt(mse / ss_x)
    t_stat = coef / se_coef
    # Approximate p-value (two-tailed) using scipy if available, else mock logic for stability
    try:
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(np.abs(t_stat), len(y_train) - 2))
    except ImportError:
        logger.warning("scipy not found, using approximate p-value logic")
        p_value = 0.05 if abs(t_stat) > 2.0 else 0.1

    return model, {
        'coef': float(coef),
        'intercept': float(intercept),
        'r2': float(r2),
        'p_value': float(p_value)
    }

def save_model_and_metrics(model: Any, model_name: str, metrics: Dict[str, Any], model_path: Path):
    """
    Saves the model to a pickle file and updates the metrics dictionary.
    """
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model {model_name} saved to {model_path}")

    # Load existing metrics or create new
    metrics_file = MODELS_DIR / 'metrics.json'
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            existing_metrics = json.load(f)
    else:
        existing_metrics = {}

    # Update metrics
    if model_name == 'rf':
        existing_metrics['rf_best_params'] = metrics['best_params']
        existing_metrics['rf_best_cv_score'] = metrics['best_cv_score']
    elif model_name == 'gb':
        existing_metrics['gb_best_params'] = metrics['best_params']
        existing_metrics['gb_best_cv_score'] = metrics['best_cv_score']
    elif model_name == 'linear':
        existing_metrics['linear_coef'] = metrics['coef']
        existing_metrics['linear_intercept'] = metrics['intercept']
        existing_metrics['linear_r2'] = metrics['r2']
        existing_metrics['linear_p_value'] = metrics['p_value']

    with open(metrics_file, 'w') as f:
        json.dump(existing_metrics, f, indent=2)

def main():
    """
    Main entry point for training pipeline.
    Loads curated data, splits, trains RF, GB, and Linear models.
    """
    ensure_directories()
    logger.info("Starting model training pipeline...")

    curated_path = DATA_DIR / 'curated' / 'filtered.csv'
    if not curated_path.exists():
        raise FileNotFoundError(f"Curated data not found at {curated_path}. Run ingestion and curation first.")

    df = pd.read_csv(curated_path)
    logger.info(f"Loaded {len(df)} rows from {curated_path}")

    X, y = prepare_features_target(df)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=None
    )
    # Stratify might fail if target is continuous and unique values < 2 in a fold,
    # so we catch it and fallback to random split if necessary (handled by split_data_stratified in ingestion usually)
    # For this script, we assume valid split or fallback logic handled upstream.
    
    logger.info(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")

    # Train RF
    rf_model, rf_metrics = train_random_forest(X_train, y_train, cv=5)
    save_model_and_metrics(rf_model, 'rf', rf_metrics, MODELS_DIR / 'final_rf.pkl')

    # Train GB
    gb_model, gb_metrics = train_gradient_boosting(X_train, y_train, cv=5)
    save_model_and_metrics(gb_model, 'gb', gb_metrics, MODELS_DIR / 'final_gb.pkl')

    # Train Linear
    lr_model, lr_metrics = train_linear_regression(X_train, y_train)
    save_model_and_metrics(lr_model, 'linear', lr_metrics, MODELS_DIR / 'linear_model.pkl')

    logger.info("Training pipeline completed successfully.")

if __name__ == "__main__":
    main()