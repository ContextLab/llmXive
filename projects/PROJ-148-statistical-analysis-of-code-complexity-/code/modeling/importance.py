"""
Feature importance extraction and persistence utilities.

This module provides functionality to extract feature importance from the
primary L1‑regularized logistic regression model and the alternative Random
Forest model, and to store these importance vectors alongside feature names
for downstream analysis.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd


def get_importance(
    primary_model,
    alternative_model,
    feature_names: List[str],
) -> Dict[str, np.ndarray]:
    """
    Extract feature importance from both models.

    Parameters
    ----------
    primary_model: LogisticRegression
        Trained L1 logistic regression model.
    alternative_model: RandomForestClassifier
        Trained random forest model.
    feature_names: list[str]
        List of feature column names.

    Returns
    -------
    dict
        Mapping with keys ``primary_coeff`` and ``rf_importance``.
    """
    # Coefficients from logistic regression (already sparse because of L1)
    primary_coeff = np.asarray(primary_model.coef_).ravel()
    # Feature importances from random forest
    rf_importance = np.asarray(alternative_model.feature_importances_)
    return {
        "primary_coeff": primary_coeff,
        "rf_importance": rf_importance,
    }


def save_importance(
    importance: Dict[str, np.ndarray],
    feature_names: List[str],
    output_path: pathlib.Path,
) -> None:
    """
    Persist the importance vectors to a CSV file.

    The CSV will contain three columns:
    ``feature``, ``primary_coeff`` and ``rf_importance``.

    Parameters
    ----------
    importance: dict
        Output of :func:`get_importance`.
    feature_names: list[str]
        Ordered list of feature names matching the vectors.
    output_path: pathlib.Path
        Destination CSV file. Parent directories are created if needed.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({
        "feature": feature_names,
        "primary_coeff": importance["primary_coeff"],
        "rf_importance": importance["rf_importance"],
    })
    df.to_csv(output_path, index=False)


def _load_feature_names(feature_path: pathlib.Path) -> List[str]:
    """
    Load feature names from a CSV file. The file is expected to contain a
    header row with column names; the feature list is taken from the header
    (i.e., the column order used during model training).
    """
    df = pd.read_csv(feature_path, nrows=0)
    return list(df.columns)


def main() -> None:
    """
    CLI entry point.

    Example
    -------
    python -m modeling.importance \\
        --primary-model data/model/primary.pkl \\
        --alternative-model data/model/alternative.pkl \\
        --features data/processed/train_features.csv \\
        --output data/model/feature_importance.csv
    """
    parser = argparse.ArgumentParser(
        description="Extract and store feature importance from trained models."
    )
    parser.add_argument(
        "--primary-model",
        type=pathlib.Path,
        required=True,
        help="Path to the pickled primary (logistic regression) model.",
    )
    parser.add_argument(
        "--alternative-model",
        type=pathlib.Path,
        required=True,
        help="Path to the pickled alternative (random forest) model.",
    )
    parser.add_argument(
        "--features",
        type=pathlib.Path,
        required=True,
        help="CSV file containing the feature columns used for training.",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        required=True,
        help="Destination CSV file for the importance vectors.",
    )

    args = parser.parse_args()

    # Load models
    primary_model = joblib.load(args.primary_model)
    alternative_model = joblib.load(args.alternative_model)

    # Load feature names (preserve order)
    feature_names = _load_feature_names(args.features)

    # Extract importance
    importance = get_importance(primary_model, alternative_model, feature_names)

    # Persist to CSV
    save_importance(importance, feature_names, args.output)

    print(f"Feature importance written to {args.output}")


if __name__ == "__main__":
    main()
