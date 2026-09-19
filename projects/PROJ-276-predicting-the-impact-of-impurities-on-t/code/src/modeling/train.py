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
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from code.src.utils.logging import get_modeling_logger
from code.src.utils.constants import get_atomic_weight

logger = get_modeling_logger()

# --- Timeout Handling for Constitution Principle VII ---

class TimeoutError(Exception):
    """Custom exception raised when the runtime watchdog is triggered."""
    pass

def timeout_handler(signum, frame):
    """Signal handler to raise TimeoutError when the watchdog fires."""
    raise TimeoutError("Runtime limit exceeded. Aborting hyperparameter search.")

class TimeoutGuard:
    """
    Context manager to enforce a maximum runtime for a block of code.
    Uses the 'signal' module (Unix only) to enforce a hard timeout.
    """
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.old_handler = None

    def __enter__(self):
        # Only works on Unix systems where signal.SIGALRM is available
        if not hasattr(signal, 'SIGALRM'):
            logger.warning("Signal-based timeout not supported on this OS (likely Windows). Skipping timeout enforcement.")
            return self

        self.old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_handler is not None:
            signal.alarm(0)  # Cancel the alarm
            signal.signal(signal.SIGALRM, self.old_handler)
        return False

# --- Data Loading and Preparation ---

def load_clean_data(data_path: str) -> pd.DataFrame:
    """
    Loads the cleaned dataset produced by T014.
    """
    path = Path(data_path)
    if not path.exists():
        logger.error(f"Clean data file not found: {data_path}")
        sys.exit(1)
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {data_path}")
    
    # Basic validation
    required_cols = ['Tc', 'impurities_atomic_pct', 'temp_K', 'pressure_GPa']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        sys.exit(1)
        
    return df

