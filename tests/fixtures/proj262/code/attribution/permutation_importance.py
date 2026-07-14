"""Permutation importance for a trained Random Forest model.

This module provides a utility to compute permutation feature importance
(as defined in scikit‑learn) for a RandomForestRegressor that has been
trained on the 2‑D descriptor dataset produced in the data preparation
stage.  The resulting importance scores are written to a JSON file that
downstream tests and analysis pipelines can consume.

The implementation is deliberately lightweight and has no external
configuration beyond the command‑line arguments.  It can also be used as
a library by importing :func:`compute_permutation_importance`.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, Any

import joblib
import pandas as pd
from sklearn.inspection import permutation_importance

__all__ = [
    "compute_permutation_importance",
    "main",
]


def compute_permutation_importance(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    n_repeats: int = 10,
    random_state: int | None = None,
) -> Dict[str, float]:
    """
    Compute permutation importance for a fitted model.

    Parameters
    ----------
    model:
        A fitted estimator that implements ``predict`` (e.g. a
        ``RandomForestRegressor``).
    X:
        Feature matrix (pandas DataFrame).  Columns are used as feature
        names in the output dictionary.
    y:
        Target vector (pandas Series or 1‑D array‑like).
    n_repeats:
        Number of times each feature is shuffled.  Defaults to 10.
    random_state:
        Random seed for reproducibility.

    Returns
    -------
    dict
        Mapping from feature name to mean importance (higher means more
        important).
    """
    # ``permutation_importance`` returns an object with ``importances_mean``
    # aligned with the column order of ``X``.
    result = permutation_importance(
        model,
        X,
        y,
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=-1,
    )
    importance_dict = dict(zip(X.columns, result.importances_mean.tolist()))
    return importance_dict


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute permutation importance for a Random Forest model."
    )
    parser.add_argument(
        "--model-path",
        type=pathlib.Path,
        required=True,
        help="Path to the pickled Random Forest model (e.g. data/checkpoints/rf_seed_0.pkl).",
    )
    parser.add_argument(
        "--features-path",
        type=pathlib.Path,
        required=True,
        help="Path to the Parquet file containing features and target (e.g. data/processed/features_2d.parquet).",
    )
    parser.add_argument(
        "--target-column",
        type=str,
        default="dipole_moment",
        help="Name of the target column in the features file.",
    )
    parser.add_argument(
        "--output-path",
        type=pathlib.Path,
        required=True,
        help="Path where the JSON attribution file will be written.",
    )
    parser.add_argument(
        "--n-repeats",
        type=int,
        default=10,
        help="Number of permutation repeats per feature.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=None,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the ``python -m code.attribution.permutation_importance`` CLI."""
    args = _parse_args()

    # Load the model.
    if not args.model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {args.model_path}")
    model = joblib.load(args.model_path)

    # Load the feature/target dataframe.
    if not args.features_path.is_file():
        raise FileNotFoundError(f"Features file not found: {args.features_path}")
    df = pd.read_parquet(args.features_path)

    if args.target_column not in df.columns:
        raise KeyError(f"Target column '{args.target_column}' not found in features file.")

    X = df.drop(columns=[args.target_column])
    y = df[args.target_column]

    # Compute importance.
    importances = compute_permutation_importance(
        model,
        X,
        y,
        n_repeats=args.n_repeats,
        random_state=args.random_state,
    )

    # Ensure the output directory exists.
    args.output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON.
    with args.output_path.open("w", encoding="utf-8") as f:
        json.dump(importances, f, indent=2, sort_keys=True)

    print(f"Permutation importance written to {args.output_path}")


if __name__ == "__main__":
    main()
