"""
Feature Extraction Service

This module provides utilities for extracting training‑side features from a
DataFrame produced by the ground‑truth generation step and (optionally)
applying Principal Component Analysis (PCA) to reduce dimensionality.

The primary public API matches the expectations of the unit tests and any
downstream pipeline components:

* ``extract_features(df, columns=None)`` – Returns a NumPy ``ndarray`` of
  shape ``(n_samples, n_features)`` containing the selected columns.
* ``fit_pca(features, n_components=2, random_state=42)`` – Fits a
  ``sklearn.decomposition.PCA`` model on the provided feature matrix and
  returns a tuple ``(pca_model, transformed_features)``.
* ``apply_pca(pca_model, features)`` – Transforms a feature matrix using an
  already‑fitted PCA model.

The implementation is deliberately lightweight and reproducible:
* The default ``random_state`` for PCA is fixed (42) to guarantee identical
  results across runs, which satisfies the reproducibility verification.
* Input validation raises clear errors for missing columns or incorrect
  types, preventing silent failures later in the pipeline.
"""

from __future__ import annotations

import logging
from typing import List, Sequence, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

__all__: List[str] = [
    "extract_features",
    "fit_pca",
    "apply_pca",
]

_log = logging.getLogger(__name__)

def _validate_dataframe(df: pd.DataFrame, required_columns: Sequence[str]) -> None:
    """Validate that *df* contains all *required_columns*."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(
            f"The DataFrame is missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )
    if df.empty:
        raise ValueError("The input DataFrame is empty; cannot extract features.")

def extract_features(
    df: pd.DataFrame,
    columns: Optional[Sequence[str]] = None,
) -> np.ndarray:
    """
    Extract numeric feature columns from *df*.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame produced by ``code/cli/generate_ground_truth.py`` (or a
        downstream split). It must contain at least the columns
        ``gradient_norm`` and ``local_curvature``.
    columns: sequence of str, optional
        Column names to extract. If ``None`` the default set
        ``[\"gradient_norm\", \"local_curvature\"]`` is used.

    Returns
    -------
    np.ndarray
        A 2‑D array of shape ``(n_samples, n_features)`` with ``dtype=float``.
    """
    default_columns = ("gradient_norm", "local_curvature")
    cols = tuple(columns) if columns is not None else default_columns

    _log.debug("Extracting features %s from DataFrame with %d rows.", cols, len(df))
    _validate_dataframe(df, cols)

    # Ensure numeric conversion; non‑numeric entries raise.
    try:
        feature_array = df.loc[:, cols].to_numpy(dtype=np.float64, copy=True)
    except Exception as exc:
        raise TypeError(
            f"Failed to convert columns {cols} to numeric NumPy array: {exc}"
        ) from exc

    _log.debug("Extracted feature array shape: %s", feature_array.shape)
    return feature_array

def fit_pca(
    features: np.ndarray,
    n_components: int = 2,
    random_state: int = 42,
) -> Tuple[PCA, np.ndarray]:
    """
    Fit a PCA model to *features* and return the fitted model together with
    the transformed feature matrix.

    Parameters
    ----------
    features: np.ndarray
        Input feature matrix of shape ``(n_samples, n_features)``.
    n_components: int, default 2
        Number of principal components to retain.
    random_state: int, default 42
        Seed for reproducibility.

    Returns
    -------
    Tuple[PCA, np.ndarray]
        ``(pca_model, transformed_features)`` where ``transformed_features``
        has shape ``(n_samples, n_components)``.
    """
    if not isinstance(features, np.ndarray):
        raise TypeError("features must be a NumPy ndarray.")
    if features.ndim != 2:
        raise ValueError("features must be a 2‑D array (samples × features).")
    if n_components <= 0 or n_components > features.shape[1]:
        raise ValueError(
            f"n_components must be >0 and ≤ number of original features "
            f"({features.shape[1]}), got {n_components}."
        )

    _log.debug(
        "Fitting PCA: n_components=%d, random_state=%d, input shape=%s",
        n_components,
        random_state,
        features.shape,
    )
    pca = PCA(n_components=n_components, random_state=random_state, svd_solver="full")
    transformed = pca.fit_transform(features)
    _log.debug("PCA fitted. Explained variance ratio: %s", pca.explained_variance_ratio_)
    _log.debug("Transformed feature shape: %s", transformed.shape)
    return pca, transformed

def apply_pca(pca_model: PCA, features: np.ndarray) -> np.ndarray:
    """
    Transform *features* using an already‑fitted ``pca_model``.

    Parameters
    ----------
    pca_model: sklearn.decomposition.PCA
        Fitted PCA instance.
    features: np.ndarray
        Feature matrix with the same number of columns as used during
        ``pca_model`` fitting.

    Returns
    -------
    np.ndarray
        Transformed feature matrix of shape ``(n_samples, n_components)``.
    """
    if not isinstance(pca_model, PCA):
        raise TypeError("pca_model must be an instance of sklearn.decomposition.PCA.")
    if not isinstance(features, np.ndarray):
        raise TypeError("features must be a NumPy ndarray.")
    _log.debug(
        "Applying PCA transformation: input shape=%s, n_components=%d",
        features.shape,
        pca_model.n_components_,
    )
    transformed = pca_model.transform(features)
    _log.debug("PCA transformation result shape: %s", transformed.shape)
    return transformed
