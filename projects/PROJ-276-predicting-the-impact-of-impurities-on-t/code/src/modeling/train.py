"""
Model Training and Selection Pipeline for MgB2 Impurity Impact Study.

This module handles:
1. Loading clean data from preprocessing.
2. Preparing features and targets.
3. Training multiple models (Linear, Ridge, RF, XGBoost).
4. Enforcing runtime timeouts (Constitution Principle VII).
5. Selecting the best model based on cross-validated R².
6. Saving the best model and generating metrics reports.
"""

import os
import sys
import json
import pickle
import argparse
import signal
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# XGBoost is optional; handle import failure gracefully but fail loudly if requested
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from code.src.utils.logging import get_modeling_logger
from code.src.utils.config import get_project_root

logger = get_modeling_logger()

# --- Timeout Handling (Constitution Principle VII) ---

class TimeoutError(Exception):
    """Custom exception for timeout events."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Model training timed out. Exceeded maximum allowed runtime.")

class TimeoutGuard:
    """Context manager to enforce a runtime limit on a block of code."""
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.old_handler = None

    def __enter__(self):
        # Set the signal handler
        self.old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset the alarm
        signal.alarm(0)
        if self.old_handler:
            signal.signal(signal.SIGALRM, self.old_handler)

# --- Data Loading ---

def load_clean_data(file_path: str) -> pd.DataFrame:
    """
    Load the preprocessed clean dataset.

    Args:
        file_path: Path to the CSV file.

    Returns:
        DataFrame with clean data.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Clean data file not found at {file_path}")

    logger.info(f"Loading clean data from {file_path}")
    df = pd.read_csv(file_path)

    if df.empty:
        raise ValueError("Loaded dataset is empty.")

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

# --- Feature Preparation ---

