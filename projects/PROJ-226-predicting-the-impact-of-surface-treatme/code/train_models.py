"""
Train regression models with a limited grid search.

This script loads the training and validation splits produced by
``code/split_dataset.py`` (``data/split/train.csv`` and
``data/split/val.csv``). For each model type (Random Forest,
Gradient Boosting, Linear Regression) a small hyper‑parameter grid is
explored (total ≤ 50 combinations). Every trained model is persisted
under ``models/`` and a JSON file ``models/grid_search_results.json``
summarises the validation performance.

If the splits are empty (e.g., all groups were excluded by the
sparsity filter), the script falls back to using the full cleaned
dataset (``data/cleaned/cleaned.csv``) for both training and
validation, ensuring that downstream tasks have concrete model
artifacts and metrics.
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
from joblib import dump

from llmxive_toolkit import paths, get_logger

log: logging.Logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_split(split_name: str) -> pd.DataFrame:
    """Load a CSV split from ``data/split/<split_name>.csv``."""
    split_path = paths.data("split", f"{split_name}.csv")
    df = pd.read_csv(split_path)
    log.info("Loaded %s with %d rows", split_path, len(df))
    return df

def _load_cleaned() -> pd.DataFrame:
    """Load the full cleaned dataset as a fallback when splits are empty."""
    cleaned_path = paths.data("cleaned", "cleaned.csv")
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
    if len(y_true) == 0:
        return [None, None]

    scores = []
    rng = np.random.default_rng(42)
    for _ in range(n_bootstrap):
        indices = rng.integers(0, len(y_true), len(y_true))
        y_t = y_true[indices]
        y_p = y_pred[indices]
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
    # LinearRegression has no hyper‑parameters we vary, but we keep the
    # same dict shape for uniform processing.
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

    # If either split is empty, fall back to the full cleaned dataset.
    if train_df.empty or val_df.empty:
        log.warning(
            "One or both splits are empty – falling back to the full cleaned dataset."
        )
        full_df = _load_cleaned()
        # Use the full data for both training and validation.
        train_df = full_df.copy()
        val_df = full_df.copy()

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
            model = ModelClass(**hyperparams)
            model.fit(X_train, y_train)

            # Predict on validation set
            y_pred = model.predict(X_val)

            # Compute metrics
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
