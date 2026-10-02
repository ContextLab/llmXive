"""
Log-likelihood implementation using the full covariance matrix.
Employs Cholesky decomposition for numerical stability.
"""
import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import logging
from scipy.linalg import cholesky, cho_solve, LinAlgError

from models.physics import yukawa_force, newtonian_force
from config import get_logger, ProjectConfig

logger = get_logger(__name__)


def load_covariance_matrix(path: Path) -> np.ndarray:
    """
    Load the full covariance matrix from a .npy file.
    
    Args:
        path: Path to the .npy file containing the covariance matrix.
        
    Returns:
        The covariance matrix as a 2D numpy array.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the loaded data is not a 2D array.
    """
    if not path.exists():
        raise FileNotFoundError(f"Covariance matrix file not found: {path}")
    
    cov_matrix = np.load(path)
    
    if cov_matrix.ndim != 2:
        raise ValueError(f"Expected 2D covariance matrix, got shape {cov_matrix.shape}")
        
    logger.info(f"Loaded covariance matrix from {path} with shape {cov_matrix.shape}")
    return cov_matrix


def compute_cholesky_decomposition(cov_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Cholesky decomposition of the covariance matrix for efficient likelihood calculation.
    
    The decomposition C = L @ L.T is computed, where L is lower triangular.
    We return L and its inverse (L_inv) for use in the log-likelihood function.
    
    Args:
        cov_matrix: The covariance matrix (must be positive definite).
        
    Returns:
        Tuple of (L, L_inv) where L is the lower triangular Cholesky factor
        and L_inv is its inverse.
        
    Raises:
        LinAlgError: If the matrix is not positive definite.
    """
    try:
        # Compute Cholesky decomposition: C = L @ L.T
        L = cholesky(cov_matrix, lower=True)
        
        # Compute inverse of L for efficient solving
        # Since L is lower triangular, we can solve L @ x = I efficiently
        n = L.shape[0]
        L_inv = np.linalg.inv(L)
        
        logger.info("Cholesky decomposition computed successfully")
        return L, L_inv
        
    except LinAlgError as e:
        logger.error(f"Cholesky decomposition failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Cholesky decomposition: {e}")
        raise


def log_likelihood_newtonian(
    separation_m: np.ndarray,
    force_n: np.ndarray,
    cov_matrix: np.ndarray,
    L_inv: Optional[np.ndarray] = None
) -> float:
    """
    Compute the log-likelihood for the Newtonian force model.
    
    The likelihood is based on a Gaussian error model:
    log L = -0.5 * (N * log(2*pi) + log|C| + (y - f(x))^T @ C^-1 @ (y - f(x)))
    
    Using Cholesky decomposition: C^-1 = (L^-1)^T @ L^-1
    and log|C| = 2 * sum(log(diag(L)))
    
    Args:
        separation_m: Array of separation distances in meters.
        force_n: Array of measured forces in Newtons.
        cov_matrix: The full covariance matrix.
        L_inv: Pre-computed inverse of the Cholesky factor L.
               If None, it will be computed from cov_matrix.
               
    Returns:
        The log-likelihood value.
    """
    # Compute Newtonian force predictions
    predicted_force = newtonian_force(separation_m)
    
    # Compute residuals
    residuals = force_n - predicted_force
    
    # Ensure L_inv is available
    if L_inv is None:
        L, L_inv = compute_cholesky_decomposition(cov_matrix)
    
    # Compute the Mahalanobis distance: residuals^T @ C^-1 @ residuals
    # Using Cholesky: C^-1 = (L^-1)^T @ L^-1
    # So: residuals^T @ (L^-1)^T @ L^-1 @ residuals = ||L^-1 @ residuals||^2
    transformed_residuals = L_inv @ residuals
    mahalanobis_dist = np.sum(transformed_residuals ** 2)
    
    # Compute log determinant: log|C| = 2 * sum(log(diag(L)))
    # We need L for this, so compute it if not available
    if L_inv is not None:
        # Reconstruct L from L_inv is not straightforward, so we recompute L
        # Actually, we can get L from the Cholesky decomposition again
        # But we can also compute log|C| from the determinant of C directly
        # However, for numerical stability, we prefer the Cholesky approach
        # Let's recompute L to get its diagonal
        L = cholesky(cov_matrix, lower=True)
        log_det = 2 * np.sum(np.log(np.diag(L)))
    else:
        L = cholesky(cov_matrix, lower=True)
        log_det = 2 * np.sum(np.log(np.diag(L)))
    
    n = len(force_n)
    log_likelihood = -0.5 * (n * np.log(2 * np.pi) + log_det + mahalanobis_dist)
    
    return log_likelihood


def log_likelihood_yukawa(
    separation_m: np.ndarray,
    force_n: np.ndarray,
    cov_matrix: np.ndarray,
    alpha: float,
    lambda_m: float,
    L_inv: Optional[np.ndarray] = None
) -> float:
    """
    Compute the log-likelihood for the Yukawa-modified force model.
    
    The likelihood is based on a Gaussian error model:
    log L = -0.5 * (N * log(2*pi) + log|C| + (y - f(x))^T @ C^-1 @ (y - f(x)))
    
    Using Cholesky decomposition: C^-1 = (L^-1)^T @ L^-1
    and log|C| = 2 * sum(log(diag(L)))
    
    Args:
        separation_m: Array of separation distances in meters.
        force_n: Array of measured forces in Newtons.
        cov_matrix: The full covariance matrix.
        alpha: Yukawa strength parameter (dimensionless).
        lambda_m: Yukawa range parameter in meters.
        L_inv: Pre-computed inverse of the Cholesky factor L.
               If None, it will be computed from cov_matrix.
               
    Returns:
        The log-likelihood value.
    """
    # Compute Yukawa force predictions
    predicted_force = yukawa_force(separation_m, alpha, lambda_m)
    
    # Compute residuals
    residuals = force_n - predicted_force
    
    # Ensure L_inv is available
    if L_inv is None:
        L, L_inv = compute_cholesky_decomposition(cov_matrix)
    
    # Compute the Mahalanobis distance: residuals^T @ C^-1 @ residuals
    transformed_residuals = L_inv @ residuals
    mahalanobis_dist = np.sum(transformed_residuals ** 2)
    
    # Compute log determinant: log|C| = 2 * sum(log(diag(L)))
    # We need L for this
    L = cholesky(cov_matrix, lower=True)
    log_det = 2 * np.sum(np.log(np.diag(L)))
    
    n = len(force_n)
    log_likelihood = -0.5 * (n * np.log(2 * np.pi) + log_det + mahalanobis_dist)
    
    return log_likelihood


def main():
    """
    Main function to demonstrate the likelihood computation.
    Loads the harmonized dataset and covariance matrix, then computes
    the log-likelihood for both Newtonian and Yukawa models.
    """
    config = ProjectConfig()
    
    # Paths to data
    data_path = config.data_processed_dir / "harmonized_dataset.npy"
    cov_path = config.data_processed_dir / "covariance_matrix.npy"
    
    if not data_path.exists():
        logger.error(f"Harmonized dataset not found at {data_path}")
        logger.info("Please run the data harmonization pipeline first.")
        return
        
    if not cov_path.exists():
        logger.error(f"Covariance matrix not found at {cov_path}")
        logger.info("Please run the covariance construction pipeline first.")
        return
    
    # Load data
    from data.loaders import load_harmonized_data
    dataset = load_harmonized_data(data_path)
    
    logger.info(f"Loaded dataset with {len(dataset.separation_m)} points")
    
    # Load covariance matrix
    cov_matrix = load_covariance_matrix(cov_path)
    
    # Compute Cholesky decomposition
    L, L_inv = compute_cholesky_decomposition(cov_matrix)
    
    # Compute log-likelihood for Newtonian model
    ll_newtonian = log_likelihood_newtonian(
        dataset.separation_m,
        dataset.force_n,
        cov_matrix,
        L_inv
    )
    logger.info(f"Newtonian log-likelihood: {ll_newtonian:.4f}")
    
    # Compute log-likelihood for Yukawa model with sample parameters
    # These are just example values; real inference would optimize these
    sample_alpha = 0.1
    sample_lambda_m = 1e-4  # 100 micrometers
    
    ll_yukawa = log_likelihood_yukawa(
        dataset.separation_m,
        dataset.force_n,
        cov_matrix,
        sample_alpha,
        sample_lambda_m,
        L_inv
    )
    logger.info(f"Yukawa log-likelihood (alpha={sample_alpha}, lambda={sample_lambda_m}m): {ll_yukawa:.4f}")
    
    # Compare the two
    delta_ll = ll_yukawa - ll_newtonian
    logger.info(f"Difference in log-likelihood (Yukawa - Newtonian): {delta_ll:.4f}")
    
    if delta_ll > 0:
        logger.info("Yukawa model provides a better fit for these sample parameters.")
    else:
        logger.info("Newtonian model provides a better fit for these sample parameters.")


if __name__ == "__main__":
    main()