def prepare_features_targets(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepares features (X) and target (y) for modeling.
    Handles the impurity columns dynamically.
    Returns: X, y, impurity_stratifier (for stratified split)
    """
    # Target
    y = df['Tc'].values
    
    # Features: All numeric columns except known non-features
    exclude_cols = {'Tc', 'impurities_atomic_pct', 'temp_K', 'pressure_GPa', 'material_id', 'formula'}
    feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if not feature_cols:
        logger.error("No feature columns found in dataset.")
        sys.exit(1)
        
    X = df[feature_cols].values
    
    # Stratifier: Create bins based on the primary impurity type or a dominant impurity
    # Since impurities_atomic_pct might be a string or complex object, we assume it's aggregated or we use a proxy.
    # For this implementation, we assume the dataset has a 'dominant_impurity' or similar, 
    # or we bin the 'impurities_atomic_pct' if it's numeric. 
    # If 'impurities_atomic_pct' is a string representation of a dict, we need to extract.
    # Given the spec, let's assume we have a 'dominant_impurity' column or we create one.
    # If not present, we create a stratifier based on the count of impurities.
    
    if 'dominant_impurity' in df.columns:
        stratifier = df['dominant_impurity'].values
    elif 'impurity_count' in df.columns:
        # Bin counts into 3-5 groups for stratification
        bins = np.histogram_bin_edges(df['impurity_count'], bins=5)
        stratifier = np.digitize(df['impurity_count'].values, bins)
    else:
        # Fallback: use Tc bins for stratification if impurity info is missing
        logger.warning("No explicit impurity stratifier found. Using Tc bins.")
        stratifier = pd.qcut(y, q=5, labels=False, duplicates='drop')
        
    return X, y, stratifier

# --- Model Training Logic ---

def train_model(X: np.ndarray, y: np.ndarray, stratifier: np.ndarray, 
                timeout_seconds: int = 120, max_grid_combinations: int = 50) -> Dict[str, Any]:
    """
    Trains multiple models with hyperparameter tuning, enforcing:
    1. Hard cap on grid combinations.
    2. Runtime watchdog (Constitution Principle VII).
    
    Returns a dictionary containing the best model, metrics, and training history.
    """
    logger.info("Starting model training with timeout and grid constraints.")
    
    # Define models and their grids
    models_config = [
        {
            "name": "LinearRegression",
            "estimator": LinearRegression(),
            "param_grid": {}, # No tuning needed for baseline
            "tune": False
        },
        {
            "name": "Ridge",
            "estimator": Ridge(),
            "param_grid": {"alpha": [0.1, 1.0, 10.0]},
            "tune": True
        },
        {
            "name": "RandomForest",
            "estimator": RandomForestRegressor(random_state=42),
            "param_grid": {
                "n_estimators": [50, 100],
                "max_depth": [None, 5, 10]
            },
            "tune": True
        },
        {
            "name": "XGBoost",
            # Note: XGBoost might need to be installed. If not, we fallback or skip.
            "estimator": None, 
            "param_grid": {
                "n_estimators": [50, 100],
                "max_depth": [3, 5]
            },
            "tune": True,
            "import_name": "xgboost"
        }
    ]

    results = []
    best_model = None
    best_r2 = -np.inf
    best_model_name = ""

    # Split data once for final evaluation
    # Using a simple hold-out or CV approach. Here we use CV for selection.
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

    for config in models_config:
        name = config["name"]
        estimator = config["estimator"]
        param_grid = config["param_grid"]
        tune = config["tune"]
        
        # Handle XGBoost import dynamically
        if config.get("import_name"):
            try:
                import xgboost
                if name == "XGBoost":
                    estimator = xgboost.XGBRegressor(random_state=42)
            except ImportError:
                logger.warning(f"{name} not installed. Skipping.")
                continue

        if estimator is None:
            continue

        logger.info(f"Training {name}...")
        
        model_pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', estimator)
        ])

        if tune and param_grid:
            # Calculate number of combinations
            n_combinations = 1
            for k, v in param_grid.items():
                n_combinations *= len(v)
            
            if n_combinations > max_grid_combinations:
                logger.warning(f"{name} grid size ({n_combinations}) exceeds limit ({max_grid_combinations}). Truncating grid.")
                # Truncate logic: keep first max_combinations by iterating
                # Simple approach: reduce 'n_estimators' or 'max_depth' lists
                keys = list(param_grid.keys())
                # Heuristic: reduce the first dimension until under limit
                while n_combinations > max_grid_combinations and len(keys) > 0:
                    key = keys.pop(0)
                    # Keep only the first half of values for this param
                    mid = max(1, len(param_grid[key]) // 2)
                    param_grid[key] = param_grid[key][:mid]
                    n_combinations = 1
                    for k, v in param_grid.items():
                        n_combinations *= len(v)
                
                logger.info(f"Reduced {name} grid to {n_combinations} combinations.")

            # Enforce timeout for GridSearch
            try:
                with TimeoutGuard(timeout_seconds):
                    grid_search = GridSearchCV(
                        model_pipeline, 
                        param_grid, 
                        cv=cv, 
                        scoring='r2', 
                        n_jobs=-1,
                        refit=True
                    )
                    grid_search.fit(X, y, regressor__sample_weight=None) # Sample weight not needed for now
                    
                    best_params = grid_search.best_params_
                    best_cv_score = grid_search.best_score_
                    best_estimator = grid_search.best_estimator_
                    
                    logger.info(f"{name} Best Params: {best_params}, CV R²: {best_cv_score:.4f}")
            except TimeoutError:
                logger.error(f"{name} timed out during grid search. Aborting this model.")
                continue
        else:
            # No tuning, just fit
            try:
                with TimeoutGuard(timeout_seconds):
                    model_pipeline.fit(X, y)
                    best_estimator = model_pipeline
                    # Estimate score
                    scores = cross_val_score(model_pipeline, X, y, cv=cv, scoring='r2')
                    best_cv_score = np.mean(scores)
                    best_params = {}
            except TimeoutError:
                logger.error(f"{name} timed out during fitting. Aborting.")
                continue

        # Store result
        results.append({
            "model_name": name,
            "best_params": best_params,
            "cv_r2": float(best_cv_score),
            "model": best_estimator
        })

        if best_cv_score > best_r2:
            best_r2 = best_cv_score
            best_model = best_estimator
            best_model_name = name

    if best_model is None:
        logger.error("No models could be trained successfully.")
        sys.exit(1)

    logger.info(f"Best model selected: {best_model_name} with R² = {best_r2:.4f}")
    
    return {
        "best_model": best_model,
        "best_model_name": best_model_name,
        "best_r2": best_r2,
        "all_results": results
    }

def main():
    parser = argparse.ArgumentParser(description="Train and select the best model for MgB2 Tc prediction.")
    parser.add_argument("--input", type=str, default="data/processed/mgb2_clean.csv", help="Path to clean data CSV")
    parser.add_argument("--output-model", type=str, default="data/processed/best_model.pkl", help="Path to save best model")
    parser.add_argument("--output-metrics", type=str, default="data/processed/model_metrics.json", help="Path to save metrics JSON")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds for grid search steps")
    parser.add_argument("--max-combinations", type=int, default=50, help="Max grid search combinations per model")
    
    args = parser.parse_args()

    # Load Data
    df = load_clean_data(args.input)
    X, y, stratifier = prepare_features_targets(df)

    # Train Models
    training_result = train_model(
        X, y, stratifier, 
        timeout_seconds=args.timeout,
        max_grid_combinations=args.max_combinations
    )

    # Save Best Model
    output_model_path = Path(args.output_model)
    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_model_path, 'wb') as f:
        pickle.dump(training_result["best_model"], f)
    logger.info(f"Saved best model to {output_model_path}")

    # Save Metrics Report
    metrics_report = {
        "best_model_name": training_result["best_model_name"],
        "best_cv_r2": training_result["best_r2"],
        "models_trained": [
            {
                "name": r["model_name"],
                "cv_r2": r["cv_r2"],
                "best_params": r["best_params"]
            }
            for r in training_result["all_results"]
        ]
    }

    output_metrics_path = Path(args.output_metrics)
    output_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_metrics_path, 'w') as f:
        json.dump(metrics_report, f, indent=2)
    logger.info(f"Saved metrics report to {output_metrics_path}")

    print(f"Training complete. Best model: {training_result['best_model_name']} (R²: {training_result['best_r2']:.4f})")

if __name__ == "__main__":
    main()