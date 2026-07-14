"""
Train a Random Forest baseline on the processed QM9 subset.

This script:
  * Ensures the required processed data file exists.
  * Loads the feature matrix (2‑D Morgan fingerprints) and dipole targets.
  * Generates an identical train/test split for each of five seeds.
  * Trains a ``RandomForestRegressor`` for each seed.
  * Computes MAE and RMSE on the held‑out test set.
  * Writes per‑seed metrics to ``results/metrics.csv``.
  * Computes the variance (and 95 % bootstrap CI) of RMSE across seeds
    and records it in ``results/variance_rf.csv``.
  * Saves a model checkpoint for each seed under ``data/checkpoints/``.

The script is deliberately self‑contained and only uses the public API
defined elsewhere in the repository (e.g., ``set_seed`` from
``utils.reproducibility`` and the ``mae``/``rmse`` helpers from
``training.evaluate``).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
from pathlib import Path
from typing import List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# Local imports (public API surface)
from utils.reproducibility import set_seed
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from training.save_checkpoints import save_rf_checkpoint

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def ensure_dir(path: Path) -> None:
    """Create ``path`` (including parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def ensure_data_available() -> Path:
    """
    Verify that the processed QM9 subset exists.

    Returns
    -------
    Path
        Path to ``data/processed/molecules_10k.parquet``.

    Raises
    ------
    FileNotFoundError
        If the file is missing.
    """
    data_path = Path("data/processed/molecules_10k.parquet")
    if not data_path.is_file():
        raise FileNotFoundError(
            f"Required processed data not found: {data_path}. "
            "Run `python code/data/generate_processed_data.py` first."
        )
    return data_path


def load_data(parquet_path: Path) -> pd.DataFrame:
    """
    Load the processed dataset.

    The file is expected to contain at least two columns:
        * ``features_2d`` – a list‑like representation of the 2‑D fingerprint.
        * ``dipole`` – the target dipole moment (float).

    Returns
    -------
    pd.DataFrame
    """
    df = pd.read_parquet(parquet_path)
    # Ensure the fingerprint column is a proper NumPy array for sklearn.
    if "features_2d" in df.columns:
        df["features_2d"] = df["features_2d"].apply(
            lambda x: np.asarray(x, dtype=np.float32)
        )
    return df


def write_metrics_header_if_needed(csv_path: Path) -> None:
    """Create ``results/metrics.csv`` with a header if it does not exist."""
    ensure_dir(csv_path.parent)
    if not csv_path.is_file():
        with csv_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["seed", "model", "mae", "rmse"]
            )  # simple header – CI is added later by other scripts


def append_metrics_row(csv_path: Path, row: Tuple[int, str, float, float]) -> None:
    """Append a single metric row to ``results/metrics.csv``."""
    with csv_path.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def compute_bootstrap_ci(
    values: List[float],
    n_bootstrap: int = 10_000,
    confidence: float = 0.95,
) -> Tuple[float, float]:
    """
    Compute a percentile bootstrap confidence interval.

    Parameters
    ----------
    values : List[float]
        Metric values (e.g., RMSE) across seeds.
    n_bootstrap : int
        Number of bootstrap resamples.
    confidence : float
        Desired confidence level (default 0.95).

    Returns
    -------
    Tuple[float, float]
        Lower and upper bounds of the CI.
    """
    rng = np.random.default_rng(42)
    boot_means = [
        np.mean(rng.choice(values, size=len(values), replace=True))
        for _ in range(n_bootstrap)
    ]
    lower = np.percentile(boot_means, (1 - confidence) / 2 * 100)
    upper = np.percentile(boot_means, (1 + confidence) / 2 * 100)
    return float(lower), float(upper)


