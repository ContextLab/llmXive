"""
Random Forest training script for predicting molecular dipole moments.

This script trains a scikit-learn RandomForestRegressor on the 2‑D feature
matrix generated in the US1 pipeline.  Five random seeds are used to
produce five independent models and corresponding performance metrics.
The models are saved as ``rf_seed_{seed}.pkl`` in the ``data/checkpoints``
directory and a CSV file summarising the MAE and RMSE for each seed is
written to the same directory.

The implementation mirrors the style of ``train_gnn.py`` – it re‑uses the
``set_global_seed`` utility from that module to guarantee reproducibility
and the ``mae``/``rmse`` helpers from ``training.evaluate`` for metric
computation.
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import List

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Re‑use utilities from the GNN training module
from training.train_gnn import set_global_seed
from training.evaluate import mae, rmse


def load_data(data_dir: Path) -> pd.DataFrame:
    """
    Load the 2‑D feature parquet file produced by the US1 pipeline.

    Parameters
    ----------
    data_dir: Path
        Directory containing ``features_2d.parquet``.

    Returns
    ----------
    pd.DataFrame
        Dataframe with feature columns and a ``dipole`` target column.
    """
    feature_path = data_dir / "features_2d.parquet"
    if not feature_path.is_file():
        raise FileNotFoundError(f"Feature file not found: {feature_path}")
    df = pd.read_parquet(feature_path)
    if "dipole" not in df.columns:
        raise KeyError(
            "Target column 'dipole' not found in the feature parquet file."
        )
    return df


def train_one_seed(
    seed: int,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[float, float, RandomForestRegressor]:
    """
    Train a RandomForestRegressor for a single seed and evaluate it.

    Returns
    -------
    tuple
        (mae_score, rmse_score, fitted_model)
    """
    set_global_seed(seed)

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=seed,
        n_jobs=-1,  # honour the global CPU‑core constraint elsewhere
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae_score = mae(y_test, preds)
    rmse_score = rmse(y_test, preds)

    return mae_score, rmse_score, model


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train Random Forest models on 2‑D molecular descriptors."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory containing the pre‑processed feature parquet file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/checkpoints"),
        help="Directory where model checkpoints and metrics CSV will be saved.",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[0, 1, 2, 3, 4],
        help="Random seeds for reproducible training runs.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion of the dataset to hold out for testing.",
    )
    args = parser.parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    df = load_data(args.data_dir)

    # Separate features and target
    y = df["dipole"]
    X = df.drop(columns=["dipole"])

    # Prepare CSV writer for metrics
    metrics_path = args.output_dir / "rf_metrics.csv"
    with metrics_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["seed", "mae", "rmse"])

        for seed in args.seeds:
            # Split data – using the same seed for reproducibility
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=args.test_size, random_state=seed
            )

            mae_score, rmse_score, model = train_one_seed(
                seed, X_train, y_train, X_test, y_test
            )

            # Save model checkpoint
            model_path = args.output_dir / f"rf_seed_{seed}.pkl"
            joblib.dump(model, model_path)

            # Record metrics
            writer.writerow([seed, mae_score, rmse_score])
            print(
                f"Seed {seed}: MAE={mae_score:.4f}, RMSE={rmse_score:.4f} – saved to {model_path}"
            )

    print(f"All metrics written to {metrics_path}")


if __name__ == "__main__":
    main()
