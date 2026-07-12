"""
Statistical utilities for the LLMXive pipeline.
Implements Mahalanobis distance calculation using Ledoit-Wolf covariance estimation.
"""
import numpy as np
from numpy.linalg import LinAlgError
from sklearn.covariance import LedoitWolf
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def compute_benign_statistics(
    benign_embeddings: np.ndarray,
    regularization: float = 1e-6
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the centroid (mean) and regularized covariance matrix for benign samples.
    
    Args:
        benign_embeddings: 2D numpy array of shape (N, D) containing benign embeddings.
        regularization: Small value added to diagonal for numerical stability.
        
    Returns:
        Tuple of (centroid, covariance)
        - centroid: 1D array of shape (D,)
        - covariance: 2D array of shape (D, D)
    """
    if benign_embeddings.ndim != 2:
        raise ValueError(f"Expected 2D array, got {benign_embeddings.ndim}D")
    if benign_embeddings.shape[0] == 0:
        raise ValueError("Benign embeddings array is empty")
        
    logger.info(f"Computing statistics for {benign_embeddings.shape[0]} benign samples")
    
    centroid = np.mean(benign_embeddings, axis=0)
    
    # Use Ledoit-Wolf estimator for robust covariance
    try:
        lw = LedoitWolf()
        lw.fit(benign_embeddings)
        covariance = lw.covariance_
    except Exception as e:
        logger.warning(f"Ledoit-Wolf failed: {e}. Falling back to empirical covariance.")
        covariance = np.cov(benign_embeddings, rowvar=False)
        
    # Add regularization for numerical stability
    covariance += regularization * np.eye(covariance.shape[0])
    
    logger.info(f"Computed centroid (norm: {np.linalg.norm(centroid):.4f}) and covariance")
    return centroid, covariance


def calculate_mahalanobis_distance(
    embeddings: np.ndarray,
    centroid: np.ndarray,
    covariance: np.ndarray
) -> np.ndarray:
    """
    Calculate Mahalanobis distance from the centroid for each sample.
    
    Args:
        embeddings: 2D numpy array of shape (N, D) containing samples to score.
        centroid: 1D array of shape (D,) representing the benign centroid.
        covariance: 2D array of shape (D, D) representing the benign covariance.
        
    Returns:
        1D array of shape (N,) containing Mahalanobis distances.
    """
    if embeddings.ndim != 2:
        raise ValueError(f"Expected 2D embeddings, got {embeddings.ndim}D")
    if centroid.ndim != 1 or covariance.ndim != 2:
        raise ValueError("Centroid and covariance must be 1D and 2D respectively")
    if embeddings.shape[1] != centroid.shape[0]:
        raise ValueError(f"Embedding dim {embeddings.shape[1]} != centroid dim {centroid.shape[0]}")
        
    logger.info(f"Calculating Mahalanobis distance for {embeddings.shape[0]} samples")
    
    # Compute (x - mu) * inv(Sigma) * (x - mu)^T
    diff = embeddings - centroid
    
    try:
        # Use cholesky decomposition for numerical stability
        L = np.linalg.cholesky(covariance)
        # Solve L * y = diff^T for y, then solve L^T * z = y for z
        # This gives z = inv(Sigma) * diff^T
        y = np.linalg.solve(L, diff.T)
        z = np.linalg.solve(L.T, y)
        # Mahalanobis distance is sqrt(diff * z)
        mahal_dist = np.sqrt(np.sum(diff * z.T, axis=1))
    except LinAlgError as e:
        logger.warning(f"Cholesky decomposition failed: {e}. Using pseudo-inverse.")
        # Fallback to pseudo-inverse
        inv_cov = np.linalg.pinv(covariance)
        mahal_dist = np.sqrt(np.sum(diff @ inv_cov * diff, axis=1))
        
    logger.info(f"Mahalanobis distance stats: min={np.min(mahal_dist):.4f}, "
               f"max={np.max(mahal_dist):.4f}, mean={np.mean(mahal_dist):.4f}")
               
    return mahal_dist
