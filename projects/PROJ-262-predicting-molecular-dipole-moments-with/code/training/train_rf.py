from __future__ import annotations

import argparse
import csv
import os
import pickle
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

# Project imports based on API surface
from utils.reproducibility import set_seed
from training.split_data import get_train_test_splits
from training.evaluate import mae, rmse
from training.save_checkpoints import save_rf_checkpoint

# Constants
NUM_SEEDS = 5
NUM_ESTIMATORS = 100  # Reduced for CPU efficiency while maintaining validity
MAX_DEPTH = 10
OUTPUT_METRICS_PATH = "results/metrics.csv"
OUTPUT_CKPT_DIR = "data/checkpoints"

def ensure_data_available() -> bool:
    """Check if required processed data files exist."""
    required_files = [
        "data/processed/features_2d.parquet",
        "data/processed/molecules_10k.parquet"
    ]
    for f in required_files:
        if not Path(f).exists():
            print(f"Error: Required file {f} not found.")
            return False
    return True

def load_data() -> Tuple[pd.DataFrame, pd.Series]:
    """Load feature data and labels."""
    # Load features
    features_df = pd.read_parquet("data/processed/features_2d.parquet")
    
    # Load molecules to get dipole moments
    molecules_df = pd.read_parquet("data/processed/molecules_10k.parquet")
    
    # Ensure alignment
    if "molecule_id" in features_df.columns:
        features_df = features_df.set_index("molecule_id")
    if "molecule_id" in molecules_df.columns:
        molecules_df = molecules_df.set_index("molecule_id")
        
    # Align indices
    common_ids = features_df.index.intersection(molecules_df.index)
    if len(common_ids) == 0:
        raise ValueError("No common molecule IDs found between features and molecules.")
    
    X = features_df.loc[common_ids]
    y = molecules_df.loc[common_ids, "dipole"]
    
    return X, y

def train_one_seed(seed: int, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """Train a single Random Forest model with a specific seed."""
    set_seed(seed)
    
    # Split data using the project's split utility
    X_train, X_test, y_train, y_test = get_train_test_splits(X, y, test_size=0.2, random_state=seed)
    
    # Initialize model
    rf = RandomForestRegressor(
        n_estimators=NUM_ESTIMATORS,
        max_depth=MAX_DEPTH,
        random_state=seed,
        n_jobs=-1
    )
    
    # Train
    start_time = time.time()
    rf.fit(X_train, y_train)
    train_time = time.time() - start_time
    
    # Evaluate
    y_pred = rf.predict(X_test)
    mae_score = mae(y_test, y_pred)
    rmse_score = rmse(y_test, y_pred)
    
    # Save checkpoint
    ckpt_path = save_rf_checkpoint(
        model=rf,
        config={
            "n_estimators": NUM_ESTIMATORS,
            "max_depth": MAX_DEPTH,
            "seed": seed
        },
        seed=seed,
        output_dir=OUTPUT_CKPT_DIR
    )
    
    return {
        "seed": seed,
        "model": "random_forest",
        "mae": mae_score,
        "rmse": rmse_score,
        "train_time": train_time,
        "checkpoint_path": str(ckpt_path)
    }

def write_metrics_csv(metrics_list: List[Dict[str, Any]], output_path: str):
    """Write metrics to CSV file, calculating and recording RMSE variance."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Calculate variance of RMSE across seeds
    rmse_values = [m["rmse"] for m in metrics_list]
    rmse_variance = float(np.var(rmse_values))
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["seed", "model", "mae", "rmse", "rmse_variance"])
        writer.writeheader()
        for i, metrics in enumerate(metrics_list):
            row = {
                "seed": metrics["seed"],
                "model": metrics["model"],
                "mae": metrics["mae"],
                "rmse": metrics["rmse"]
            }
            # Add variance to the first row (representing the global stat for this run)
            if i == 0:
                row["rmse_variance"] = rmse_variance
            writer.writerow(row)
    
    print(f"Metrics written to {output_path}")
    print(f"RMSE Variance across {NUM_SEEDS} seeds: {rmse_variance:.6f}")

def save_checkpoints(metrics_list: List[Dict[str, Any]]):
    """Ensure all checkpoints are saved (wrapper for explicit task requirement)."""
    # Handled in train_one_seed, but kept for explicit API contract
    pass

def parse_args():
    parser = argparse.ArgumentParser(description="Train Random Forest baseline")
    parser.add_argument("--num-seeds", type=int, default=NUM_SEEDS, help="Number of random seeds")
    parser.add_argument("--output-path", type=str, default=OUTPUT_METRICS_PATH, help="Output metrics CSV path")
    return parser.parse_args()

def main():
    args = parse_args()
    
    if not ensure_data_available():
        raise FileNotFoundError("Required data files not found. Run data preprocessing first.")
    
    print("Loading data...")
    X, y = load_data()
    print(f"Loaded {len(X)} samples with {X.shape[1]} features")
    
    metrics_list = []
    print(f"Training Random Forest with {args.num_seeds} seeds...")
    
    # Loop over seeds to train and record metrics
    for i in range(args.num_seeds):
        seed = 42 + i  # Deterministic seed sequence
        print(f"  Training seed {seed}...")
        metrics = train_one_seed(seed, X, y)
        metrics_list.append(metrics)
        print(f"    Seed {seed}: MAE={metrics['mae']:.4f}, RMSE={metrics['rmse']:.4f}")
    
    # Write metrics including the calculated RMSE variance
    write_metrics_csv(metrics_list, args.output_path)
    print("Random Forest training complete.")

if __name__ == "__main__":
    main()