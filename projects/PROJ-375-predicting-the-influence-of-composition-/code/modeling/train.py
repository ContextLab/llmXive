"""
Training pipeline for Metallic Glass CTE prediction.

This script:
1. Loads the cleaned dataset produced by the ingestion step.
2. Prepares the feature matrix using the four descriptor columns.
3. Performs a stratified (or random) train‑test split and writes the splits
   to ``data/processed/train.parquet`` and ``data/processed/test.parquet``.
4. Trains a Linear Regression model and a Random Forest model (grid‑search
   over a modest hyper‑parameter space) respecting the 2‑core / 7 GB RAM
   limits.
5. Serialises the final models to ``models/linear_regression.pkl`` and
   ``models/random_forest.pkl``.
6. Writes basic training metrics to ``results/training_metrics.json``.
"""
import sys
import json
import logging
import time
import resource
from pathlib import Path
from typing import Tuple, Dict, Any

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error

from utils.io import setup_logging
from utils.config import get_env_var

logger = setup_logging()

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------

REQUIRED_FEATURES = [
    "weighted_mean_atomic_radius",
    "electronegativity_variance",
    "vec",
    "atomic_size_coefficient_of_variation",
]
TARGET_COLUMN = "cte"

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def set_resource_limits(n_jobs: int = 2, memory_limit_mb: int = 7000) -> None:
    """Enforce resource constraints (memory limit only; n_jobs is passed to sklearn)."""
    logger.info(f"Setting resource limits: n_jobs={n_jobs}, memory_limit={memory_limit_mb}MB")
    if sys.platform != "win32":
        try:
            resource.setrlimit(resource.RLIMIT_AS,
                              (memory_limit_mb * 1024 * 1024, memory_limit_mb * 1024 * 1024))
            logger.info(f"Memory limit set to {memory_limit_mb} MB")
        except Exception as e:
            logger.warning(f"Could not set memory limit: {e}")

def load_clean_data(filepath: Path) -> pd.DataFrame:
    if not filepath.exists():
        raise FileNotFoundError(f"Clean data file not found: {filepath}")
    logger.info(f"Loading clean data from {filepath}")
    df = pd.read_parquet(filepath)
    missing = [c for c in REQUIRED_FEATURES + [TARGET_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    logger.info("Preparing feature matrix X and target vector y")
    mask = df[REQUIRED_FEATURES + [TARGET_COLUMN]].notna().all(axis=1)
    df_clean = df[mask].copy()
    if df_clean.empty:
        raise ValueError("No rows left after dropping NaNs.")
    X = df_clean[REQUIRED_FEATURES].values
    y = df_clean[TARGET_COLUMN].values
    logger.info(f"Prepared X shape {X.shape}, y shape {y.shape}")
    return X, y, df_clean

def split_and_save(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split by ``alloy_family`` if present, otherwise random.
    Writes the splits to parquet files and returns the two DataFrames.
    """
    # The current dataset does not contain an explicit ``alloy_family`` column.
    # We therefore fall back to a simple random split.
    logger.info("Performing random train‑test split.")
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)

    # Write splits
    train_path = Path("data/processed/train.parquet")
    test_path = Path("data/processed/test.parquet")
    train_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)
    logger.info(f"Train split written to {train_path}")
    logger.info(f"Test split written to {test_path}")
    return train_df, test_df

def train_linear_regression(X_train: np.ndarray, y_train: np.ndarray) -> LinearRegression:
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    return lr

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    param_grid = {
        "n_estimators": [100, 200, 500],
        "max_depth": [None, 10, 20],
        "min_samples_leaf": [1, 2],
    }
    rf = RandomForestRegressor(random_state=42, n_jobs=2)
    cv = GridSearchCV(rf, param_grid, cv=5, scoring="r2", n_jobs=2)
    cv.fit(X_train, y_train)
    best_rf = cv.best_estimator_
    logger.info(f"Random Forest best params: {cv.best_params_}")
    return best_rf, cv.best_params_

def save_models(lr: LinearRegression, rf: RandomForestRegressor) -> None:
    from joblib import dump
    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)
    dump(lr, models_dir / "linear_regression.pkl")
    dump(rf, models_dir / "random_forest.pkl")
    logger.info(f"Models saved to {models_dir}")

def main() -> int:
    start_time = time.time()
    set_resource_limits(n_jobs=2, memory_limit_mb=7000)

    clean_path = Path("data/processed/clean_mg_data.parquet")
    df = load_clean_data(clean_path)

    X, y, df_clean = prepare_features(df)

    # Split and persist splits (the split retains the target column)
    train_df, test_df = split_and_save(df_clean)

    # Align X/Y with the split DataFrames
    X_train = train_df[REQUIRED_FEATURES].values
    y_train = train_df[TARGET_COLUMN].values
    X_test = test_df[REQUIRED_FEATURES].values
    y_test = test_df[TARGET_COLUMN].values

    # Train models
    lr = train_linear_regression(X_train, y_train)
    rf, best_params = train_random_forest(X_train, y_train)

    # Save models
    save_models(lr, rf)

    # Basic training metrics
    metrics = {
        "linear_regression": {
            "r2_train": r2_score(y_train, lr.predict(X_train)),
            "mae_train": mean_absolute_error(y_train, lr.predict(X_train)),
        },
        "random_forest": {
            "r2_train": r2_score(y_train, rf.predict(X_train)),
            "mae_train": mean_absolute_error(y_train, rf.predict(X_train)),
            "best_params": best_params,
        },
    }
    results_path = Path("results/training_metrics.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Training metrics written to {results_path}")

    # Log runtime
    runtime = time.time() - start_time
    logger.info(f"Training pipeline completed in {runtime:.2f}s")
    return 0

if __name__ == "__main__":
    sys.exit(main())
