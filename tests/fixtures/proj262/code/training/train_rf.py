#!/usr/bin/env python3
"""
Random Forest training for molecular dipole moment prediction.

Trains a Random Forest baseline model on 2D molecular descriptors with
reproducibility via multiple random seeds.

Output:
    - data/checkpoints/rf_seed_{N}.pkl (model checkpoints)
    - results/metrics.csv (performance metrics across seeds)
"""

from __future__ import annotations

import argparse
import csv
import os
import pickle
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Import from training module for reproducibility (consistent with train_gnn.py)
from training.train_gnn import set_global_seed


def ensure_data_available() -> bool:
    """Verify that required input data files exist."""
    required_files = [
        "data/processed/features_2d.parquet",
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"ERROR: Required file not found: {file_path}")
            return False
    
    return True


def load_data() -> Tuple[np.ndarray, np.ndarray]:
    """Load 2D molecular features and dipole moment targets."""
    features_df = pd.read_parquet("data/processed/features_2d.parquet")
    
    # Features are all columns except dipole_moment
    feature_cols = [col for col in features_df.columns if col != "dipole_moment"]
    X = features_df[feature_cols].values
    y = features_df["dipole_moment"].values
    
    return X, y


def train_one_seed(
    X: np.ndarray,
    y: np.ndarray,
    seed: int,
    test_size: float = 0.2,
    n_estimators: int = 100,
    max_depth: int = 10,
) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """
    Train a Random Forest model with a specific random seed.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,) - dipole moments
        seed: Random seed for reproducibility
        test_size: Fraction of data for test set
        n_estimators: Number of trees in the forest
        max_depth: Maximum depth of each tree
        
    Returns:
        Tuple of (trained model, metrics dict with 'mae' and 'rmse')
    """
    # Set seed for reproducibility
    set_global_seed(seed)
    
    # Split data with stratified sampling if possible
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed
    )
    
    # Train Random Forest
    rf_model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=seed,
        n_jobs=-1,
        verbose=0,
    )
    rf_model.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = rf_model.predict(X_test)
    
    # Compute metrics
    mae = np.mean(np.abs(y_test - y_pred))
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
    
    metrics = {
        "mae": float(mae),
        "rmse": float(rmse),
    }
    
    return rf_model, metrics


def write_metrics_csv(metrics_list: List[Dict[str, float]], output_path: str) -> None:
    """Write metrics to CSV file with standard column names."""
    # Ensure results directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write with standard column names expected by analysis scripts
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["seed", "model", "mae", "rmse"])
        writer.writeheader()
        for metrics in metrics_list:
            writer.writerow({
                "seed": metrics["seed"],
                "model": "random_forest",
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
            })


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train Random Forest model for dipole moment prediction"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[42, 123, 456, 789, 1011],
        help="Random seeds to use (default: 5 seeds for reproducibility)",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="Number of trees in Random Forest (default: 100)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum depth of trees (default: 10)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test set fraction (default: 0.2)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/checkpoints",
        help="Directory for model checkpoints (default: data/checkpoints)",
    )
    parser.add_argument(
        "--metrics-file",
        type=str,
        default="results/metrics.csv",
        help="Output path for metrics CSV (default: results/metrics.csv)",
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for Random Forest training."""
    args = parse_args()
    
    print("=" * 60)
    print("Random Forest Training for Molecular Dipole Moments")
    print("=" * 60)
    
    # Check data availability
    if not ensure_data_available():
        print("ERROR: Required data files not found. Exiting.")
        sys.exit(1)
    
    # Load data
    print("Loading 2D molecular features...")
    X, y = load_data()
    print(f"  Loaded {len(X)} samples with {X.shape[1]} features")
    
    # Train for each seed
    all_metrics = []
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for seed in args.seeds:
        print(f"\nTraining seed {seed}...")
        
        # Train model
        rf_model, metrics = train_one_seed(
            X, y, seed,
            test_size=args.test_size,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
        )
        
        # Save checkpoint
        checkpoint_path = output_dir / f"rf_seed_{seed}.pkl"
        with open(checkpoint_path, "wb") as f:
            pickle.dump(rf_model, f)
        print(f"  Saved checkpoint to {checkpoint_path}")
        
        # Store metrics
        metrics["seed"] = seed
        all_metrics.append(metrics)
        
        print(f"  Test MAE: {metrics['mae']:.4f}")
        print(f"  Test RMSE: {metrics['rmse']:.4f}")
    
    # Write metrics CSV to results/ directory (expected by analysis scripts)
    write_metrics_csv(all_metrics, args.metrics_file)
    print(f"\nMetrics written to {args.metrics_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Completed training for {len(args.seeds)} seeds")
    print(f"Checkpoints saved to: {output_dir}/")
    print(f"Metrics saved to: {args.metrics_file}")
    print("=" * 60)