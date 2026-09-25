"""
Likelihood functions for Bayesian inference of the Inverse Square Law.

This module implements log-likelihood functions for both Newtonian and Yukawa-modified
force models, utilizing the full covariance matrix constructed in T015-COV.
Numerical stability is ensured via Cholesky decomposition.
"""
import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import logging
from scipy.linalg import cholesky, cho_solve, LinAlgError

from models.physics import yukawa_force, newtonian_force
from config import get_logger

logger = get_logger(__name__)

# Cache for Cholesky decomposition to avoid recomputing if covariance is constant
_cholesky_cache: Optional[Tuple[np.ndarray, np.ndarray]] = None
_covariance_hash: Optional[int] = None

def load_covariance_matrix(path: Path) -> np.ndarray:
    """
    Load the full covariance matrix from a .npy file.

    Args:
        path: Path to the covariance matrix file (e.g., data/processed/covariance_matrix.npy)

    Returns:
        numpy.ndarray: The covariance matrix.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid numpy array or is not square.
    """
    if not path.exists():
        raise FileNotFoundError(f"Covariance matrix file not found: {path}")
    
    cov = np.load(path)
    if not isinstance(cov, np.ndarray):
        raise ValueError(f"Loaded file is not a numpy array: {path}")
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError(f"Covariance matrix must be square. Shape: {cov.shape}")
    
    logger.info(f"Loaded covariance matrix of shape {cov.shape} from {path}")
    return cov

