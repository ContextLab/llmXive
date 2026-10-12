"""
Model training utilities.

The ``main`` function now trains RandomForest and GradientBoosting models,
evaluates them on the full dataset, and writes a JSON results file
``data/processed/model_results.json`` compatible with the contract schema.
"""

import os
import json
import logging
import argparse

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

try:
    from code.config import SEED, OUTLIER_SIGMA, TARGET_VAR
except Exception:
    SEED = 42
    OUTLIER_SIGMA = 3.0
    TARGET_VAR = "conductivity"

def load_data() -> pd.DataFrame:
    """Load the processed descriptor table."""
    path = paths.data("processed", "descriptors.csv")
    if not path.exists():
        raise FileNotFoundError(f"Descriptor file not found: {path}")
    return pd.read_csv(path)

def select_target(df: pd.DataFrame) -> str:
    """Pick the appropriate target column."""
    candidates = [
        "log_conductivity",
        "log_conductivity_proxy",
        "conductivity",
        "log_conductivity_proxy",
    ]
    for cand in candidates:
        if cand in df.columns:
            return cand
    raise ValueError("No suitable target column found.")

def prepare_features(df: pd.DataFrame, target_col: str):
    """Return X, y after dropping non‑numeric columns."""
    y = df[target_col]
    X = df.drop(columns=[target_col, "smiles"], errors="ignore")
    X = X.select_dtypes(include=[np.number])
    return X, y

def train_and_evaluate(X, y):
    """Train RF and GB, evaluate on a held‑out test split."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED
    )

    models = {
        "random_forest": RandomForestRegressor(
            n_estimators=200, random_state=SEED, n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=200, learning_rate=0.1, random_state=SEED
        ),
    }

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        results[name] = {
            "r2_test": r2,
            "mae_test": mae,
            "outlier_threshold": OUTLIER_SIGMA,
        }
        log.info(f"{name}: R2={r2:.4f}, MAE={mae:.4f}")

    return results

def write_results(results: dict) -> None:
    out_path = paths.data("processed", "model_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    log.info(f"Model results written to {out_path}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true", help="Trigger training")
    args = parser.parse_args()

    df = load_data()
    target_col = select_target(df)
    X, y = prepare_features(df, target_col)

    if args.train:
        results = train_and_evaluate(X, y)
        write_results(results)
    else:
        log.info("Training not requested; exiting without action.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
