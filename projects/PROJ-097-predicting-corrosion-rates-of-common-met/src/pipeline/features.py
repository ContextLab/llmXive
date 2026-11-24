"""Feature engineering for corrosion prediction (T003).

This module creates interaction and polynomial features from the cleaned
dataset produced by ``src.pipeline.ingest``. It follows the specifications
in the project plan:

* Pairwise products among numeric environmental variables (ph, salinity,
  temperature).
* Interactions between each numeric environmental variable and each
  one‑hot encoded composition column.
* Degree‑2 polynomial terms for each numeric environmental variable.
* Orthogonalization (residualization) of each interaction column against its
  constituent main‑effect columns before adding to the feature matrix.

The resulting feature matrix is written to
``data/processed/features.parquet`` and a JSON list of feature names is
stored at ``data/processed/feature_names.json``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _numeric_env_columns(df: pd.DataFrame) -> List[str]:
    """Return the list of numeric environmental columns (canonical names)."""
    return [col for col in ("ph", "salinity", "temperature") if col in df.columns]

def _composition_one_hot_columns(df: pd.DataFrame) -> List[str]:
    """Return columns that are one‑hot encoded composition features.

    The ingestion step creates one‑hot columns prefixed with ``composition_``.
    An auxiliary column ``composition_original`` (the raw string label) is also
    added; it is **not** one‑hot encoded and should be excluded. We therefore
    filter by the prefix **and** ensure the column dtype is numeric (int/float).
    """
    return [
        col
        for col in df.columns
        if col.startswith("composition_")
        and pd.api.types.is_numeric_dtype(df[col])
    ]

def _residualize(series: pd.Series, predictors: pd.DataFrame) -> pd.Series:
    """Orthogonalize ``series`` against ``predictors`` using OLS residuals.

    Parameters
    ----------
    series: pd.Series
        The interaction column to be residualized.
    predictors: pd.DataFrame
        DataFrame containing the constituent main‑effect columns.

    Returns
    -------
    pd.Series
        Residuals (interaction column with linear dependence on predictors
        removed). If the regression cannot be solved (e.g., singular
        matrix), the original series is returned unchanged.
    """
    # Add intercept
    X = predictors.copy()
    X["intercept"] = 1.0
    try:
        # Solve least‑squares: beta = (X'X)^{-1} X'y
        beta, *_ = np.linalg.lstsq(X.values, series.values, rcond=None)
        y_hat = X.values @ beta
        residuals = series.values - y_hat
        return pd.Series(residuals, index=series.index, name=series.name)
    except np.linalg.LinAlgError as exc:
        log.warning(
            "Residualization failed for column %s (LinAlgError: %s); "
            "using original values.",
            series.name,
            exc,
        )
        return series

# ----------------------------------------------------------------------
# Main feature‑engineering workflow
# ----------------------------------------------------------------------
def build_features(cleaned_path: Path) -> pd.DataFrame:
    """Create the full feature matrix from the cleaned dataset.

    Parameters
    ----------
    cleaned_path: Path
        Path to ``cleaned_dataset.csv`` produced by the ingestion step.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the original predictors plus engineered
        interaction and polynomial columns.
    """
    df = pd.read_csv(cleaned_path)

    # Identify base columns.
    env_cols = _numeric_env_columns(df)
    comp_one_hot = _composition_one_hot_columns(df)

    # ------------------------------------------------------------------
    # 1. Polynomial (degree‑2) terms for numeric env variables.
    # ------------------------------------------------------------------
    poly_features = {}
    for col in env_cols:
        poly_name = f"{col}_sq"
        poly_features[poly_name] = df[col] ** 2

    # ------------------------------------------------------------------
    # 2. Pairwise products among numeric env variables.
    # ------------------------------------------------------------------
    interaction_features = {}
    for i, col_i in enumerate(env_cols):
        for col_j in env_cols[i + 1 :]:
            inter_name = f"{col_i}_x_{col_j}"
            interaction_features[inter_name] = df[col_i] * df[col_j]

    # ------------------------------------------------------------------
    # 3. Interactions between numeric env variables and composition one‑hot.
    # ------------------------------------------------------------------
    for env_col in env_cols:
        for comp_col in comp_one_hot:
            inter_name = f"{env_col}_x_{comp_col}"
            interaction_features[inter_name] = df[env_col] * df[comp_col]

    # ------------------------------------------------------------------
    # 4. Residualize each interaction column against its constituents.
    # ------------------------------------------------------------------
    residualized = {}
    for name, series in interaction_features.items():
        parts = name.split("_x_")
        if len(parts) != 2:
            residualized[name] = series
            continue
        # Determine which parts correspond to actual columns in the DataFrame.
        main_cols = [p for p in parts if p in df.columns]
        if len(main_cols) != 2:
            residualized[name] = series
            continue
        predictors = df[main_cols]
        residualized[name] = _residualize(series, predictors)

    # ------------------------------------------------------------------
    # 5. Assemble final feature matrix.
    # ------------------------------------------------------------------
    feature_df = df.copy()
    # Add polynomial features.
    for name, col in poly_features.items():
        feature_df[name] = col
    # Add residualized interaction columns.
    for name, col in residualized.items():
        feature_df[name] = col

    return feature_df

def main(argv: List[str] | None = None) -> int:
    """Entry point for ``python -m src.pipeline.features``.

    The command writes ``features.parquet`` and a JSON list of feature
    names to ``data/processed``.
    """
    # The cleaned dataset path is fixed by the pipeline contract.
    cleaned_path = paths.data("processed", "cleaned_dataset.csv")
    if not cleaned_path.is_file():
        log.error("Cleaned dataset not found at %s", cleaned_path)
        return 1

    log.info("Building engineered features from %s", cleaned_path)
    feature_df = build_features(cleaned_path)

    # Write Parquet file.
    out_path = paths.data("processed", "features.parquet")
    feature_df.to_parquet(out_path, index=False)
    log.info(
        "Feature matrix written to %s (%d columns, %d rows)",
        out_path,
        feature_df.shape[1],
        feature_df.shape[0],
    )

    # Store the list of feature names (excluding the target and grouping columns).
    feature_names = [
        c
        for c in feature_df.columns
        if c not in ("corrosion_rate", "source_id")
    ]
    names_path = paths.data("processed", "feature_names.json")
    with open(names_path, "w", encoding="utf-8") as fh:
        json.dump(feature_names, fh, indent=2)
    log.info("Feature name list written to %s", names_path)

    return 0

if __name__ == "__main__":
    import sys

    sys.exit(main())
