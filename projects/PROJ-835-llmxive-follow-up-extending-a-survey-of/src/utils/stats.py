"""
src.utils.stats
----------------

Statistical utilities for the LlmXive follow‑up pipeline.

This module implements the Mahalanobis‑distance based anomaly detection
required by functional requirement **FR‑006**.  The core workflow consists
of two steps:

1. **Compute benign statistics** – Given a matrix of embeddings that are
   known to be *benign* (i.e. not jailbreak attempts), compute a robust
   estimate of the centroid (mean vector) and the covariance matrix.  The
   covariance is estimated with the :class:`sklearn.covariance.LedoitWolf`
   shrinkage estimator which is well‑suited for high‑dimensional data where
   the number of samples may be comparable to the embedding dimensionality.
2. **Calculate Mahalanobis distances** – For any set of embeddings (benign
   or adversarial) compute the Mahalanobis distance to the benign centroid
   using the covariance matrix from step 1.  Large distances indicate that
   a sample lies far outside the benign manifold and are therefore treated
   as potential anomalies.

The public API consists of three convenience functions:

* :func:`compute_benign_statistics` – Returns the centroid and regularised
  covariance matrix for a benign embedding matrix.
* :func:`calculate_mahalanobis_distance` – Returns a 1‑D array of Mahalanobis
  distances for a set of embeddings.
* :func:`compute_mahalanobis_for_embeddings` – End‑to‑end helper that
  receives the full embedding matrix together with a boolean mask that
  selects the benign rows, computes the statistics, and returns the
  distances for *all* embeddings.

All functions raise informative exceptions for invalid inputs and emit
structured log messages via the standard ``logging`` module.  The module
has no side‑effects other than logging, making it safe to import from any
part of the pipeline (training, evaluation, anomaly‑score generation, …).

Example
-------
>>> import numpy as np
>>> from src.utils.stats import compute_mahalanobis_for_embeddings
>>> # ``embeddings`` is a (N, D) ndarray, ``is_benign`` a boolean mask of length N
>>> distances = compute_mahalanobis_for_embeddings(embeddings, is_benign)
>>> distances.shape
(N,)

The implementation follows the mathematical definition:

.. math::
    D_M(x) = \sqrt{(x - \mu)^{\\top}\\,\\Sigma^{-1}\\,(x - \mu)}

where :math:`\\mu` is the benign centroid and :math:`\\Sigma` the
covariance matrix (regularised for numerical stability).

"""

import logging
from typing import Tuple

import numpy as np
from numpy.linalg import LinAlgError
from sklearn.covariance import LedoitWolf

__all__ = [
    "compute_benign_statistics",
    "calculate_mahalanobis_distance",
    "compute_mahalanobis_for_embeddings",
]

logger = logging.getLogger(__name__)


