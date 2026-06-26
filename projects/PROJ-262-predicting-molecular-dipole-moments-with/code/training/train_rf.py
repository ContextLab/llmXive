from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Import from sibling modules per API surface
from training.evaluate import mae, rmse
from utils.reproducibility import set_seed


def set_global_seed(seed: int) -> None:
    """Set global random seed for reproducibility."""
    set_seed(seed)


def ensure_data_available() -> bool:
    """Verify required input data files exist."""
    features_2d_path = Path("data/processed/features_2d.parquet")
    molecules_path = Path("data/processed/molecules_10k.parquet")

    if not features_2d_path.exists():
        print(f"ERROR: Missing {features_2d_path}", file=sys.stderr)
        return False
    if not molecules_path.exists():
        print(f"ERROR: Missing {molecules_path}", file=sys.stderr)
        return False

    return True


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load 2D features and molecule metadata.
    Returns features DataFrame and targets (dipole moments) from molecules file.
    """
    features_df = pd.read_parquet("data/processed/features_2d.parquet")
    molecules_df = pd.read_parquet("data/processed/molecules_10k.parquet")

    # Extract target variable (dipole moment magnitude) from molecules
    # The molecules file contains 'dipole_moment' column
    if 'dipole_moment' not in molecules_df.columns:
        raise ValueError(
            f"molecules_10k.parquet missing 'dipole_moment' column. "
            f"Available columns: {list(molecules_df.columns)}"
        )

    # Ensure feature columns are numeric
    feature_cols = [col for col in features_df.columns if col != 'molecule_id']
    X = features_df[feature_cols].values

    # Align targets with features using molecule_id
    # Merge on molecule_id to ensure proper alignment
    merged = molecules_df.merge(
        features_df[['molecule_id']],
        on='molecule_id',
        how='inner'
    )
    y = merged['dipole_moment'].values

    return X, y


def train_one_seed(seed: int, test_size: float = 0.2) -> Dict:
    """
    Train Random Forest model with given seed.

    Args:
        seed: Random seed for reproducibility
        test_size: Fraction of data to hold out for testing

    Returns:
        Dictionary with model, metrics, and seed info
    """
    set_global_seed(seed)

    # Load data
    X, y = load_data()

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=seed,
        stratify=None  # Regression, no stratification needed
    )

    # Train Random Forest
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=seed,
        n_jobs=2  # Respect CPU constraint FR-010
    )
    rf_model.fit(X_train, y_train)

    # Evaluate
    y_pred = rf_model.predict(X_test)
    mae_score = mae(y_test, y_pred)
    rmse_score = rmse(y_test, y_pred)

    # Save checkpoint
    checkpoint_path = Path(f"data/checkpoints/rf_seed_{seed}.pkl")
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf_model, checkpoint_path)

    return {
        'model': 'random_forest',
        'seed': seed,
        'mae': mae_score,
        'rmse': rmse_score,
        'n_train': len(X_train),
        'n_test': len(X_test)
    }


def write_metrics_csv(metrics_list: List[Dict], output_path: Path) -> None:
    """
    Write metrics to CSV with correct column names for downstream consumers.

    Downstream scripts (generate_performance_plots.py, generate_significance.py)
    expect columns: model, seed, mae, rmse
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['model', 'seed', 'mae', 'rmse'],
            extrasaction='ignore'
        )
        writer.writeheader()
        for metrics in metrics_list:
            writer.writerow(metrics)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train Random Forest baseline on molecular dipole moment data"
    )
    parser.add_argument(
        '--seeds',
        type=int,
        nargs='+',
        default=[42, 123, 456, 789, 1011],
        help="Random seeds to use (default: 5 seeds)"
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path("results/metrics.csv"),
        help="Output path for metrics CSV"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for Random Forest training pipeline."""
    args = parse_args()

    # Verify data availability
    if not ensure_data_available():
        print("Data availability check failed. Exiting.", file=sys.stderr)
        sys.exit(1)

    print(f"Training Random Forest with seeds: {args.seeds}")

    metrics_list = []
    for seed in args.seeds:
        print(f"  Training seed {seed}...")
        try:
            metrics = train_one_seed(seed)
            metrics_list.append(metrics)
            print(f"    MAE: {metrics['mae']:.4f}, RMSE: {metrics['rmse']:.4f}")
        except Exception as e:
            print(f"    FAILED: {e}", file=sys.stderr)
            raise

    # Write metrics CSV with correct column names
    write_metrics_csv(metrics_list, args.output)
    print(f"Metrics written to {args.output}")

    # Also save individual seed metrics for checkpoint tracking
    rf_metrics_path = Path("data/checkpoints/rf_metrics.csv")
    write_metrics_csv(metrics_list, rf_metrics_path)
    print(f"Seed metrics written to {rf_metrics_path}")


if __name__ == "__main__":
    main()