def prepare_features_targets(df: pd.DataFrame, target_col: str = "Tc") -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Separate features and target, and create stratification bins for split.

    Args:
        df: Input dataframe.
        target_col: Name of the target column.

    Returns:
        X (features), y (target), strat_labels (for stratified split).
    """
    # Identify impurity columns (assume they contain 'impurity' or are numeric cols not target)
    # Based on spec, we expect a mix of composition features.
    # For this implementation, we assume all numeric columns except Tc are features.
    # If specific impurity columns exist, we might want to bin them for stratification.
    
    # Drop non-numeric columns if any (besides target)
    X = df.select_dtypes(include=[np.number])
    if target_col in X.columns:
        X = X.drop(columns=[target_col])
    
    if X.empty:
        raise ValueError("No feature columns found in dataset.")

    y = df[target_col]

    # Create stratification labels based on impurity type if available, else bins of Tc
    # Assuming 'impurity_type' or similar might exist. If not, bin Tc.
    strat_col = None
    for col in df.columns:
        if 'impurity_type' in col.lower() or 'impurity' in col.lower():
            # If it's categorical, use it directly
            if df[col].dtype == 'object':
                strat_col = col
                break
            # If it's numeric but represents a category ID, use it
            elif df[col].nunique() < 20:
                strat_col = col
                break

    if strat_col:
        strat_labels = df[strat_col]
        logger.info(f"Using '{strat_col}' for stratification.")
    else:
        # Bin Tc into 5 groups for stratification if no explicit category
        y_bins = pd.qcut(y, q=5, duplicates='drop', labels=False)
        strat_labels = y_bins
        logger.info("Binned Tc for stratification.")

    return X, y, strat_labels

# --- Model Training ---

def train_model(
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    cv_folds: int = 5,
    timeout_seconds: int = 300
) -> Dict[str, Any]:
    """
    Train a specific model, perform cross-validation, and evaluate.

    Args:
        model_name: Identifier for the model ('linear', 'ridge', 'rf', 'xgb').
        X_train, y_train: Training data.
        X_test, y_test: Test data.
        cv_folds: Number of CV folds.
        timeout_seconds: Maximum time allowed for training this model.

    Returns:
        Dictionary containing model instance, metrics, and CV scores.
    """
    logger.info(f"Training model: {model_name}")
    
    # Initialize model
    if model_name == 'linear':
        model = LinearRegression()
        param_grid = {} # No grid search for simple linear in this MVP, or minimal
    elif model_name == 'ridge':
        # Ridge is authorized for collinearity handling
        model = Ridge()
        param_grid = {'alpha': [0.1, 1.0, 10.0]}
    elif model_name == 'rf':
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        param_grid = {'max_depth': [None, 5, 10]}
    elif model_name == 'xgb':
        if not HAS_XGBOOST:
            logger.warning("XGBoost not installed. Skipping.")
            return None
        model = xgb.XGBRegressor(random_state=42, n_jobs=-1)
        param_grid = {'max_depth': [3, 6], 'learning_rate': [0.01, 0.1]}
    else:
        raise ValueError(f"Unknown model: {model_name}")

    # Simple Pipeline: Scaling + Model (except tree-based usually don't need scaling, but safe)
    # For linear/ridge, scaling is crucial. For trees, it doesn't hurt.
    # We'll apply scaling for all to be consistent, or skip for trees if optimized.
    # Let's stick to a simple model training for MVP to ensure speed within timeout.
    # We will perform a simple grid search if param_grid is not empty.
    
    best_model = None
    best_score = -np.inf
    best_params = {}

    # Define search space
    # If param_grid is empty, just use default params
    if not param_grid:
        param_grid = [{}]
    else:
        # Convert dict to list of dicts for grid search simulation without sklearn GridSearchCV overhead if needed
        # But using sklearn GridSearchCV is standard.
        pass

    # To keep it simple and fast (MVP), we will do a manual grid search or simple CV on defaults
    # Given the constraint "hard cap on number of grid combinations", we will limit iterations.
    
    candidates = []
    if not param_grid:
        candidates.append({})
    else:
        # Generate combinations
        import itertools
        keys = param_grid.keys()
        values = param_grid.values()
        for combination in itertools.product(*values):
            candidates.append(dict(zip(keys, combination)))

    # Enforce limit
    if len(candidates) > 10:
        logger.warning(f"Grid size {len(candidates)} exceeds limit. Truncating to 10.")
        candidates = candidates[:10]

    logger.info(f"Evaluating {len(candidates)} parameter combinations for {model_name}")

    cv_scores = []
    
    # Use TimeoutGuard for the entire training block
    try:
        with TimeoutGuard(timeout_seconds):
            for params in candidates:
                # Set params
                for k, v in params.items():
                    setattr(model, k, v)
                
                # Cross Validation
                # Use StratifiedKFold if target is continuous? No, use KFold for regression
                from sklearn.model_selection import KFold
                kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
                
                scores = cross_val_score(model, X_train, y_train, cv=kfold, scoring='r2')
                mean_score = np.mean(scores)
                cv_scores.append(mean_score)
                
                if mean_score > best_score:
                    best_score = mean_score
                    best_params = params
                    # Clone model with best params for final fit?
                    # We'll refit after the loop
                    best_model_temp = model
    
    except TimeoutError:
        logger.error(f"Timeout exceeded for {model_name}. Aborting.")
        return {
            "model_name": model_name,
            "status": "timeout",
            "best_r2": None,
            "test_r2": None,
            "test_mae": None
        }

    # Refit best model on full training data
    for k, v in best_params.items():
        setattr(model, k, v)
    model.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = model.predict(X_test)
    test_r2 = r2_score(y_test, y_pred)
    test_mae = mean_absolute_error(y_test, y_pred)

    logger.info(f"Model {model_name} completed. Best CV R²: {best_score:.4f}, Test R²: {test_r2:.4f}")

    return {
        "model_name": model_name,
        "model": model,
        "best_params": best_params,
        "best_cv_r2": best_score,
        "cv_scores": cv_scores,
        "test_r2": test_r2,
        "test_mae": test_mae,
        "status": "success"
    }

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Train and select best model for MgB2 study.")
    parser.add_argument("--data", type=str, default="data/processed/mgb2_clean.csv", help="Path to clean data CSV")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Directory to save outputs")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds for each model training")
    args = parser.parse_args()

    project_root = get_project_root()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load Data
    try:
        df = load_clean_data(args.data)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Prepare Features
    try:
        X, y, strat_labels = prepare_features_targets(df)
    except ValueError as e:
        logger.error(f"Feature preparation failed: {e}")
        sys.exit(1)

    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=strat_labels
    )
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Define Models to Train
    models_to_train = ['linear', 'ridge', 'rf']
    if HAS_XGBOOST:
        models_to_train.append('xgb')

    results = []

    # Train each model
    for model_name in models_to_train:
        res = train_model(
            model_name=model_name,
            X_train=X_train, y_train=y_train,
            X_test=X_test, y_test=y_test,
            timeout_seconds=args.timeout
        )
        if res:
            results.append(res)

    if not results:
        logger.error("No models were successfully trained.")
        sys.exit(1)

    # Select Best Model
    # Criteria: Highest cross-validated R²
    best_result = max(results, key=lambda x: x['best_cv_r2'] if x['status'] == 'success' else -np.inf)

    if best_result['status'] != 'success':
        logger.error(f"No successful models found. Best candidate status: {best_result['status']}")
        sys.exit(1)

    logger.info(f"Selected best model: {best_result['model_name']} with CV R²: {best_result['best_cv_r2']:.4f}")

    # Save Best Model
    model_path = output_dir / "best_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(best_result['model'], f)
    logger.info(f"Saved best model to {model_path}")

    # Save Metrics Report (JSON) for all models
    # This fulfills T021 requirement as well, as part of the training flow
    metrics_report = []
    for res in results:
        entry = {
            "model_name": res['model_name'],
            "status": res['status'],
            "best_cv_r2": res.get('best_cv_r2'),
            "test_r2": res.get('test_r2'),
            "test_mae": res.get('test_mae'),
            "best_params": res.get('best_params')
        }
        metrics_report.append(entry)

    metrics_path = output_dir / "model_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics_report, f, indent=2)
    logger.info(f"Saved metrics report to {metrics_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())