def write_variance_file(
    csv_path: Path,
    rmse_values: List[float],
    mae_values: List[float],
) -> None:
    """
    Record variance statistics for the Random Forest baseline.

    The file ``results/variance_rf.csv`` will contain:
        seed, model, metric, variance, ci_lower, ci_upper

    For this task we only write the RMSE variance (as required by the
    user story) but also include MAE for completeness.
    """
    ensure_dir(csv_path.parent)
    rmse_var = float(np.var(rmse_values, ddof=1))
    mae_var = float(np.var(mae_values, ddof=1))
    rmse_ci = compute_bootstrap_ci(rmse_values)
    mae_ci = compute_bootstrap_ci(mae_values)

    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "model",
                "metric",
                "variance",
                "ci_lower",
                "ci_upper",
            ]
        )
        writer.writerow(
            ["RandomForest", "RMSE", rmse_var, rmse_ci[0], rmse_ci[1]]
        )
        writer.writerow(
            ["RandomForest", "MAE", mae_var, mae_ci[0], mae_ci[1]]
        )


def train_one_seed(
    seed: int,
    df: pd.DataFrame,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
) -> Tuple[float, float]:
    """
    Train a RandomForestRegressor on a single seed split.

    Returns
    -------
    Tuple[float, float]
        (MAE, RMSE) on the test set.
    """
    # Set deterministic seeds
    set_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    X = np.stack(df.loc[:, "features_2d"].values)
    y = df["dipole"].values.astype(np.float32)

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Initialise and train the model
    rf = RandomForestRegressor(
        n_estimators=200,
        random_state=seed,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)

    # Predictions and metrics
    preds = rf.predict(X_test)
    test_mae = mae(y_test, preds)
    test_rmse = rmse(y_test, preds)

    # Save checkpoint
    checkpoint_path = Path(
        f"data/checkpoints/rf_seed_{seed}.pkl"
    )
    ensure_dir(checkpoint_path.parent)
    save_rf_checkpoint(
        checkpoint_path,
        model=rf,
        seed=seed,
        train_metrics={"mae": test_mae, "rmse": test_rmse},
    )

    return float(test_mae), float(test_rmse)


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Random Forest baseline on QM9 subset."
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[0, 1, 2, 3, 4],
        help="Random seeds to use for the experiment.",
    )
    parser.add_argument(
        "--output-metrics",
        type=str,
        default="results/metrics.csv",
        help="CSV file to which per‑seed metrics are written.",
    )
    parser.add_argument(
        "--output-variance",
        type=str,
        default="results/variance_rf.csv",
        help="CSV file containing variance and CI of metrics.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ------------------------------------------------------------------- #
    # Data preparation
    # ------------------------------------------------------------------- #
    processed_path = ensure_data_available()
    df = load_data(processed_path)

    # ------------------------------------------------------------------- #
    # Train / test split generation (identical across seeds)
    # ------------------------------------------------------------------- #
    # ``get_train_test_splits`` returns a list of (train_idx, test_idx) tuples,
    # one for each requested seed.  The implementation lives in
    # ``code/training/split_data.py`` and guarantees reproducibility.
    splits = get_train_test_splits(seeds=args.seeds)

    # ------------------------------------------------------------------- #
    # Metric collection
    # ------------------------------------------------------------------- #
    mae_values: List[float] = []
    rmse_values: List[float] = []

    metrics_csv = Path(args.output_metrics)
    write_metrics_header_if_needed(metrics_csv)

    for seed, (train_idx, test_idx) in zip(args.seeds, splits):
        seed_mae, seed_rmse = train_one_seed(seed, df, train_idx, test_idx)
        mae_values.append(seed_mae)
        rmse_values.append(seed_rmse)
        append_metrics_row(
            metrics_csv,
            (seed, "RandomForest", seed_mae, seed_rmse),
        )
        print(
            f"[seed {seed}] MAE: {seed_mae:.4f} | RMSE: {seed_rmse:.4f}"
        )

    # ------------------------------------------------------------------- #
    # Variance / CI computation
    # ------------------------------------------------------------------- #
    variance_csv = Path(args.output_variance)
    write_variance_file(variance_csv, rmse_values, mae_values)
    print(f"Variance and confidence intervals written to {variance_csv}")


if __name__ == "__main__":
    main()