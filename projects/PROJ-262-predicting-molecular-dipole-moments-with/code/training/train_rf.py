"""
Random Forest training script for the dipole‑moment prediction project.

This script:
  1. Loads the processed QM9 subset (``data/processed/molecules_10k.parquet``).
  2. For each of five seeds it:
     - Splits the data into train / test using the shared split logic.
     - Trains a ``sklearn.ensemble.RandomForestRegressor`` on the training set.
     - Evaluates MAE and RMSE on the test set.
     - Appends a row to ``results/metrics.csv``.
  3. After all seeds, computes the variance of the test RMSE values and
     writes it to ``data/reports/rmse_variance.csv``.
  4. Saves each model checkpoint as ``data/checkpoints/rf_seed_{seed}.pkl``.

The script is deliberately lightweight and CPU‑only to satisfy the
resource‑constraint decorators used elsewhere in the project.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Local utilities
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from training.save_checkpoints import save_rf_checkpoint
from utils.reproducibility import set_seed

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def ensure_dir(path: Path) -> None:
    """Create ``path`` (including parents) if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def write_metrics_header_if_needed(csv_path: Path) -> None:
    """Write the CSV header for ``results/metrics.csv`` if the file is new."""
    if not csv_path.exists():
        with csv_path.open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['seed', 'model', 'mae', 'rmse'])


def append_metrics_row(csv_path: Path, seed: int, mae_val: float, rmse_val: float) -> None:
    """Append a single metrics row for a given seed."""
    with csv_path.open('a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([seed, 'random_forest', f'{mae_val:.6f}', f'{rmse_val:.6f}'])


def write_rmse_variance(csv_path: Path, rmse_values: List[float]) -> None:
    """Write a one‑row CSV containing the variance of the RMSE values."""
    variance = pd.Series(rmse_values).var()
    with csv_path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['rmse_variance', f'{variance:.6f}'])


def load_dataset() -> pd.DataFrame:
    """
    Load the processed QM9 subset.

    Expected columns (at minimum):
      - ``molecule_id`` (string)
      - ``dipole`` (float) – target variable
      - any number of feature columns (numeric)
    """
    data_path = Path('data/processed/molecules_10k.parquet')
    if not data_path.is_file():
        raise FileNotFoundError(f'Processed data not found: {data_path}')
    df = pd.read_parquet(data_path)
    return df


def train_one_seed(seed: int, df: pd.DataFrame) -> Tuple[float, float, RandomForestRegressor]:
    """
    Train a Random Forest on a single seed.

    Returns:
      - MAE on the test split
      - RMSE on the test split
      - The fitted ``RandomForestRegressor`` model (for checkpointing)
    """
    set_seed(seed)

    # Split the data using the shared split utility.
    train_idx, test_idx = get_train_test_splits(df, seed=seed, test_frac=0.2)
    train_df = df.iloc[train_idx]
    test_df = df.iloc[test_idx]

    # Separate features and target.
    target_col = 'dipole'
    feature_cols = [c for c in df.columns if c not in ('molecule_id', target_col)]

    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values

    # Train the model.
    rf = RandomForestRegressor(
        n_estimators=200,
        random_state=seed,
        n_jobs=1,  # Respect the CPU‑limit decorator used elsewhere.
    )
    rf.fit(X_train, y_train)

    # Predictions and metrics.
    preds = rf.predict(X_test)
    mae_val = mae(y_test, preds)
    rmse_val = rmse(y_test, preds)

    return mae_val, rmse_val, rf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Train Random Forest baseline with 5 seeds and record metrics.'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Base directory for outputs (default: current working directory).',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.output_dir)

    # Ensure required directories exist.
    results_dir = base_dir / 'results'
    checkpoints_dir = base_dir / 'data' / 'checkpoints'
    reports_dir = base_dir / 'data' / 'reports'

    for d in (results_dir, checkpoints_dir, reports_dir):
        ensure_dir(d)

    # Paths for output files.
    metrics_csv = results_dir / 'metrics.csv'
    variance_csv = reports_dir / 'rmse_variance.csv'

    # Prepare the metrics CSV header.
    write_metrics_header_if_needed(metrics_csv)

    # Load the dataset once.
    df = load_dataset()

    # Train across five seeds.
    rmse_values: List[float] = []
    for seed in range(5):
        mae_val, rmse_val, model = train_one_seed(seed, df)
        rmse_values.append(rmse_val)

        # Record per‑seed metrics.
        append_metrics_row(metrics_csv, seed, mae_val, rmse_val)

        # Save the model checkpoint.
        checkpoint_path = checkpoints_dir / f'rf_seed_{seed}.pkl'
        save_rf_checkpoint(model, checkpoint_path, seed)

    # After all seeds, write the RMSE variance report.
    write_rmse_variance(variance_csv, rmse_values)

    print(f'Training complete. Metrics written to {metrics_csv}')
    print(f'RMSE variance written to {variance_csv}')


if __name__ == '__main__':
    main()
