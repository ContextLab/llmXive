"""
Statistical utilities for the LlmXive follow-up pipeline.

This module provides functions for computing Mahalanobis distances
using the Ledoit-Wolf covariance estimator, as required for anomaly
detection in latent space (FR-006).
"""

import logging
from typing import Optional, Tuple

import numpy as np
from numpy.linalg import LinAlgError
from sklearn.covariance import LedoitWolf

logger = logging.getLogger(__name__)


def compute_benign_statistics(
    benign_embeddings: np.ndarray,
    regularization: float = 1e-4
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the centroid (mean) and covariance matrix for a set of benign embeddings.

    This function uses the Ledoit-Wolf shrinkage estimator to provide a robust
    covariance estimate, which is critical when the number of samples is close
    to or smaller than the dimensionality of the embeddings.

    Args:
        benign_embeddings (np.ndarray): A 2D array of shape (n_samples, n_features)
            containing only benign (non-jailbreak) embeddings.
        regularization (float): A small value added to the diagonal of the covariance
            matrix during inversion to ensure numerical stability. Defaults to 1e-4.

    Returns:
        Tuple[np.ndarray, np.ndarray]: A tuple containing:
            - centroid (np.ndarray): The mean vector of shape (n_features,).
            - cov_matrix (np.ndarray): The regularized covariance matrix of shape
              (n_features, n_features).

    Raises:
        ValueError: If `benign_embeddings` is empty or has incorrect shape.
        LinAlgError: If the covariance matrix is singular and cannot be regularized.
    """
    if benign_embeddings.size == 0:
        raise ValueError("benign_embeddings cannot be empty.")

    if benign_embeddings.ndim != 2:
        raise ValueError(
            f"benign_embeddings must be a 2D array (n_samples, n_features). "
            f"Got shape: {benign_embeddings.shape}"
        )

    logger.info(
        f"Computing benign statistics for {benign_embeddings.shape[0]} samples "
        f"with dimensionality {benign_embeddings.shape[1]}"
    )

    # Calculate centroid
    centroid = np.mean(benign_embeddings, axis=0)

    # Calculate covariance using Ledoit-Wolf estimator
    try:
        estimator = LedoitWolf()
        estimator.fit(benign_embeddings)
        cov_matrix = estimator.covariance_
    except Exception as e:
        logger.error(f"Failed to compute Ledoit-Wolf covariance: {e}")
        raise

    # Add small regularization to diagonal for numerical stability during inversion
    cov_matrix += regularization * np.eye(cov_matrix.shape[0])

    logger.info("Benign statistics computed successfully (Ledoit-Wolf + regularization).")

    return centroid, cov_matrix


def calculate_mahalanobis_distance(
    embeddings: np.ndarray,
    centroid: np.ndarray,
    cov_matrix: np.ndarray,
    regularization: float = 1e-6
) -> np.ndarray:
    """
    Calculate the Mahalanobis distance of each sample from a reference centroid.

    The Mahalanobis distance is defined as:
        D_M(x) = sqrt( (x - μ)ᵀ Σ⁻¹ (x - μ) )
    where μ is the centroid and Σ is the covariance matrix.

    This metric measures how many standard deviations a sample is from the centroid,
    accounting for the correlations in the data. It is used here to score anomalies
    (potential jailbreaks) based on their deviation from the benign cluster.

    Args:
        embeddings (np.ndarray): A 2D array of shape (n_samples, n_features)
            for which to calculate distances.
        centroid (np.ndarray): The reference mean vector of shape (n_features,).
        cov_matrix (np.ndarray): The reference covariance matrix of shape
            (n_features, n_features).
        regularization (float): A small value added to the diagonal of the covariance
            matrix before inversion to prevent singularity errors. Defaults to 1e-6.

    Returns:
        np.ndarray: A 1D array of shape (n_samples,) containing the Mahalanobis
            distance for each input sample.

    Raises:
        ValueError: If input shapes are inconsistent.
        LinAlgError: If the covariance matrix is singular even after regularization.
    """
    if embeddings.ndim != 2:
        raise ValueError(
            f"embeddings must be a 2D array. Got shape: {embeddings.shape}"
        )

    if centroid.shape[0] != embeddings.shape[1]:
        raise ValueError(
            f"Dimension mismatch: centroid has {centroid.shape[0]} features, "
            f"but embeddings have {embeddings.shape[1]}."
        )

    if cov_matrix.shape != (embeddings.shape[1], embeddings.shape[1]):
        raise ValueError(
            f"Covariance matrix shape {cov_matrix.shape} does not match "
            f"embedding dimension {embeddings.shape[1]}."
        )

    logger.info(f"Calculating Mahalanobis distances for {embeddings.shape[0]} samples.")

    # Center the data
    diff = embeddings - centroid

    # Regularize covariance matrix
    cov_reg = cov_matrix + regularization * np.eye(cov_matrix.shape[0])

    try:
        # Compute inverse of covariance matrix
        cov_inv = np.linalg.inv(cov_reg)
    except LinAlgError as e:
        logger.error(f"Failed to invert covariance matrix: {e}")
        raise

    # Calculate Mahalanobis distance: sqrt( (x-μ) Σ⁻¹ (x-μ)ᵀ )
    # Using einsum for efficient batch computation: sum over features (i, j)
    # diff shape: (N, D), cov_inv shape: (D, D)
    # result: (N, D) @ (D, D) @ (D, N) -> (N, N) diagonal elements
    # We want vector of length N: sum_k sum_l diff_i_k * cov_inv_kl * diff_i_l
    mahal_sq = np.einsum('ij,jk,ik->i', diff, cov_inv, diff)

    # Ensure no negative values due to numerical errors
    mahal_sq = np.maximum(mahal_sq, 0.0)
    distances = np.sqrt(mahal_sq)

    logger.info(f"Mahalanobis distance calculation complete. "
                f"Min: {distances.min():.4f}, Max: {distances.max():.4f}, Mean: {distances.mean():.4f}")

    return distances