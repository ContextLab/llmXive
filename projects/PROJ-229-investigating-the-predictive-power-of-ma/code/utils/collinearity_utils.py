"""
Collinearity utilities for the project.

Provides simple VIF‑style diagnostics and a helper to identify pairs of
features that exhibit high linear correlation. The implementation avoids
heavyweight dependencies (e.g. ``statsmodels``) and therefore works in the
constrained execution environment used by the CI runner.

All functions raise ``DataProcessingError`` (defined in
``code.utils.error_handling``) when they encounter unexpected input.
"""

import logging
from typing import List, Tuple

import numpy as np
import pandas as pd

# Import the custom error class using a relative import to avoid circular
# dependencies with ``code.utils.logger``.
from .error_handling import DataProcessingError

_logger = logging.getLogger("pipeline")


def _validate_dataframe(df: pd.DataFrame) -> None:
    """Validate that the input is a non‑empty DataFrame with numeric columns."""
    if not isinstance(df, pd.DataFrame):
        raise DataProcessingError("Input must be a pandas DataFrame.")
    if df.empty:
        raise DataProcessingError("Input DataFrame is empty.")
    if not all(np.issubdtype(dt, np.number) for dt in df.dtypes):
        raise DataProcessingError("All columns must contain numeric data.")


def calculate_vif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a simple Variance Inflation Factor (VIF) for each column.

    The classic VIF definition requires regressing each feature against all
    others. To keep the implementation lightweight we approximate it using
    the correlation matrix:

        VIF_i ≈ 1 / (1 - max_j |corr(i, j)|²)

    This approximation is sufficient for flagging problematic multicollinearity
    in the pipeline.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing only numeric feature columns.

    Returns
    -------
    pd.DataFrame
        A DataFrame with columns ``feature`` and ``vif`` sorted by descending
        VIF value.
    """
    try:
        _validate_dataframe(df)
        corr = df.corr().abs()
        # Replace diagonal with zeros to ignore self‑correlation
        np.fill_diagonal(corr.values, 0.0)
        max_corr_sq = (corr ** 2).max(axis=1)
        # Guard against division by zero (perfect collinearity)
        with np.errstate(divide="ignore", invalid="ignore"):
            vif = 1.0 / (1.0 - max_corr_sq)
        vif.replace([np.inf, -np.inf], np.nan, inplace=True)
        vif_df = pd.DataFrame({"feature": df.columns, "vif": vif.values})
        vif_df.sort_values(by="vif", ascending=False, inplace=True)
        vif_df.reset_index(drop=True, inplace=True)
        _logger.debug("Calculated VIF for %d features.", len(df.columns))
        return vif_df
    except Exception as exc:
        raise DataProcessingError(f"Failed to calculate VIF: {exc}") from exc


def identify_high_collinearity(
    df: pd.DataFrame, vif_threshold: float = 5.0, corr_threshold: float = 0.9
) -> List[Tuple[str, str, float]]:
    """
    Identify pairs of features that exceed collinearity thresholds.

    The function uses two complementary heuristics:
    1. VIF greater than ``vif_threshold`` (default 5.0).
    2. Absolute Pearson correlation greater than ``corr_threshold``
       (default 0.9).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with numeric features.
    vif_threshold : float, optional
        Minimum VIF to consider a feature problematic.
    corr_threshold : float, optional
        Minimum absolute correlation to flag a pair.

    Returns
    -------
    List[Tuple[str, str, float]]
        List of tuples ``(feature_i, feature_j, correlation)`` for each
        flagged pair, ordered by descending absolute correlation.
    """
    try:
        _validate_dataframe(df)

        # First, compute VIF and drop features that are already flagged by VIF
        vif_df = calculate_vif(df)
        high_vif_features = set(vif_df[vif_df["vif"] > vif_threshold]["feature"])

        # Compute correlation matrix
        corr_matrix = df.corr()
        flagged_pairs: List[Tuple[str, str, float]] = []

        for i, col_i in enumerate(df.columns):
            for j in range(i + 1, len(df.columns)):
                col_j = df.columns[j]
                corr_val = corr_matrix.at[col_i, col_j]
                if abs(corr_val) >= corr_threshold:
                    flagged_pairs.append((col_i, col_j, corr_val))

        # Additionally flag any pair where at least one member has high VIF
        if high_vif_features:
            for i, col_i in enumerate(df.columns):
                for j in range(i + 1, len(df.columns)):
                    col_j = df.columns[j]
                    if col_i in high_vif_features or col_j in high_vif_features:
                        corr_val = corr_matrix.at[col_i, col_j]
                        flagged_pairs.append((col_i, col_j, corr_val))

        # Remove duplicates (possible if both heuristics flagged the same pair)
        unique_pairs = {}
        for a, b, c in flagged_pairs:
            key = tuple(sorted((a, b)))
            if key not in unique_pairs or abs(c) > abs(unique_pairs[key][2]):
                unique_pairs[key] = (a, b, c)

        result = sorted(unique_pairs.values(), key=lambda x: abs(x[2]), reverse=True)
        _logger.debug(
            "Identified %d high‑collinearity pairs (VIF>%.1f or |corr|>%.2f).",
            len(result),
            vif_threshold,
            corr_threshold,
        )
        return result
    except Exception as exc:
        raise DataProcessingError(
            f"Failed to identify high collinearity: {exc}"
        ) from exc