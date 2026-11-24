"""
Train regression models with a limited grid search.

This script loads the training and validation splits produced by
``code/split_dataset.py`` (``data/split/train.csv`` and
``data/split/val.csv``). For each model type (Random Forest,
Gradient Boosting, Linear Regression) a small hyper‑parameter grid is
explored (total ≤ 50 combinations). Every trained model is persisted
under ``models/`` and a JSON file ``models/grid_search_results.json``
summarises the validation performance.

If the splits are empty or missing (e.g., due to sparsity filtering), the 
script falls back to using the full cleaned dataset (``data/cleaned/cleaned.csv``),
performing a simple 80/20 split to ensure that the validation set is 
distinct from the training set, avoiding degenerate metrics.
"""

import json
import itertools
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from joblib import dump

from llmxive_toolkit import paths, get_logger

log: logging.Logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_split(split_name: str) -> pd.DataFrame:
    """Load a CSV split from ``data/split/<split_name>.csv``."""
    split_path = paths.data("split", f"{split_name}.csv")
    if not split_path.exists():
        log.warning("Split file %s not found.", split_path)
        return pd.DataFrame()
    df = pd.read_csv(split_path)
    log.info("Loaded %s with %d rows", split_path, len(df))
    return df

def _load_cleaned() -> pd.DataFrame:
    """Load the full cleaned dataset."""
    cleaned_path = paths.data("cleaned", "cleaned.csv")
    if not cleaned_path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {cleaned_path}")
    df = pd.read_csv(cleaned_path)
    log.info("Loaded cleaned dataset %s with %d rows", cleaned_path, len(df))
    return df

def _bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bootstrap: int = 10_000,
    ci: float = 0.95,
) -> list[float]:
    """Return lower/upper bounds of a bootstrapped confidence interval for R²."""
    if len(y_true) < 2:
        # R2 is undefined for a single sample
        return [float('nan'), float('nan')]

    scores = []
    rng = np.random.default_rng(42)
    for _ in range(n_bootstrap):
        indices = rng.integers(0, len(y_true), len(y_true))
        y_t = y_true[indices]
        y_p = y_pred[indices]
        # Handle cases where bootstrap sample has zero variance in y_t
        if np.var(y_t) == 0:
            scores.append(0.0)
        else:
            scores.append(r2_score(y_t, y_p))
    
    lower = np.percentile(scores, (1 - ci) / 2 * 100)
    upper = np.percentile(scores, (1 + ci) / 2 * 100)
    return [float(lower), float(upper)]

# ----------------------------------------------------------------------
# Model‑specific hyper‑parameter grids (kept small to respect the ≤ 50 limit)
# ----------------------------------------------------------------------
RF_GRID = {
    "n_estimators": [50, 100],
    "max_depth": [None, 10],
    "min_samples_split": [2, 5],
}

GB_GRID = {
    "n_estimators": [50, 100],
    "learning_rate": [0.1, 0.05],
    "max_depth": [3, 5],
}

LR_GRID = {
    "fit_intercept": [True],
}

MODEL_SPECS = [
    ("RandomForest", RandomForestRegressor, RF_GRID),
    ("GradientBoosting", GradientBoostingRegressor, GB_GRID),
    ("LinearRegression", LinearRegression, LR_GRID),
]

def _grid_combinations(grid: dict) -> list[dict]:
    """Return a list of all hyper‑parameter combinations for a grid."""
    keys = list(grid.keys())
    combos = list(itertools.product(*(grid[k] for k in keys)))
    return [dict(zip(keys, combo)) for combo in combos]

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    # Load data splits
    train_df = _load_split("train")
    val_df = _load_split("val")

    # If either split is empty or missing, fall back to cleaned data with a fresh split
    if train_df.empty or val_df.empty:
        log.warning(
            "One or both splits are empty or missing – performing 80/20 split on cleaned dataset."
        )
        full_df = _load_cleaned()
        
        # Ensure we have a target column
        target_col = "adhesion_strength_mj_m2"
        if target_col not in full_df.columns:
            raise KeyError(f"Target column {target_col} missing from cleaned dataset.")

        # Split the full cleaned dataset to ensure training and validation are distinct
        train_df, val_df = train_test_split(
            full_df, test_size=0.2, random_state=42
        )
        log.info("Fallback split: train=%d, val=%d", len(train_df), len(val_df))

    # Identify target and feature columns
    target_col = "adhesion_strength_mj_m2"
    feature_cols = [c for c in train_df.columns if c != target_col]

    X_train = train_df[feature_cols].to_numpy()
    y_train = train_df[target_col].to_numpy()
    X_val = val_df[feature_cols].to_numpy()
    y_val = val_df[target_col].to_numpy()

    all_results = []
    model_counter = 0

    for model_name, ModelClass, grid in MODEL_SPECS:
        combos = _grid_combinations(grid)
        # Ensure we respect the overall 50‑combo limit
        if model_counter + len(combos) > 50:
            allowed = 50 - model_counter
            combos = combos[:allowed]
        
        for hyperparams in combos:
            log.info(
                "Training %s with hyper‑parameters %s", model_name, hyperparams
            )
            model = ModelClass(**hyperparams, random_state=42) if 'random_state' in ModelClass().get_params() else ModelClass(**hyperparams)
            model.fit(X_train, y_train)

            # Predict on validation set
            y_pred = model.predict(X_val)

            # Compute metrics
            # Handle cases where y_val is too small for R2
            if len(y_val) < 2:
                val_r2 = 0.0
                val_rmse = float(np.sqrt(mean_squared_error(y_val, y_pred)))
                r2_ci = [float('nan'), float('nan')]
            else:
                val_r2 = float(r2_score(y_val, y_pred))
                val_rmse = float(np.sqrt(mean_squared_error(y_val, y_pred)))
                r2_ci = _bootstrap_ci(y_val, y_pred, n_bootstrap=10_000)

            # Persist model under the ``models`` directory
            model_filename = f"{model_name.lower()}_{model_counter:03d}.pkl"
            model_path = paths.models(model_filename)
            model_path.parent.mkdir(parents=True, exist_ok=True)
            dump(model, model_path)

            # Record result entry
            result_entry = {
                "model_type": model_name,
                "model_path": str(model_path.relative_to(paths.root)),
                "hyperparameters": hyperparams,
                "validation_r2": val_r2,
                "validation_rmse": val_rmse,
                "validation_r2_ci_95": r2_ci,
            }
            all_results.append(result_entry)

            model_counter += 1
            if model_counter >= 50:
                log.info("Reached the 50‑combination limit – stopping search.")
                break
        if model_counter >= 50:
            break

    # Write aggregated results under the ``models`` directory
    results_path = paths.models("grid_search_results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(all_results, indent=2))
    log.info(
        "Grid‑search completed – %d models evaluated. Results written to %s",
        len(all_results),
        results_path,
    )

if __name__ == "__main__":
    main()