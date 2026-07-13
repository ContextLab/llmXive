from __future__ import annotations

import argparse
import csv
import os
import pickle
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

# Project imports based on API surface
from utils.reproducibility import set_seed
from training.split_data import get_train_test_splits
from training.evaluate import mae, rmse
from training.save_checkpoints import save_rf_checkpoint


def ensure_data_available() -> bool:
    """Verify that required processed data files exist."""
    required_files = [
        "data/processed/features_2d.parquet",
        "data/processed/molecules_10k.parquet"
    ]
    for f in required_files:
        if not Path(f).exists():
            print(f"Error: Required file {f} not found. Run data preprocessing first.")
            return False
    return True


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load features and target values from parquet files."""
    features_path = Path("data/processed/features_2d.parquet")
    molecules_path = Path("data/processed/molecules_10k.parquet")

    if not features_path.exists() or not molecules_path.exists():
        raise FileNotFoundError("Required data files missing. Run preprocessing scripts first.")

    features_df = pd.read_parquet(features_path)
    molecules_df = pd.read_parquet(molecules_path)

    # Ensure molecule_id is present in both for merging
    if "molecule_id" not in features_df.columns or "molecule_id" not in molecules_df.columns:
        raise ValueError("molecule_id column missing in data files")

    # Merge to get features with dipole moment
    merged = pd.merge(features_df, molecules_df[["molecule_id", "dipole"]], on="molecule_id")

    # Separate features and target
    feature_cols = [c for c in merged.columns if c not in ["molecule_id", "dipole"]]
    X = merged[feature_cols].fillna(0)
    y = merged["dipole"]

    return X, y


def train_one_seed(seed: int, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Dict[str, Any]:
    """Train a Random Forest model for a single seed and return metrics."""
    set_seed(seed)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train model
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=seed,
        n_jobs=1,  # Enforce single core for reproducibility in this context
        max_depth=10
    )
    model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    mae_score = mae(y_test.values, y_pred)
    rmse_score = rmse(y_test.values, y_pred)

    return {
        "seed": seed,
        "model": "random_forest",
        "mae": mae_score,
        "rmse": rmse_score,
        "model_object": model,
        "scaler": scaler,
        "config": {
            "n_estimators": 100,
            "max_depth": 10,
            "test_size": test_size
        }
    }


def write_metrics_csv(metrics_list: List[Dict[str, Any]], output_path: str) -> None:
    """Append metrics to the results CSV file."""
    file_exists = os.path.isfile(output_path)
    with open(output_path, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["seed", "model", "mae", "rmse"])
        if not file_exists:
            writer.writeheader()
        for m in metrics_list:
            writer.writerow({
                "seed": m["seed"],
                "model": m["model"],
                "mae": m["mae"],
                "rmse": m["rmse"]
            })


def save_checkpoints(metrics_list: List[Dict[str, Any]], checkpoint_dir: str) -> None:
    """Save model and scaler for each seed."""
    Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
    for m in metrics_list:
        path = Path(checkpoint_dir) / f"rf_seed_{m['seed']}.pkl"
        save_rf_checkpoint(m["model_object"], m["scaler"], m["config"], m["seed"], path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Random Forest baseline for dipole prediction")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 456, 789, 1011],
                      help="List of random seeds to use for training")
    parser.add_argument("--output", type=str, default="results/metrics.csv",
                      help="Path to output metrics CSV")
    parser.add_argument("--checkpoints", type=str, default="data/checkpoints",
                      help="Directory to save model checkpoints")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not ensure_data_available():
        sys.exit(1)

    print("Loading data...")
    X, y = load_data()
    print(f"Data loaded: {X.shape[0]} samples, {X.shape[1]} features")

    results = []
    for seed in args.seeds:
        print(f"Training with seed {seed}...")
        try:
            result = train_one_seed(seed, X, y)
            results.append(result)
            print(f"  Seed {seed} -> MAE: {result['mae']:.4f}, RMSE: {result['rmse']:.4f}")
        except Exception as e:
            print(f"  Error training seed {seed}: {e}")
            continue

    if not results:
        print("No models trained successfully.")
        sys.exit(1)

    # Calculate RMSE variance across seeds as required by task
    rmse_values = [r["rmse"] for r in results]
    rmse_variance = np.var(rmse_values)
    print(f"RMSE Variance across seeds: {rmse_variance:.6f}")

    # Write metrics
    write_metrics_csv(results, args.output)
    print(f"Metrics written to {args.output}")

    # Save checkpoints
    save_checkpoints(results, args.checkpoints)
    print(f"Checkpoints saved to {args.checkpoints}")


if __name__ == "__main__":
    main()