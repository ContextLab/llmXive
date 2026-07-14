"""
Random Forest training script for the dipole‑moment prediction project.

This script trains a scikit‑learn RandomForestRegressor on the 2‑D feature set
extracted from the QM9 subset. It runs for a configurable number of seeds
(default: 5), records MAE and RMSE for each seed, writes per‑seed metrics
to ``results/metrics.csv`` and finally computes the variance (and 95 % confidence
interval) of the RMSE across seeds, storing the result in ``results/rf_variance.csv``.
Model checkpoints are saved under ``data/checkpoints/``.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pickle
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

# Local utilities
from training.save_checkpoints import save_rf_checkpoint
from training.split_data import get_train_test_splits

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def ensure_dir(path: Path) -> None:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def ensure_data_available() -> Tuple[Path, Path, Path]:
    """
    Verify that the required processed data files exist.

    Returns
    -------
    Tuple[Path, Path, Path]
        Paths to ``molecules_10k.parquet``, ``features_2d.parquet`` and
        ``features_3d.parquet`` (the latter is not used here but is part of the
        project contract).
    """
    data_dir = Path("data/processed")
    molecules_path = data_dir / "molecules_10k.parquet"
    features_2d_path = data_dir / "features_2d.parquet"
    features_3d_path = data_dir / "features_3d.parquet"

    missing = [p for p in (molecules_path, features_2d_path, features_3d_path) if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required processed data files: {missing}")

    return molecules_path, features_2d_path, features_3d_path


def load_data(
    molecules_path: Path, features_2d_path: Path
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load feature matrix ``X`` and target vector ``y``.

    Parameters
    ----------
    molecules_path : Path
        Parquet file containing at least ``molecule_id`` and ``dipole`` columns.
    features_2d_path : Path
        Parquet file containing ``molecule_id`` and the 2‑D descriptor columns.

    Returns
    -------
    X : np.ndarray
        Feature matrix (n_samples, n_features).
    y : np.ndarray
        Target dipole moments (n_samples, ).
    ids : List[str]
        List of molecule identifiers (preserved for checkpointing).
    """
    mol_df = pd.read_parquet(molecules_path)
    feat_df = pd.read_parquet(features_2d_path)

    # Ensure the identifier column exists in both.
    if "molecule_id" not in mol_df.columns or "molecule_id" not in feat_df.columns:
        raise KeyError("Both data files must contain a 'molecule_id' column.")

    # Join on molecule_id to align features with targets.
    merged = pd.merge(mol_df[["molecule_id", "dipole"]], feat_df, on="molecule_id", how="inner")
    if merged.empty:
        raise ValueError("Joined feature/target dataframe is empty. Check data integrity.")

    ids = merged["molecule_id"].tolist()
    y = merged["dipole"].to_numpy(dtype=np.float64)
    X = merged.drop(columns=["molecule_id", "dipole"]).to_numpy(dtype=np.float64)

    return X, y, ids


def write_metrics_header_if_needed(csv_path: Path) -> None:
    """Create the CSV header for the metrics file if it does not already exist."""
    if not csv_path.is_file():
        with csv_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["seed", "model", "mae", "rmse"])


def append_metrics_row(csv_path: Path, seed: int, mae_val: float, rmse_val: float) -> None:
    """Append a single row of metrics to the CSV file."""
    with csv_path.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([seed, "RandomForest", f"{mae_val:.6f}", f"{rmse_val:.6f}"])


def compute_bootstrap_ci(
    values: List[float], n_bootstrap: int = 1000, confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Compute a non‑parametric bootstrap confidence interval for a list of values.

    Parameters
    ----------
    values : List[float]
        Metric values (e.g., RMSE across seeds).
    n_bootstrap : int, default 1000
        Number of bootstrap resamples.
    confidence : float, default 0.95
        Desired confidence level.

    Returns
    -------
    lower : float
        Lower bound of the confidence interval.
    upper : float
        Upper bound of the confidence interval.
    """
    rng = np.random.default_rng(42)
    boot_samples = rng.choice(values, size=(n_bootstrap, len(values)), replace=True)
    stat = np.mean(boot_samples, axis=1)
    lower = np.percentile(stat, (1 - confidence) / 2 * 100)
    upper = np.percentile(stat, (1 + confidence) / 2 * 100)
    return float(lower), float(upper)


def write_variance_file(
    output_path: Path, rmse_values: List[float]
) -> None:
    """
    Write the variance (and 95 % CI) of the RMSE across seeds to CSV.

    The file contains three columns: ``metric``, ``variance`` and ``ci_lower``,
    ``ci_upper``.
    """
    variance = float(np.var(rmse_values, ddof=1))
    ci_lower, ci_upper = compute_bootstrap_ci(rmse_values)

    with output_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "variance", "ci_lower", "ci_upper"])
        writer.writerow(["rmse", f"{variance:.6f}", f"{ci_lower:.6f}", f"{ci_upper:.6f}"])


def train_one_seed(
    seed: int,
    X: np.ndarray,
    y: np.ndarray,
    ids: List[str],
    checkpoint_dir: Path,
) -> Tuple[float, float]:
    """
    Train a Random Forest on a single random seed.

    Returns
    -------
    mae_val : float
        Mean Absolute Error on the hold‑out test set.
    rmse_val : float
        Root Mean Squared Error on the hold‑out test set.
    """
    # Ensure reproducibility
    rng = np.random.default_rng(seed)

    # Use an 80/20 train‑test split (consistent across seeds)
    X_train, X_test, y_train, y_test, id_train, id_test = train_test_split(
        X, y, ids, test_size=0.2, random_state=seed
    )

    # Initialise the model
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)

    mae_val = mean_absolute_error(y_test, y_pred)
    rmse_val = mean_squared_error(y_test, y_pred, squared=False)

    # Save checkpoint
    checkpoint_path = checkpoint_dir / f"rf_seed_{seed}.pkl"
    save_rf_checkpoint(
        checkpoint_path,
        model=model,
        train_config={"seed": seed, "n_estimators": 200},
        seed=seed,
        timestamp=pd.Timestamp.utcnow().isoformat(),
    )

    return mae_val, rmse_val


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Random Forest baseline on QM9 10k subset."
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[0, 1, 2, 3, 4],
        help="List of random seeds to use for training (default: five seeds 0‑4).",
    )
    parser.add_argument(
        "--metrics-output",
        type=Path,
        default=Path("results/metrics.csv"),
        help="CSV file to which per‑seed metrics are appended.",
    )
    parser.add_argument(
        "--variance-output",
        type=Path,
        default=Path("results/rf_variance.csv"),
        help="CSV file that stores the RMSE variance and its confidence interval.",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path("data/checkpoints"),
        help="Directory where model checkpoints are saved.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Prepare output directories
    ensure_dir(args.metrics_output.parent)
    ensure_dir(args.variance_output.parent)
    ensure_dir(args.checkpoint_dir)

    # Verify data availability
    molecules_path, features_2d_path, _ = ensure_data_available()

    # Load data
    X, y, ids = load_data(molecules_path, features_2d_path)

    # Prepare metrics file
    write_metrics_header_if_needed(args.metrics_output)

    # Train for each seed
    rmse_across_seeds: List[float] = []
    for seed in args.seeds:
        mae_val, rmse_val = train_one_seed(seed, X, y, ids, args.checkpoint_dir)
        append_metrics_row(args.metrics_output, seed, mae_val, rmse_val)
        rmse_across_seeds.append(rmse_val)

    # Record variance / confidence interval
    write_variance_file(args.variance_output, rmse_across_seeds)


if __name__ == "__main__":
    main()
