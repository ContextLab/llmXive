"""
Train a Random Forest baseline on the QM9 dipole‑moment dataset.

This script:
  * Loads the processed feature parquet files (2‑D and 3‑D) together with
    the target dipole moment.
  * Generates identical train/test splits for a configurable number of
    random seeds (default 5) using ``training.split_data.get_train_test_splits``.
  * Trains a ``sklearn.ensemble.RandomForestRegressor`` for each seed.
  * Computes MAE and RMSE on the held‑out test set via ``training.evaluate``.
  * Writes per‑seed metrics to ``results/metrics.csv``.
  * After all seeds are processed, writes the variance of the RMSE values to
    ``results/rf_rmse_variance.csv``.

The script is intended to be executed from the project root:
    python code/training/train_rf.py
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import sys
from typing import List

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor

# Local imports – these modules are part of the project API surface.
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from training.save_checkpoints import save_rf_checkpoint

# --------------------------------------------------------------------------- #
# Utility helpers
# --------------------------------------------------------------------------- #

def ensure_dir(path: pathlib.Path) -> None:
    """Create ``path`` (including parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def write_metrics_header_if_needed(csv_path: pathlib.Path) -> None:
    """Write the CSV header for ``results/metrics.csv`` if the file is new."""
    if not csv_path.exists():
        with csv_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["seed", "model", "mae", "rmse"]
            )

def append_metrics_row(csv_path: pathlib.Path, seed: int, mae_val: float, rmse_val: float) -> None:
    """Append a single row of metrics for a given seed."""
    with csv_path.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

def write_rmse_variance(csv_path: pathlib.Path, rmse_values: List[float]) -> None:
    """
    Write a CSV containing the variance (and standard deviation) of the RMSE
    values observed across all seeds.
    """
    variance = np.var(rmse_values, ddof=1)  # sample variance
    std_dev = np.sqrt(variance)
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["rmse_variance", f"{variance:.6f}"])
        writer.writerow(["rmse_std_dev", f"{std_dev:.6f}"])

# --------------------------------------------------------------------------- #
# Core training logic
# --------------------------------------------------------------------------- #

def load_dataset(
    molecules_path: pathlib.Path,
    features_2d_path: pathlib.Path,
    features_3d_path: pathlib.Path,
) -> pd.DataFrame:
    """
    Load the processed dataset and return a single DataFrame containing:
        - ``molecule_id`` (string)
        - ``dipole`` (float, target)
        - ``features_2d`` (list of floats)
        - ``features_3d`` (list of floats)
    The function expects the feature parquet files to contain a column named
    ``features`` holding a list‑like object.
    """
    # Load the main molecule table – it contains ``molecule_id`` and ``dipole``.
    molecules_df = pd.read_parquet(molecules_path)

    # Load feature tables.
    feats_2d = pd.read_parquet(features_2d_path).rename(columns={"features": "features_2d"})
    feats_3d = pd.read_parquet(features_3d_path).rename(columns={"features": "features_3d"})

    # Merge on ``molecule_id``.
    df = molecules_df.merge(feats_2d, on="molecule_id", how="inner")
    df = df.merge(feats_3d, on="molecule_id", how="inner")

    # Ensure the target column is present.
    if "dipole" not in df.columns:
        raise KeyError("Target column 'dipole' not found in the molecules parquet file.")

    return df

def train_one_seed(
    seed: int,
    df: pd.DataFrame,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    checkpoint_dir: pathlib.Path,
) -> dict:
    """
    Train a Random Forest on the training split for a single seed and return
    a dictionary with ``mae`` and ``rmse`` for the test split.
    """
    # Set the random state for reproducibility.
    rng = np.random.default_rng(seed)

    # Extract features – we concatenate 2‑D and 3‑D descriptors.
    X = np.stack(
        df.loc[:, ["features_2d", "features_3d"]].apply(
            lambda row: np.concatenate([np.asarray(row["features_2d"]), np.asarray(row["features_3d"])]),
            axis=1,
        )
    )
    y = df["dipole"].to_numpy()

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Initialise and train the model.
    rf = RandomForestRegressor(
        n_estimators=200,
        random_state=seed,
        n_jobs=1,  # Respect the CPU‑limit decorator elsewhere in the pipeline.
    )
    rf.fit(X_train, y_train)

    # Predictions and metrics.
    y_pred = rf.predict(X_test)
    mae_val = mae(y_test, y_pred)
    rmse_val = rmse(y_test, y_pred)

    # Save a checkpoint for reproducibility.
    checkpoint_path = checkpoint_dir / f"rf_seed_{seed}.pkl"
    save_rf_checkpoint(rf, checkpoint_path, seed, {"model": "RandomForest"})

    return {"mae": mae_val, "rmse": rmse_val}

# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #

def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Random Forest baseline on QM9 dipole moments."
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=5,
        help="Number of random seeds / independent training runs (default: 5).",
    )
    parser.add_argument(
        "--molecules",
        type=pathlib.Path,
        default=pathlib.Path("data/processed/molecules_10k.parquet"),
        help="Path to the processed molecules parquet file.",
    )
    parser.add_argument(
        "--features-2d",
        type=pathlib.Path,
        default=pathlib.Path("data/processed/features_2d.parquet"),
        help="Path to the 2‑D feature parquet file.",
    )
    parser.add_argument(
        "--features-3d",
        type=pathlib.Path,
        default=pathlib.Path("data/processed/features_3d.parquet"),
        help="Path to the 3‑D feature parquet file.",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("results"),
        help="Directory where metrics and variance CSV files will be written.",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=pathlib.Path,
        default=pathlib.Path("data/checkpoints"),
        help="Directory to store model checkpoint files.",
    )
    return parser.parse_args(argv)

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)

    # Ensure required output directories exist.
    ensure_dir(args.output_dir)
    ensure_dir(args.checkpoint_dir)

    # Load the dataset – this will raise a clear error if the expected file
    # does not exist, satisfying the quick‑start validation step.
    df = load_dataset(args.molecules, args.features_2d, args.features_3d)

    # Prepare the CSV for metrics.
    metrics_csv = args.output_dir / "metrics.csv"
    write_metrics_header_if_needed(metrics_csv)

    # Collect RMSE values for variance computation.
    rmse_values: List[float] = []

    # Generate identical train/test splits for each seed.
    splits = get_train_test_splits(df.shape[0], n_seeds=args.seeds, test_size=0.2, random_state=42)

    for seed_idx, (train_idx, test_idx) in enumerate(splits, start=1):
        results = train_one_seed(
            seed=seed_idx,
            df=df,
            train_idx=train_idx,
            test_idx=test_idx,
            checkpoint_dir=args.checkpoint_dir,
        )
        mae_val = results["mae"]
        rmse_val = results["rmse"]
        rmse_values.append(rmse_val)

        # Record per‑seed metrics.
        append_metrics_row(metrics_csv, seed_idx, mae_val, rmse_val)

    # After all seeds have run, write the variance summary.
    variance_csv = args.output_dir / "rf_rmse_variance.csv"
    write_rmse_variance(variance_csv, rmse_values)

    return 0

if __name__ == "__main__":
    sys.exit(main())
