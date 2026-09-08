"""
Collinearity utilities for VIF analysis (T014).

This module provides:
- ``calculate_vif``: Compute the Variance Inflation Factor for each feature.
- ``identify_high_collinearity``: Return a list of features whose VIF exceeds a threshold.

The implementation follows the classic definition VIF = 1 / (1 - R²) where R² is obtained
by regressing each feature against all the others.  Constant columns are removed before
calculation because they would lead to singular matrices.

The functions are deliberately lightweight and have no external dependencies beyond
``numpy`` and ``pandas`` so they can be used in streaming contexts or on large datasets.
"""
import logging
from typing import List

import numpy as np
import pandas as pd

# NOTE: All other project modules import the logger via ``utils.logger``.
# The original code used ``code.utils.logger`` which is not a valid import path
# given the project's API surface.  The corrected import below matches the
# declared public names.
from utils.logger import get_pipeline_logger
from utils.error_handling import DataProcessingError

logger = get_pipeline_logger(__name__)

def _select_feature_columns(df: pd.DataFrame, column_prefix: str) -> List[str]:
    """Return a list of column names that start with ``column_prefix``.
    If ``column_prefix`` is an empty string, all numeric columns are returned.
    """
    if column_prefix:
        return [col for col in df.columns if col.startswith(column_prefix)]
    # Fallback: use all numeric columns
    return [col for col, dtype in df.dtypes.items() if np.issubdtype(dtype, np.number)]

def calculate_vif(df: pd.DataFrame, column_prefix: str = 'feat_') -> pd.DataFrame:
    """
    Calculate the Variance Inflation Factor (VIF) for each feature column.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the features (and possibly other columns).
    column_prefix : str, optional
        Prefix that identifies feature columns.  If empty, all numeric columns
        are considered.

    Returns
    -------
    pd.DataFrame
        A DataFrame with two columns: ``feature`` and ``VIF``.
    """
    logger.info("Starting VIF calculation.")
    feature_cols = _select_feature_columns(df, column_prefix)

    if len(feature_cols) < 2:
        logger.warning(
            "Not enough feature columns (found %d) for VIF calculation.", len(feature_cols)
        )
        return pd.DataFrame({'feature': [], 'VIF': []})

    # Extract the feature matrix
    X = df[feature_cols].to_numpy(dtype=float)

    # Detect and drop constant columns (zero variance)
    variances = X.var(axis=0)
    constant_mask = variances == 0
    if constant_mask.any():
        constant_cols = [feature_cols[i] for i, is_const in enumerate(constant_mask) if is_const]
        logger.warning("Constant columns detected and will be removed: %s", constant_cols)
        X = X[:, ~constant_mask]
        feature_cols = [col for i, col in enumerate(feature_cols) if not constant_mask[i]]

    if X.shape[1] < 2:
        logger.warning(
            "Insufficient non‑constant features after removal (found %d).", X.shape[1]
        )
        # By definition VIF for a single predictor is 1
        return pd.DataFrame({'feature': feature_cols, 'VIF': [1.0] * len(feature_cols)})

    vif_records = []
    n_samples = X.shape[0]

    for i, col in enumerate(feature_cols):
        try:
            y = X[:, i]
            X_others = np.delete(X, i, axis=1)

            # Add intercept term
            X_others_with_intercept = np.column_stack((np.ones(n_samples), X_others))

            # Ordinary Least Squares solution
            beta, residuals, rank, s = np.linalg.lstsq(
                X_others_with_intercept, y, rcond=None
            )
            y_pred = X_others_with_intercept @ beta

            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)

            # Guard against division by zero
            if ss_tot == 0:
                r_squared = 0.0
            else:
                r_squared = 1 - ss_res / ss_tot

            # VIF = 1 / (1 - R^2); protect against values very close to 1
            denominator = 1.0 - r_squared
            if denominator < 1e-10:
                vif = np.inf
            else:
                vif = 1.0 / denominator

            vif_records.append({'feature': col, 'VIF': vif})
        except Exception as exc:
            logger.error("Failed VIF calculation for column %s: %s", col, exc)
            # Record an infinite VIF to flag the problem
            vif_records.append({'feature': col, 'VIF': np.inf})

    vif_df = pd.DataFrame(vif_records)
    logger.info("VIF calculation completed for %d features.", len(vif_df))
    return vif_df

def identify_high_collinearity(vif_df: pd.DataFrame, threshold: float = 10.0) -> List[str]:
    """
    Identify features whose VIF exceeds ``threshold``.

    Parameters
    ----------
    vif_df : pd.DataFrame
        DataFrame produced by :func:`calculate_vif` containing a ``VIF`` column.
    threshold : float, optional
        VIF value above which a feature is considered highly collinear.

    Returns
    -------
    List[str]
        Feature names with VIF > ``threshold``.  Returns an empty list if
        ``vif_df`` is empty or no feature exceeds the threshold.
    """
    if vif_df.empty:
        logger.debug("Received empty VIF DataFrame; returning empty list.")
        return []

    high_vif = vif_df[vif_df['VIF'] > threshold]
    high_features = high_vif['feature'].tolist()
    logger.debug(
        "Identified %d high‑collinearity features (threshold=%s).",
        len(high_features),
        threshold,
    )
    return high_features

if __name__ == "__main__":
    # Simple sanity check when the module is executed directly.
    # This block is *not* part of the library API.
    np.random.seed(0)
    df_demo = pd.DataFrame(
        {
            "feat_a": np.random.rand(100),
            "feat_b": np.random.rand(100),
            "feat_c": np.random.rand(100),
        }
    )
    # Introduce a perfectly collinear column
    df_demo["feat_d"] = df_demo["feat_a"] * 1.1

    vif_res = calculate_vif(df_demo, column_prefix="feat_")
    print(vif_res)

    high = identify_high_collinearity(vif_res, threshold=10.0)
    print("High VIF features:", high)