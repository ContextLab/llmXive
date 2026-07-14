"""
Train a Random Forest baseline on the QM9 10k subset.

This script:

* Loads the processed dataset (``data/processed/molecules_10k.parquet``).
* For each of five reproducible seeds:
    - Splits the data into train / test using the shared split utility.
    - Trains a ``RandomForestRegressor``.
    - Evaluates MAE and RMSE on the test set.
    - Persists the trained model checkpoint.
    * Writes a row to ``results/metrics.csv``.
* After all seeds are processed, computes the variance of the RMSE values and
  writes it to ``results/rmse_variance.csv``.

The script is deliberately lightweight (CPU‑only) and respects the project's
reproducibility, time‑limit and resource‑constraint decorators via the existing
utility modules.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# Project utilities
from utils.reproducibility import set_seed
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from training.save_checkpoints import save_rf_checkpoint


def ensure_dir(path: Path) -> None:
    """Create parent directories for *path* if they do not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_metrics_header_if_needed(csv_path: Path) -> None:
    """Write the CSV header for the metrics file if the file does not exist."""
    if not csv_path.exists():
        ensure_dir(csv_path)
        with csv_path.open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['seed', 'model', 'mae', 'rmse'])


def append_metrics_row(csv_path: Path, seed: int, mae_val: float, rmse_val: float) -> None:
    """Append a single row of metrics for a given seed."""
    with csv_path.open('a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([seed, 'random_forest', f"{mae_val:.6f}", f"{rmse_val:.6f}"])


def write_rmse_variance(csv_path: Path, rmse_values: List[float]) -> None:
    """
    Write the variance (and standard deviation) of RMSE across seeds.

    The file contains a single row with columns:
    ``seed_count, rmse_variance, rmse_std``.
    """
    variance = np.var(rmse_values, ddof=1)  # unbiased estimator
    std_dev = np.sqrt(variance)
    ensure_dir(csv_path)
    with csv_path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['seed_count', 'rmse_variance', 'rmse_std'])
        writer.writerow([len(rmse_values), f"{variance:.6f}", f"{std_dev:.6f}"])


def load_dataset() -> pd.DataFrame:
    """
    Load the pre‑processed QM9 subset.

    Expected columns:
    - ``molecule_id`` (str)
    - ``dipole`` (float) – target
    - ``features_2d`` (list of float) – optional
    - ``features_3d`` (list of float) – optional

    The function returns a DataFrame where ``features`` is a 2‑D NumPy array
    suitable for scikit‑learn.
    """
    data_path = Path('data/processed/molecules_10k.parquet')
    if not data_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {data_path}")
    df = pd.read_parquet(data_path)

    # Prefer 3‑D features if they exist; otherwise fall back to 2‑D.
    if 'features_3d' in df.columns:
        feature_col = 'features_3d'
    elif 'features_2d' in df.columns:
        feature_col = 'features_2d'
    else:
        raise KeyError("Neither 'features_3d' nor 'features_2d' columns found in dataset.")

    # Convert list‑like feature column to a 2‑D NumPy array.
    X = np.vstack(df[feature_col].values)
    y = df['dipole'].values.astype(float)
    return pd.DataFrame({'X': list(X), 'y': y, 'molecule_id': df['molecule_id']})


def train_one_seed(seed: int, dataset: pd.DataFrame, metrics_path: Path) -> Tuple[float, float]:
    """
    Train a Random Forest on a single seed and record metrics.

    Returns a tuple ``(mae, rmse)`` for the test split.
    """
    set_seed(seed)

    # Split indices using the shared utility to guarantee identical splits across models.
    train_idx, test_idx = get_train_test_splits(
        n_samples=len(dataset),
        test_size=0.2,
        random_state=seed
    )

    X = np.vstack(dataset['X'].values)
    y = dataset['y'].values

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Train the model.
    rf = RandomForestRegressor(
        n_estimators=200,
        random_state=seed,
        n_jobs=1  # respect the CPU‑limit decorator elsewhere in the repo
    )
    rf.fit(X_train, y_train)

    # Evaluate.
    y_pred = rf.predict(X_test)
    mae_val = mae(y_test, y_pred)
    rmse_val = rmse(y_test, y_pred)

    # Persist checkpoint.
    checkpoint_path = Path(f"data/checkpoints/rf_seed_{seed}.pkl")
    save_rf_checkpoint(rf, checkpoint_path, seed)

    # Record metrics.
    append_metrics_row(metrics_path, seed, mae_val, rmse_val)

    return mae_val, rmse_val


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Random Forest baseline on QM9 10k subset."
    )
    parser.add_argument(
        "--metrics-output",
        type=Path,
        default=Path("results/metrics.csv"),
        help="Path to CSV file where per‑seed metrics are stored."
    )
    parser.add_argument(
        "--variance-output",
        type=Path,
        default=Path("results/rmse_variance.csv"),
        help="Path to CSV file where RMSE variance across seeds is stored."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Ensure output directories exist.
    ensure_dir(args.metrics_output)
    ensure_dir(args.variance_output)

    # Prepare the metrics file.
    write_metrics_header_if_needed(args.metrics_output)

    # Load data.
    dataset = load_dataset()

    # Train across 5 seeds.
    rmse_values: List[float] = []
    for seed in range(5):
        _, rmse_val = train_one_seed(seed, dataset, args.metrics_output)
        rmse_values.append(rmse_val)

    # Write variance information.
    write_rmse_variance(args.variance_output, rmse_values)


if __name__ == "__main__":
    main()
