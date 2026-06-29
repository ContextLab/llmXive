"""
Collinearity diagnostics utilities.

This module provides functions to compute the Variance Inflation Factor (VIF)
for a set of numeric features and to iteratively drop features whose VIF
exceeds a configurable threshold. The resulting reduced feature set can be
used for downstream modeling to mitigate multicollinearity issues.

The script can also be executed directly from the command line:

    python code/modeling/collinearity.py <input_csv> <output_csv> [--vif-threshold 5.0]

The script reads a CSV dataset, treats all numeric columns (except the target
column ``bug_label`` if present) as candidate features, performs VIF‑based
pruning, and writes the reduced dataset to ``output_csv``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.logging import get_logger

__all__ = [
    "compute_vif",
    "drop_high_vif_features",
    "main",
]

LOGGER = get_logger(__name__)

def compute_vif(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Compute the Variance Inflation Factor (VIF) for each feature.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    features : List[str]
        List of column names to evaluate.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``feature`` and ``VIF``.
    """
    # Ensure we work on a copy to avoid side‑effects.
    X = df[features].dropna().copy()

    # Add constant term required by statsmodels for VIF calculation.
    X_const = sm.add_constant(X, has_constant='add')

    vif_records = []
    # Skip the constant column (index 0).
    for i in range(1, X_const.shape[1]):
        vif = variance_inflation_factor(X_const.values, i)
        vif_records.append({"feature": X_const.columns[i], "VIF": vif})

    vif_df = pd.DataFrame(vif_records)
    LOGGER.debug("Computed VIF values: %s", vif_df.to_dict(orient="records"))
    return vif_df

def drop_high_vif_features(
    df: pd.DataFrame,
    features: List[str],
    threshold: float = 5.0,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Iteratively drop features whose VIF exceeds ``threshold``.

    Parameters
    ----------
    df : pd.DataFrame
        Original DataFrame.
    features : List[str]
        List of candidate numeric feature column names.
    threshold : float, optional
        VIF threshold above which a feature is considered highly collinear.
        Default is 5.0.

    Returns
    -------
    Tuple[pd.DataFrame, List[str]]
        * A DataFrame containing the retained features (plus any non‑feature
          columns that were present in the original ``df``).
        * The list of retained feature names.
    """
    remaining_features = features.copy()
    iteration = 0

    while True:
        iteration += 1
        LOGGER.info("VIF iteration %d – evaluating %d features", iteration, len(remaining_features))
        vif_df = compute_vif(df, remaining_features)

        if vif_df.empty:
            LOGGER.warning("VIF DataFrame is empty; terminating early.")
            break

        max_vif = vif_df["VIF"].max()
        if max_vif <= threshold or len(remaining_features) <= 1:
            LOGGER.info(
                "All remaining features have VIF <= %.2f (max VIF = %.2f). Stopping.",
                threshold,
                max_vif,
            )
            break

        # Identify feature with the highest VIF to drop.
        drop_feature = vif_df.loc[vif_df["VIF"].idxmax(), "feature"]
        LOGGER.info(
            "Dropping feature '%s' with VIF = %.2f (threshold = %.2f)",
            drop_feature,
            max_vif,
            threshold,
        )
        remaining_features.remove(drop_feature)

    # Build the resulting DataFrame: keep all original non‑numeric columns
    # and the retained numeric features.
    non_feature_cols = [c for c in df.columns if c not in features]
    result_df = df[non_feature_cols + remaining_features].copy()
    LOGGER.debug("Final retained features: %s", remaining_features)
    return result_df, remaining_features

def _detect_numeric_features(df: pd.DataFrame, exclude: List[str] | None = None) -> List[str]:
    """
    Helper to infer numeric candidate features, excluding specified columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    exclude : List[str] | None
        Column names to exclude (e.g., target variable).

    Returns
    -------
    List[str]
        List of numeric column names suitable for VIF analysis.
    """
    exclude = set(exclude or [])
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    return [col for col in numeric_cols if col not in exclude]

def main() -> None:
    """
    Command‑line interface.

    Usage:
        python code/modeling/collinearity.py <input_csv> <output_csv> [--vif-threshold 5.0]

    The script reads ``input_csv``, performs VIF‑based feature pruning, and
    writes the reduced dataset to ``output_csv``.
    """
    parser = argparse.ArgumentParser(
        description="Perform VIF‑based collinearity diagnostics and drop highly collinear features."
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to the input dataset CSV file.",
    )
    parser.add_argument(
        "output_csv",
        type=Path,
        help="Path where the reduced dataset CSV will be written.",
    )
    parser.add_argument(
        "--vif-threshold",
        type=float,
        default=5.0,
        help="VIF threshold above which a feature will be dropped (default: 5.0).",
    )
    args = parser.parse_args()

    if not args.input_csv.is_file():
        LOGGER.error("Input file does not exist: %s", args.input_csv)
        sys.exit(1)

    try:
        df = pd.read_csv(args.input_csv)
    except Exception as exc:
        LOGGER.exception("Failed to read input CSV: %s", exc)
        sys.exit(1)

    # Exclude common non‑feature columns such as the target label.
    exclude_cols = ["bug_label"]
    candidate_features = _detect_numeric_features(df, exclude=exclude_cols)

    if not candidate_features:
        LOGGER.warning("No numeric candidate features found for VIF analysis.")
        df.to_csv(args.output_csv, index=False)
        sys.exit(0)

    reduced_df, kept_features = drop_high_vif_features(
        df,
        candidate_features,
        threshold=args.vif_threshold,
    )

    # Ensure the output directory exists.
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)

    reduced_df.to_csv(args.output_csv, index=False)
    LOGGER.info(
        "Collinearity reduction complete. Kept %d features out of %d.",
        len(kept_features),
        len(candidate_features),
    )
    LOGGER.info("Reduced dataset written to %s", args.output_csv)

if __name__ == "__main__":
    main()