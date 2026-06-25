"""
Random Forest training script for the dipole moment prediction project.

This script loads the processed QM9 data (molecule identifiers, SMILES strings,
2‑D features, and the dipole moment target), trains a RandomForestRegressor on
five different random seeds, evaluates each model with MAE and RMSE, saves the
trained model checkpoints and writes a CSV file summarising the metrics.

The implementation respects the project's existing API surface:
  * ``set_global_seed`` – deterministic seeding for ``random`` and ``numpy``.
  * ``ensure_data_available`` – sanity‑check that required parquet files exist.
  * ``load_data`` – loads data, merges features with the dipole target and returns
    ``X`` (features) and ``y`` (target).
  * ``train_one_seed`` – performs a train/validation split, fits a
    ``RandomForestRegressor``, evaluates, and persists the model.
  * ``parse_args`` – CLI handling (optional, defaults to five seeds and the
    standard checkpoint directory).
  * ``main`` – orchestrates the whole pipeline and writes the metrics CSV.

The script is deliberately self‑contained and only relies on the public
functions listed in the project's API surface.  All paths are relative to the
project root and follow the conventions established in earlier tasks.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Helper utilities (seed handling, data checks)
# ---------------------------------------------------------------------------

def set_global_seed(seed: int) -> None:
    """Set deterministic seeds for ``random`` and ``numpy``."""
    random.seed(seed)
    np.random.seed(seed)

def ensure_data_available() -> None:
    """Verify that all required processed data files exist."""
    required_files = [
        Path("data/processed/molecules_10k.parquet"),
        Path("data/processed/features_2d.parquet"),
    ]
    missing = [str(p) for p in required_files if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required processed data files: {missing}")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the processed QM9 subset and 2‑D feature matrix.

    Returns
    -------
    X : pd.DataFrame
        Feature matrix (2‑D descriptors).
    y : pd.Series
        Target dipole moment values.
    """
    # Load molecules – should contain at least ``molecule_id`` and ``dipole``.
    molecules_path = Path("data/processed/molecules_10k.parquet")
    molecules_df = pd.read_parquet(molecules_path)

    # Load 2‑D features – must contain ``molecule_id`` to allow a join.
    features_path = Path("data/processed/features_2d.parquet")
    features_df = pd.read_parquet(features_path)

    # Verify required columns.
    required_mol_cols = {"molecule_id", "dipole"}
    if not required_mol_cols.issubset(molecules_df.columns):
        raise ValueError(
            f"Processed data must contain a dipole column as target. "
            f"Found columns: {list(molecules_df.columns)}"
        )
    if "molecule_id" not in features_df.columns:
        raise ValueError(
            "2‑D feature file must contain a 'molecule_id' column for merging."
        )

    # Merge on ``molecule_id`` – keep only rows present in both tables.
    merged = pd.merge(
        features_df,
        molecules_df[["molecule_id", "dipole"]],
        on="molecule_id",
        how="inner",
    )
    # ``X`` are all columns except ``molecule_id`` and ``dipole``.
    X = merged.drop(columns=["molecule_id", "dipole"])
    y = merged["dipole"]
    return X, y

# ---------------------------------------------------------------------------
# Training for a single seed
# ---------------------------------------------------------------------------

def train_one_seed(
    seed: int,
    X: pd.DataFrame,
    y: pd.Series,
    checkpoint_dir: Path,
) -> Tuple[int, float, float]:
    """
    Train a RandomForestRegressor on a single random seed.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility (used for train/test split and the
        regressor's internal RNG).
    X : pd.DataFrame
        Feature matrix.
    y : pd.Series
        Target dipole moments.
    checkpoint_dir : Path
        Directory where the model ``.pkl`` will be stored.

    Returns
    -------
    seed : int
        The seed used (echoed for convenience).
    mae : float
        Mean Absolute Error on the held‑out test set.
    rmse : float
        Root Mean Squared Error on the held‑out test set.
    """
    # Split data (20 % test) using the same seed for reproducibility.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=seed,
    )

    # Initialise Random Forest – modest size to keep memory < 8 GB.
    rf = RandomForestRegressor(
        n_estimators=200,
        random_state=seed,
        n_jobs=1,  # Respect the 2‑CPU constraint enforced elsewhere.
    )
    rf.fit(X_train, y_train)

    # Predictions and metric computation.
    y_pred = rf.predict(X_test)
    mae_val = mean_absolute_error(y_test, y_pred)
    rmse_val = mean_squared_error(y_test, y_pred, squared=False)

    # Persist the model.
    checkpoint_path = checkpoint_dir / f"rf_seed_{seed}.pkl"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf, checkpoint_path)

    return seed, mae_val, rmse_val

# ---------------------------------------------------------------------------
# CLI handling
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Random Forest models on QM9 dipole data."
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=5,
        help="Number of random seeds / models to train (default: 5).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/checkpoints"),
        help="Directory to store model checkpoints and metrics CSV.",
    )
    return parser.parse_args(argv)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # -------------------------------------------------------------------
    # 1️⃣  Ensure data is present.
    # -------------------------------------------------------------------
    try:
        ensure_data_available()
    except FileNotFoundError as exc:
        sys.stderr.write(str(exc) + "\n")
        sys.exit(1)

    # -------------------------------------------------------------------
    # 2️⃣  Load features and target.
    # -------------------------------------------------------------------
    try:
        X, y = load_data()
    except Exception as exc:
        sys.stderr.write(f"Data loading failed: {exc}\\n")
        sys.exit(1)

    # -------------------------------------------------------------------
    # 3️⃣  Train models across the requested seeds.
    # -------------------------------------------------------------------
    metrics = []  # List of (seed, mae, rmse)
    for seed in range(args.seeds):
        set_global_seed(seed)
        seed_id, mae_val, rmse_val = train_one_seed(
            seed, X, y, checkpoint_dir=args.output_dir
        )
        metrics.append((seed_id, mae_val, rmse_val))
        print(
            f"[seed {seed_id}] MAE={mae_val:.4f}, RMSE={rmse_val:.4f}"
        )

    # -------------------------------------------------------------------
    # 4️⃣  Write a consolidated CSV for downstream analysis.
    # -------------------------------------------------------------------
    metrics_path = args.output_dir / "rf_metrics.csv"
    with metrics_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["model", "seed", "mae", "rmse"])
        for seed_id, mae_val, rmse_val in metrics:
            writer.writerow(["random_forest", seed_id, mae_val, rmse_val])

    print(f"Random Forest training complete. Metrics written to {metrics_path}")

if __name__ == "__main__":
    main()