def compute_benign_statistics(
    benign_embeddings: np.ndarray,
    regularization: float = 1e-4,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the centroid (mean) and regularised covariance matrix for a set of
    benign embeddings.

    Parameters
    ----------
    benign_embeddings : np.ndarray
        A 2‑D array of shape ``(n_samples, n_features)`` containing only
        benign (non‑jailbreak) embeddings.
    regularization : float, optional
        Small value added to the diagonal of the covariance matrix before
        inversion to improve numerical stability (default ``1e-4``).

    Returns
    -------
    centroid : np.ndarray
        Mean vector of shape ``(n_features,)``.
    cov_matrix : np.ndarray
        Regularised covariance matrix of shape ``(n_features, n_features)``.

    Raises
    ------
    ValueError
        If ``benign_embeddings`` is empty or not two‑dimensional.
    LinAlgError
        If the covariance matrix cannot be regularised/inverted.
    """
    if benign_embeddings.size == 0:
        raise ValueError("benign_embeddings cannot be empty.")

    if benign_embeddings.ndim != 2:
        raise ValueError(
            f"benign_embeddings must be a 2‑D array (n_samples, n_features). "
            f"Got shape: {benign_embeddings.shape}"
        )

    logger.info(
        "Computing benign statistics for %d samples with dimensionality %d",
        benign_embeddings.shape[0],
        benign_embeddings.shape[1],
    )

    # Compute centroid
    centroid = np.mean(benign_embeddings, axis=0)

    # Estimate covariance with Ledoit‑Wolf shrinkage
    try:
        estimator = LedoitWolf()
        estimator.fit(benign_embeddings)
        cov_matrix = estimator.covariance_
    except Exception as exc:  # pragma: no cover – unexpected external error
        logger.error("Failed to compute Ledoit‑Wolf covariance: %s", exc)
        raise

    # Regularise diagonal to ensure invertibility
    cov_matrix += regularization * np.eye(cov_matrix.shape[0])

    logger.info("Benign statistics computed successfully.")
    return centroid, cov_matrix


def calculate_mahalanobis_distance(
    embeddings: np.ndarray,
    centroid: np.ndarray,
    cov_matrix: np.ndarray,
    regularization: float = 1e-6,
) -> np.ndarray:
    """
    Calculate the Mahalanobis distance of each sample from a reference centroid.

    The Mahalanobis distance is defined as::

        D_M(x) = sqrt( (x - μ)^T Σ⁻¹ (x - μ) )

    where ``μ`` is the centroid and ``Σ`` the covariance matrix.

    Parameters
    ----------
    embeddings : np.ndarray
        2‑D array ``(n_samples, n_features)`` to evaluate.
    centroid : np.ndarray
        1‑D array ``(n_features,)`` representing the reference mean.
    cov_matrix : np.ndarray
        2‑D array ``(n_features, n_features)`` covariance matrix.
    regularization : float, optional
        Small value added to the diagonal of ``cov_matrix`` before inversion
        (default ``1e-6``).

    Returns
    -------
    distances : np.ndarray
        1‑D array ``(n_samples,)`` of Mahalanobis distances.

    Raises
    ------
    ValueError
        If input shapes are inconsistent.
    LinAlgError
        If the covariance matrix remains singular after regularisation.
    """
    if embeddings.ndim != 2:
        raise ValueError(
            f"embeddings must be a 2‑D array. Got shape: {embeddings.shape}"
        )

    if centroid.ndim != 1 or centroid.shape[0] != embeddings.shape[1]:
        raise ValueError(
            f"Centroid shape {centroid.shape} incompatible with embeddings "
            f"dimension {embeddings.shape[1]}."
        )

    if cov_matrix.shape != (embeddings.shape[1], embeddings.shape[1]):
        raise ValueError(
            f"Covariance matrix shape {cov_matrix.shape} does not match "
            f"embedding dimension {embeddings.shape[1]}."
        )

    logger.info("Calculating Mahalanobis distances for %d samples.", embeddings.shape[0])

    # Center the data
    diff = embeddings - centroid

    # Regularise covariance matrix
    cov_reg = cov_matrix + regularization * np.eye(cov_matrix.shape[0])

    try:
        cov_inv = np.linalg.inv(cov_reg)
    except LinAlgError as exc:
        logger.error("Failed to invert covariance matrix: %s", exc)
        raise

    # Efficient batch computation using einsum
    mahal_sq = np.einsum("ij,jk,ik->i", diff, cov_inv, diff)

    # Guard against negative values due to numerical error
    mahal_sq = np.maximum(mahal_sq, 0.0)
    distances = np.sqrt(mahal_sq)

    logger.info(
        "Mahalanobis distance calculation complete. min=%.4f, max=%.4f, mean=%.4f",
        distances.min(),
        distances.max(),
        distances.mean(),
    )
    return distances


def compute_mahalanobis_for_embeddings(
    embeddings: np.ndarray,
    benign_mask: np.ndarray,
    regularization_stats: float = 1e-4,
    regularization_distance: float = 1e-6,
) -> np.ndarray:
    """
    End‑to‑end helper that computes Mahalanobis distances for *all* embeddings
    given a boolean mask that selects the benign subset.

    This function is convenient for the typical pipeline step where a
    single Parquet/NPY file contains both benign and jailbreak embeddings.
    The caller supplies a ``benign_mask`` (``True`` for benign rows) and
    receives a distance vector of the same length as ``embeddings``.

    Parameters
    ----------
    embeddings : np.ndarray
        Full embedding matrix of shape ``(n_samples, n_features)``.
    benign_mask : np.ndarray
        1‑D boolean array of length ``n_samples`` indicating which rows are
        benign.  Must contain at least one ``True`` value.
    regularization_stats : float, optional
        Regularisation added to the covariance matrix during the statistics
        computation (default ``1e-4``).
    regularization_distance : float, optional
        Regularisation added to the covariance matrix before inverting it
        for distance calculation (default ``1e-6``).

    Returns
    -------
    distances : np.ndarray
        1‑D array of Mahalanobis distances for every row in ``embeddings``.

    Raises
    ------
    ValueError
        If ``benign_mask`` is not boolean, has incorrect length, or selects
        no samples.
    """
    if benign_mask.dtype != bool:
        raise ValueError("benign_mask must be a boolean array.")
    if benign_mask.shape[0] != embeddings.shape[0]:
        raise ValueError(
            "benign_mask length must match number of embedding rows."
        )
    if not np.any(benign_mask):
        raise ValueError("benign_mask must select at least one benign sample.")

    logger.info(
        "Computing Mahalanobis distances for %d total samples "
        "(%d benign, %d jailbreak).",
        embeddings.shape[0],
        benign_mask.sum(),
        (~benign_mask).sum(),
    )

    benign_embeddings = embeddings[benign_mask]
    centroid, cov_matrix = compute_benign_statistics(
        benign_embeddings, regularization=regularization_stats
    )
    distances = calculate_mahalanobis_distance(
        embeddings, centroid, cov_matrix, regularization=regularization_distance
    )
    return distances