def compute_cholesky_decomposition(covariance: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Cholesky decomposition of the covariance matrix for numerical stability.
    This is used to efficiently compute the Mahalanobis distance and log-determinant.

    Args:
        covariance: The full covariance matrix (N x N).

    Returns:
        Tuple containing:
            - L: Lower triangular Cholesky factor (covariance = L @ L.T)
            - L_inv: Inverse of the lower triangular factor (used in cho_solve)

    Raises:
        LinAlgError: If the covariance matrix is not positive-definite.
    """
    try:
        L = cholesky(covariance, lower=True)
        # We don't compute the full inverse, we keep L to use cho_solve later
        # cho_solve expects (L, lower)
        return L, None
    except LinAlgError as e:
        logger.error(f"Covariance matrix is not positive-definite. Cholesky decomposition failed: {e}")
        raise

def log_likelihood_newtonian(
    separation: np.ndarray,
    force: np.ndarray,
    cov_cholesky: Tuple[np.ndarray, Optional[np.ndarray]]
) -> float:
    """
    Compute the log-likelihood for the Newtonian force model (alpha = 0).

    The model predicts force based on separation assuming pure inverse-square law.
    Likelihood is computed as:
    log L = -0.5 * (r^T @ Sigma^-1 @ r) - 0.5 * log|Sigma| - (N/2) * log(2*pi)

    Args:
        separation: Array of separation distances (meters).
        force: Array of measured force values (Newtons).
        cov_cholesky: Tuple (L, _) where L is the Cholesky factor of the covariance matrix.

    Returns:
        float: Log-likelihood value.
    """
    L, _ = cov_cholesky
    N = len(force)
    
    # Model prediction
    model_force = newtonian_force(separation)
    
    # Residuals
    residuals = force - model_force
    
    # Solve for Sigma^-1 @ residuals using Cholesky factor
    # cho_solve((L, True), residuals) returns Sigma^-1 @ residuals
    # We need r^T @ Sigma^-1 @ r = residuals.T @ cho_solve(...)
    try:
        # Solve L @ y = residuals => y = L^-1 @ residuals
        # Then solve L.T @ z = y => z = (L^-1 @ residuals) / L.T = Sigma^-1 @ residuals? 
        # Actually cho_solve((L, lower=True), b) computes inv(L @ L.T) @ b
        inv_cov_residuals = cho_solve((L, True), residuals)
        mahalanobis_sq = np.dot(residuals, inv_cov_residuals)
        
        # Log determinant: log|Sigma| = 2 * sum(log(diag(L)))
        log_det = 2.0 * np.sum(np.log(np.diag(L)))
        
        log_likelihood = -0.5 * mahalanobis_sq - 0.5 * log_det - 0.5 * N * np.log(2 * np.pi)
        
        return float(log_likelihood)
    except LinAlgError as e:
        logger.error(f"Cholesky solve failed during likelihood computation: {e}")
        return -np.inf

def log_likelihood_yukawa(
    separation: np.ndarray,
    force: np.ndarray,
    alpha: float,
    lambda_val: float,
    cov_cholesky: Tuple[np.ndarray, Optional[np.ndarray]]
) -> float:
    """
    Compute the log-likelihood for the Yukawa-modified force model.

    The model includes a Yukawa term: F = F_Newtonian * (1 + alpha * exp(-r/lambda))

    Args:
        separation: Array of separation distances (meters).
        force: Array of measured force values (Newtons).
        alpha: Strength of the Yukawa interaction (dimensionless).
        lambda_val: Range of the Yukawa interaction (meters).
        cov_cholesky: Tuple (L, _) where L is the Cholesky factor of the covariance matrix.

    Returns:
        float: Log-likelihood value.
    """
    L, _ = cov_cholesky
    N = len(force)
    
    # Model prediction
    model_force = yukawa_force(separation, alpha, lambda_val)
    
    # Residuals
    residuals = force - model_force
    
    try:
        inv_cov_residuals = cho_solve((L, True), residuals)
        mahalanobis_sq = np.dot(residuals, inv_cov_residuals)
        log_det = 2.0 * np.sum(np.log(np.diag(L)))
        
        log_likelihood = -0.5 * mahalanobis_sq - 0.5 * log_det - 0.5 * N * np.log(2 * np.pi)
        
        return float(log_likelihood)
    except LinAlgError as e:
        logger.error(f"Cholesky solve failed during likelihood computation: {e}")
        return -np.inf

def main():
    """
    Main entry point for testing the likelihood functions.
    This function loads the covariance matrix and a sample dataset (if available)
    to demonstrate the computation of log-likelihoods.
    """
    logger.info("Starting likelihood module self-test.")
    
    # Define paths relative to project root
    # Assuming this script is run from the project root or code/ directory
    base_path = Path(__file__).resolve().parent.parent
    cov_path = base_path / "data" / "processed" / "covariance_matrix.npy"
    
    if not cov_path.exists():
        logger.warning(f"Covariance matrix not found at {cov_path}. Skipping test execution.")
        logger.info("To run this test, ensure T015-COV has been completed and the file exists.")
        return

    try:
        cov_matrix = load_covariance_matrix(cov_path)
        L, _ = compute_cholesky_decomposition(cov_matrix)
        cov_cholesky = (L, None)
        
        # Generate dummy data for demonstration if real data is not available
        # In a real run, this would be loaded from data/processed/harmonized_dataset.csv
        N = cov_matrix.shape[0]
        separation = np.linspace(1e-4, 1e-3, N) # 100um to 1000um
        force = newtonian_force(separation) + 1e-15 * np.random.randn(N) # Add small noise
        
        # Test Newtonian Likelihood
        ll_newton = log_likelihood_newtonian(separation, force, cov_cholesky)
        logger.info(f"Newtonian Log-Likelihood: {ll_newton}")
        
        # Test Yukawa Likelihood (with alpha=0, should be similar to Newtonian)
        ll_yukawa_null = log_likelihood_yukawa(separation, force, alpha=0.0, lambda_val=1e-3, cov_cholesky=cov_cholesky)
        logger.info(f"Yukawa Log-Likelihood (alpha=0): {ll_yukawa_null}")
        
        # Test Yukawa Likelihood (with non-zero alpha)
        ll_yukawa = log_likelihood_yukawa(separation, force, alpha=1.0, lambda_val=1e-4, cov_cholesky=cov_cholesky)
        logger.info(f"Yukawa Log-Likelihood (alpha=1.0): {ll_yukawa}")
        
        logger.info("Likelihood functions executed successfully.")
        
    except Exception as e:
        logger.error(f"Error during likelihood computation: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()