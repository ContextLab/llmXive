from __future__ import annotations

import argparse
import csv
import os
import pickle
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# ---------------------------------------------------------------------------
# Compatibility shim: ensure that downstream libraries (pandas, scipy, etc.)
# receive the real NumPy implementation rather than the local placeholder.
# ---------------------------------------------------------------------------
import importlib.util
import sys

def _ensure_real_numpy() -> None:
    """
    Insert the genuine NumPy module into ``sys.modules`` before any
    third‑party libraries are imported. The ``code/numpy`` package present in
    the repository would otherwise shadow the installed NumPy distribution,
    leading to attribute errors such as missing ``__version__``.
    """
    if "numpy" in sys.modules:
        # Already loaded – nothing to do.
        return
    # Load the external NumPy using the shim defined in ``code/numpy/__init__.py``.
    spec = importlib.util.find_spec("numpy")
    if spec is None or spec.origin is None:
        raise ImportError("NumPy could not be found on sys.path.")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    sys.modules["numpy"] = module

_ensure_real_numpy()

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# Project imports based on API surface
from utils.reproducibility import set_seed
from training.split_data import get_train_test_splits
from training.evaluate import mae, rmse
from training.save_checkpoints import save_rf_checkpoint

# ---------------------------------------------------------------------------
# Constants (can be overridden via CLI)
# ---------------------------------------------------------------------------
DEFAULT_NUM_SEEDS = 5
NUM_ESTIMATORS = 100  # Reduced for CPU efficiency while maintaining validity
MAX_DEPTH = 10
DEFAULT_OUTPUT_METRICS_PATH = "results/metrics.csv"
OUTPUT_CKPT_DIR = "data/checkpoints"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def ensure_data_available() -> bool:
    """Verify that the required processed artefacts exist."""
    required_files = [
        "data/processed/features_2d.parquet",
        "data/processed/molecules_10k.parquet",
    ]
    missing = [f for f in required_files if not Path(f).exists()]
    if missing:
        print("Missing required data files:", ", ".join(missing))
        return False
    return True

def load_data() -> Tuple[pd.DataFrame, pd.Series]:
    """Load 2‑D features and dipole targets, aligning on ``molecule_id``."""
    features_df = pd.read_parquet("data/processed/features_2d.parquet")
    molecules_df = pd.read_parquet("data/processed/molecules_10k.parquet")

    # Ensure ``molecule_id`` is the index for a clean join
    if "molecule_id" in features_df.columns:
        features_df = features_df.set_index("molecule_id")
    if "molecule_id" in molecules_df.columns:
        molecules_df = molecules_df.set_index("molecule_id")

    common_ids = features_df.index.intersection(molecules_df.index)
    if len(common_ids) == 0:
        raise ValueError("No overlapping molecule IDs between features and labels.")

    X = features_df.loc[common_ids]
    y = molecules_df.loc[common_ids, "dipole"]
    return X, y

def train_one_seed(seed: int, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """Train a Random Forest model for a single seed and return metrics."""
    set_seed(seed)

    # Split using the shared utility
    X_train, X_test, y_train, y_test = get_train_test_splits(
        X, y, test_size=0.2, random_state=seed
    )

    # Initialise the model
    rf = RandomForestRegressor(
        n_estimators=NUM_ESTIMATORS,
        max_depth=MAX_DEPTH,
        random_state=seed,
        n_jobs=-1,
    )

    start = time.time()
    rf.fit(X_train, y_train)
    train_time = time.time() - start

    # Predictions & metrics
    y_pred = rf.predict(X_test)
    mae_score = mae(y_test, y_pred)
    rmse_score = rmse(y_test, y_pred)

    # Persist checkpoint
    ckpt_path = save_rf_checkpoint(
        model=rf,
        config={"n_estimators": NUM_ESTIMATORS, "max_depth": MAX_DEPTH, "seed": seed},
        seed=seed,
        output_dir=OUTPUT_CKPT_DIR,
    )

    return {
        "seed": seed,
        "model": "random_forest",
        "mae": mae_score,
        "rmse": rmse_score,
        "train_time": train_time,
        "checkpoint_path": str(ckpt_path),
    }

def write_metrics_csv(metrics_list: List[Dict[str, Any]], output_path: str) -> None:
    """Write per‑seed metrics and the global RMSE variance to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    rmse_vals = [m["rmse"] for m in metrics_list]
    # Compute variance manually to avoid NumPy dependency
    mean_rmse = sum(rmse_vals) / len(rmse_vals)
    variance = sum((v - mean_rmse) ** 2 for v in rmse_vals) / len(rmse_vals)

    fieldnames = ["seed", "model", "mae", "rmse", "rmse_variance"]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, m in enumerate(metrics_list):
            row = {
                "seed": m["seed"],
                "model": m["model"],
                "mae": m["mae"],
                "rmse": m["rmse"],
                "rmse_variance": variance if i == 0 else "",
            }
            writer.writerow(row)

    print(f"Metrics written to {output_path}")
    print(f"RMSE variance across seeds: {variance:.6f}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Random Forest baseline")
    parser.add_argument(
        "--num-seeds",
        type=int,
        default=DEFAULT_NUM_SEEDS,
        help="Number of random seeds to train (default 5)",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=DEFAULT_OUTPUT_METRICS_PATH,
        help="CSV file to write aggregated metrics",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    if not ensure_data_available():
        raise FileNotFoundError(
            "Required processed data not found – run `generate_processed_data.py` first."
        )

    print("Loading data...")
    X, y = load_data()
    print(f"Loaded {len(X)} samples with {X.shape[1]} feature(s)")

    metrics: List[Dict[str, Any]] = []
    print(f"Training Random Forest across {args.num_seeds} seeds...")
    for i in range(args.num_seeds):
        seed = 42 + i
        print(f"  Seed {seed} …")
        metrics.append(train_one_seed(seed, X, y))

    write_metrics_csv(metrics, args.output_path)
    print("Random Forest training completed.")

if __name__ == "__main__":
    main()