"""Random Forest baseline model for molecular dipole moment prediction.

This script trains a `RandomForestRegressor` on the processed feature set
(by default the 2‑D Morgan fingerprint / Coulomb matrix features) and
evaluates the model on a held‑out test split using the MAE and RMSE metrics
defined in ``training.evaluate``.  The trained model is saved as a pickle
file under ``data/checkpoints`` so that downstream pipelines (e.g. the
attribution or evaluation stages) can load it.

The implementation follows the functional requirements (FR‑005) and obeys
the project‑wide reproducibility and CPU‑constraint guidelines:
* deterministic train/test split via a user‑supplied ``--seed``
* ``n_jobs=1`` for the Random Forest to respect the 2‑CPU core limit
* explicit logging of metrics and model path
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Project‑wide metric utilities
from training.evaluate import mae, rmse


def load_data(features_path: str, target_column: str = "dipole_moment"):
    """Load a parquet file containing features and the target column.

    Parameters
    ----------
    features_path: str
        Path to a ``.parquet`` file produced by the data‑preprocessing steps.
    target_column: str, default ``"dipole_moment"``
        Column name that holds the dipole moment values.

    Returns
    -------
    X: pd.DataFrame
        Feature matrix (all columns except the target).
    y: pd.Series
        Target vector.
    """
    df = pd.read_parquet(features_path)
    if target_column not in df.columns:
        raise ValueError(
            f"Target column '{target_column}' not found in {features_path}"
        )
    X = df.drop(columns=[target_column])
    y = df[target_column]
    return X, y


def train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    seed: int,
    n_estimators: int = 200,
    max_depth: int | None = None,
) -> RandomForestRegressor:
    """Fit a RandomForestRegressor on the training data.

    Parameters
    ----------
    X_train, y_train: training data.
    seed: int
        Random state for reproducibility.
    n_estimators: int, default 200
        Number of trees in the forest.
    max_depth: int or None
        Maximum depth of each tree; ``None`` means unlimited.

    Returns
    -------
    model: RandomForestRegressor
        The fitted model.
    """
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=seed,
        n_jobs=1,  # respect the global 2‑CPU constraint
    )
    model.fit(X_train, y_train)
    return model


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train Random Forest baseline for dipole moment prediction"
    )
    parser.add_argument(
        "--features",
        type=str,
        default="data/processed/features_2d.parquet",
        help="Parquet file containing features and the target column",
    )
    parser.add_argument(
        "--target-column",
        type=str,
        default="dipole_moment",
        help="Name of the column that holds the dipole moment values",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducible train/test split and model",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of the dataset reserved for testing",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/checkpoints",
        help="Directory where the trained model will be saved",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    features_path = Path(args.features)
    if not features_path.is_file():
        raise FileNotFoundError(f"Features file not found: {features_path}")

    X, y = load_data(str(features_path), args.target_column)

    # ------------------------------------------------------------------
    # Train / test split (deterministic)
    # ------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.seed,
    )

    # ------------------------------------------------------------------
    # Model training
    # ------------------------------------------------------------------
    model = train_random_forest(X_train, y_train, seed=args.seed)

    # ------------------------------------------------------------------
    # Evaluation on the held‑out test set
    # ------------------------------------------------------------------
    y_pred = model.predict(X_test)
    test_mae = mae(y_test, y_pred)
    test_rmse = rmse(y_test, y_pred)

    print(f"Test MAE : {test_mae:.6f}")
    print(f"Test RMSE: {test_rmse:.6f}")

    # ------------------------------------------------------------------
    # Persist the model
    # ------------------------------------------------------------------
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"rf_seed_{args.seed}.pkl"
    joblib.dump(model, model_path)
    print(f"Random Forest model saved to {model_path}")


if __name__ == "__main__":
    main()
