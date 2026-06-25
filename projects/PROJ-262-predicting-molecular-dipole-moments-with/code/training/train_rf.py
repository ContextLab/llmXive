"""
Random Forest training script for the dipole moment prediction project.

This script trains a RandomForestRegressor on the processed QM9 subset
using the 2D descriptors. It runs for a configurable number of random
seeds (default 5) and writes:

* model checkpoints: data/checkpoints/rf_seed_{seed}.pkl
* per‑seed metrics CSV: data/checkpoints/rf_metrics.csv
* aggregated metrics CSV (used by downstream analysis): results/metrics.csv
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path
from typing import List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def set_global_seed(seed: int) -> None:
    """Set random seeds for reproducibility across libraries."""
    random.seed(seed)
    np.random.seed(seed)
    # torch is not required for Random Forest, but we set it if available
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def ensure_data_available() -> None:
    """
    Verify that the processed data files exist.

    The function raises a RuntimeError if required files are missing.
    """
    required_files = [
        Path("data/processed/molecules_10k.parquet"),
        Path("data/processed/features_2d.parquet"),
    ]
    missing = [str(p) for p in required_files if not p.is_file()]
    if missing:
        raise RuntimeError(f"Missing required processed data files: {missing}")


def load_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the processed molecule table and the 2‑D feature table,
    return feature matrix X and target vector y.

    The target column in the molecule table should be named ``dipole``.
    If a different name is present (e.g. ``dipole_moment``), it is
    renamed to ``dipole`` for downstream compatibility.
    """
    molecules_path = Path("data/processed/molecules_10k.parquet")
    features_path = Path("data/processed/features_2d.parquet")

    # Load dataframes
    mol_df = pd.read_parquet(molecules_path)
    feat_df = pd.read_parquet(features_path)

    # ------------------------------------------------------------------
    # Resolve target column name
    # ------------------------------------------------------------------
    target_candidates = ["dipole", "dipole_moment", "dipole (Debye)", "mu"]
    target_col = None
    for cand in target_candidates:
        if cand in mol_df.columns:
            target_col = cand
            break
    if target_col is None:
        raise RuntimeError(
            "Processed data must contain a dipole column as target. "
            f"Found columns: {list(mol_df.columns)}"
        )
    if target_col != "dipole":
        mol_df = mol_df.rename(columns={target_col: "dipole"})
        target_col = "dipole"

    # Assume both tables have a common identifier column named ``molecule_id``.
    # If not present, fall back to using the index.
    if "molecule_id" in mol_df.columns and "molecule_id" in feat_df.columns:
        X = (
            feat_df.set_index("molecule_id")
            .join(mol_df.set_index("molecule_id")["dipole"], how="inner")
            .drop(columns=["dipole"])
        )
        y = mol_df.set_index("molecule_id")["dipole"]
    else:
        # Use positional alignment – both dataframes should be ordered identically.
        X = feat_df.drop(columns=["dipole"], errors="ignore")
        y = mol_df["dipole"]
    # Ensure X is a DataFrame and y is a Series
    X = pd.DataFrame(X)
    y = pd.Series(y)

    return X, y


def train_one_seed(seed: int, X: pd.DataFrame, y: pd.Series) -> Tuple[RandomForestRegressor, float, float]:
    """
    Train a RandomForestRegressor on the supplied data using a specific seed.

    Returns the trained model together with MAE and RMSE on the training set.
    (The project currently does not split into train/validation sets for the
    RF baseline – this mirrors the original implementation intent.)
    """
    set_global_seed(seed)

    # Initialise model – a modest number of trees keeps memory usage low.
    model = RandomForestRegressor(
        n_estimators=200,
        random_state=seed,
        n_jobs=1,  # respect the global 2‑CPU constraint
    )
    model.fit(X, y)

    # Compute metrics on the same data (training metrics)
    preds = model.predict(X)
    mae_val = mean_absolute_error(y, preds)
    rmse_val = mean_squared_error(y, preds, squared=False)

    return model, mae_val, rmse_val


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Random Forest baseline on QM9 2D descriptors."
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=list(range(5)),
        help="Random seeds to use for independent training runs (default: 0‑4).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/checkpoints",
        help="Directory where model checkpoints and per‑seed metrics are stored.",
    )
    parser.add_argument(
        "--metrics-output",
        type=str,
        default="results/metrics.csv",
        help="Path for the aggregated metrics CSV consumed by analysis scripts.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)

    # ------------------------------------------------------------------
    # Prepare output directories
    # ------------------------------------------------------------------
    checkpoints_dir = Path(args.output_dir)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    Path("results").mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    try:
        X, y = load_data()
    except RuntimeError as exc:
        print(f"[ERROR] Failed to prepare data: {exc}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # Train for each seed and collect metrics
    # ------------------------------------------------------------------
    metric_rows: List[dict] = []
    for seed in args.seeds:
        print(f"Training Random Forest seed {seed} ...")
        model, mae_val, rmse_val = train_one_seed(seed, X, y)

        # Save model checkpoint
        model_path = checkpoints_dir / f"rf_seed_{seed}.pkl"
        joblib.dump(model, model_path)

        # Record metrics
        metric_rows.append(
            {
                "model": "RandomForest",
                "seed": seed,
                "mae": mae_val,
                "rmse": rmse_val,
            }
        )

    # ------------------------------------------------------------------
    # Write per‑seed metrics CSV (used by other parts of the pipeline)
    # ------------------------------------------------------------------
    rf_metrics_path = checkpoints_dir / "rf_metrics.csv"
    pd.DataFrame(metric_rows).to_csv(rf_metrics_path, index=False)

    # ------------------------------------------------------------------
    # Write aggregated metrics CSV with the column names expected by the
    # analysis scripts (model, seed, mae, rmse)
    # ------------------------------------------------------------------
    aggregated_path = Path(args.metrics_output)
    pd.DataFrame(metric_rows).to_csv(aggregated_path, index=False)

    print(f"Training complete. Models saved to {checkpoints_dir}")
    print(f"Metrics written to {rf_metrics_path} and {aggregated_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
