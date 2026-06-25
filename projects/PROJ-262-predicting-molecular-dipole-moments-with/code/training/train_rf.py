"""Random Forest training script for molecular dipole moment prediction.

This script loads the 2D feature set and the target dipole moments,
trains a ``RandomForestRegressor`` on five different random seeds,
saves each model checkpoint, and writes a consolidated metrics CSV
compatible with downstream analysis scripts.

Expected output files:
  - data/checkpoints/rf_seed_{seed}.pkl      (model checkpoint)
  - data/checkpoints/rf_metrics.csv          (metrics for all seeds)

The script is executable via:
    python code/training/train_rf.py
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Tuple

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def ensure_data_available(data_dir: Path) -> None:
    """Validate that required input files exist.

    Parameters
    ----------
    data_dir: Path
        Directory containing processed data files.
    """
    required_files = [
        data_dir / "features_2d.parquet",
        data_dir / "molecules_10k.parquet",
    ]
    missing = [str(p) for p in required_files if not p.is_file()]
    if missing:
        raise FileNotFoundError(
            f"Required data files missing in {data_dir}: {', '.join(missing)}"
        )


def _find_dipole_column(df: pd.DataFrame) -> str:
    """Return the column name that stores the dipole moment.

    The QM9 dataset uses several possible names; this function makes the
    script robust to minor naming differences.

    Parameters
    ----------
    df: pd.DataFrame
        Dataframe that should contain the target column.

    Returns
    -------
    str
        Column name that will be used as the target.
    """
    candidates = {"dipole", "dipole_moment", "mu", "dipole_mom", "dipole_moment_a.u."}
    for col in df.columns:
        if col.lower() in candidates:
            return col
    raise KeyError(
        f"Target column for dipole moment not found. Expected one of {candidates}, "
        f"found columns: {list(df.columns)}"
    )


def load_data(data_dir: Path) -> pd.DataFrame:
    """Load features and target dipole moments, returning a unified DataFrame.

    The returned DataFrame contains all feature columns plus a ``dipole``
    column that holds the target value.

    Parameters
    ----------
    data_dir: Path
        Directory containing ``features_2d.parquet`` and ``molecules_10k.parquet``.

    Returns
    -------
    pd.DataFrame
        Combined dataset ready for model training.
    """
    features_path = data_dir / "features_2d.parquet"
    molecules_path = data_dir / "molecules_10k.parquet"

    df_features = pd.read_parquet(features_path)
    df_molecules = pd.read_parquet(molecules_path)

    dipole_col = _find_dipole_column(df_molecules)
    # Standardise column name to ``dipole`` for downstream code.
    df = df_features.copy()
    df["dipole"] = df_molecules[dipole_col]
    return df


def train_one_seed(
    df: pd.DataFrame, seed: int, output_dir: Path
) -> Tuple[int, float, float]:
    """Train a Random Forest on a single seed and persist the model.

    Parameters
    ----------
    df: pd.DataFrame
        Dataset containing features and a ``dipole`` target column.
    seed: int
        Random seed for reproducibility.
    output_dir: Path
        Directory where the model checkpoint will be saved.

    Returns
    -------
    Tuple[int, float, float]
        ``(seed, mae, rmse)`` for the test split.
    """
    X = df.drop(columns=["dipole"])
    y = df["dipole"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )

    # Instantiate the regressor. Hyper‑parameters are modest to keep runtime low.
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        random_state=seed,
        n_jobs=1,  # respect the global CPU‑core constraint (2 cores max)
    )
    rf.fit(X_train, y_train)

    # Save the trained model.
    model_path = output_dir / f"rf_seed_{seed}.pkl"
    joblib.dump(rf, model_path)

    # Evaluate on the held‑out test set.
    y_pred = rf.predict(X_test)
    mae_val = mean_absolute_error(y_test, y_pred)
    rmse_val = mean_squared_error(y_test, y_pred, squared=False)

    return seed, mae_val, rmse_val


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Random Forest models on QM9 dipole data."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory containing processed feature and target files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/checkpoints"),
        help="Directory where model checkpoints and metrics CSV will be written.",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[0, 1, 2, 3, 4],
        help="Random seeds for which to train separate models.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)

    # Ensure output directory exists.
    args.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        ensure_data_available(args.data_dir)
    except FileNotFoundError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1

    try:
        df = load_data(args.data_dir)
    except KeyError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1

    # Collect metrics for each seed.
    metrics: List[Tuple[int, float, float]] = []
    for seed in args.seeds:
        seed, mae_val, rmse_val = train_one_seed(df, seed, args.output_dir)
        metrics.append((seed, mae_val, rmse_val))
        print(f"Seed {seed}: MAE={mae_val:.4f}, RMSE={rmse_val:.4f}")

    # Write consolidated metrics CSV with column names expected by downstream analysis.
    metrics_path = args.output_dir / "rf_metrics.csv"
    with metrics_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["model", "seed", "mae", "rmse"])
        for seed, mae_val, rmse_val in metrics:
            writer.writerow(["RandomForest", seed, f"{mae_val:.6f}", f"{rmse_val:.6f}"])

    print(f"Metrics written to {metrics_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
