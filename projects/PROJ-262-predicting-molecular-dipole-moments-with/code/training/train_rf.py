from __future__ import annotations

import argparse
import csv
import os
import pickle
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from utils.reproducibility import set_seed
from training.evaluate import mae, rmse

# Constants
DATA_DIR = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/data/processed")
RESULTS_DIR = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/results")
CHECKPOINT_DIR = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/data/checkpoints")

def ensure_data_available() -> bool:
    """Check if required data files exist."""
    features_path = DATA_DIR / "features_2d.parquet"
    if not features_path.exists():
        print(f"Error: {features_path} not found. Run data processing first.")
        return False
    return True

def load_data() -> Tuple[pd.DataFrame, pd.Series]:
    """Load the 2D features and dipole moments."""
    features_path = DATA_DIR / "features_2d.parquet"
    df = pd.read_parquet(features_path)

    # Ensure we have the target column
    if "dipole" not in df.columns:
        raise ValueError("DataFrame must contain 'dipole' column")

    X = df.drop(columns=["dipole", "molecule_id"])
    y = df["dipole"]

    return X, y

def train_one_seed(seed: int, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """Train a single Random Forest model with a specific seed."""
    set_seed(seed)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed
    )

    # Initialize model
    rf_model = RandomForestRegressor(
        n_estimators=100,
        random_state=seed,
        n_jobs=1,  # Enforce single core for reproducibility in this context
        max_depth=10
    )

    # Train
    start_time = time.time()
    rf_model.fit(X_train, y_train)
    train_time = time.time() - start_time

    # Evaluate
    y_pred = rf_model.predict(X_test)
    m = mae(y_test, y_pred)
    r = rmse(y_test, y_pred)

    return {
        "seed": seed,
        "model": "RandomForest",
        "mae": float(m),
        "rmse": float(r),
        "train_time": train_time,
        "model": rf_model
    }

def write_metrics_csv(metrics_list: List[Dict[str, Any]]) -> None:
    """Write metrics to results/metrics.csv with confidence intervals."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = RESULTS_DIR / "metrics.csv"

    # Calculate confidence intervals via bootstrap
    rmse_values = [m["rmse"] for m in metrics_list]
    mae_values = [m["mae"] for m in metrics_list]

    # Simple bootstrap CI (1000 iterations)
    np.random.seed(42)
    n_bootstrap = 1000
    bootstrap_rmse = []
    bootstrap_mae = []

    for _ in range(n_bootstrap):
        indices = np.random.choice(len(rmse_values), len(rmse_values), replace=True)
        bootstrap_rmse.append(np.mean([rmse_values[i] for i in indices]))
        bootstrap_mae.append(np.mean([mae_values[i] for i in indices]))

    rmse_ci_lower = float(np.percentile(bootstrap_rmse, 2.5))
    rmse_ci_upper = float(np.percentile(bootstrap_rmse, 97.5))
    mae_ci_lower = float(np.percentile(bootstrap_mae, 2.5))
    mae_ci_upper = float(np.percentile(bootstrap_mae, 97.5))

    # Write CSV
    with open(metrics_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "model", "mae", "rmse",
            "mae_ci_lower", "mae_ci_upper",
            "rmse_ci_lower", "rmse_ci_upper"
        ])

        # Write individual seed metrics
        for m in metrics_list:
            writer.writerow([
                m["seed"], m["model"], m["mae"], m["rmse"],
                mae_ci_lower, mae_ci_upper,
                rmse_ci_lower, rmse_ci_upper
            ])

    print(f"Metrics written to {metrics_path}")

def save_checkpoints(metrics_list: List[Dict[str, Any]]) -> None:
    """Save model checkpoints."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    for m in metrics_list:
        checkpoint_path = CHECKPOINT_DIR / f"rf_seed_{m['seed']}.pkl"
        checkpoint_data = {
            "model": m["model"],
            "seed": m["seed"],
            "config": {
                "n_estimators": 100,
                "max_depth": 10
            },
            "metrics": {
                "mae": m["mae"],
                "rmse": m["rmse"]
            },
            "timestamp": datetime.now().isoformat()
        }
        with open(checkpoint_path, "wb") as f:
            pickle.dump(checkpoint_data, f)
        print(f"Checkpoint saved: {checkpoint_path}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Random Forest baseline")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 456, 789, 101112],
                      help="List of random seeds to use")
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    if not ensure_data_available():
        return

    X, y = load_data()
    print(f"Loaded {len(y)} samples for Random Forest training")

    metrics_list = []
    for seed in args.seeds:
        print(f"Training with seed {seed}...")
        result = train_one_seed(seed, X, y)
        metrics_list.append(result)
        print(f"  Seed {seed}: MAE={result['mae']:.4f}, RMSE={result['rmse']:.4f}")

    # Calculate and record RMSE variance
    rmse_values = [m["rmse"] for m in metrics_list]
    rmse_variance = float(np.var(rmse_values))
    print(f"RMSE Variance across seeds: {rmse_variance:.6f}")

    # Write outputs
    write_metrics_csv(metrics_list)
    save_checkpoints(metrics_list)

    print("Random Forest training complete.")

if __name__ == "__main__":
    main()