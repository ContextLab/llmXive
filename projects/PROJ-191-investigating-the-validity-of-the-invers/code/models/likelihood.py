"""
Likelihood functions for Bayesian inference.

Implements log-likelihood calculations for Newtonian and Yukawa-modified
gravitational force models using Cholesky decomposition for numerical stability.
Handles both full covariance matrices and block-diagonal approximations.
"""
import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import logging
from scipy.linalg import cholesky, cho_solve, LinAlgError
from models.physics import yukawa_force, newtonian_force
from config import get_logger

logger = get_logger(__name__)


def load_covariance_matrix(path: Path) -> np.ndarray:
    """
    Load the covariance matrix from a .npy file.
    
    Args:
        path: Path to the covariance matrix file.
        
    Returns:
        The covariance matrix as a numpy array.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the matrix is not 2D.
    """
    if not path.exists():
        raise FileNotFoundError(f"Covariance matrix file not found: {path}")
    
    cov_matrix = np.load(path)
    
    if cov_matrix.ndim != 2:
        raise ValueError(f"Covariance matrix must be 2D, got {cov_matrix.ndim}D")
    
    logger.info(f"Loaded covariance matrix of shape {cov_matrix.shape} from {path}")
    return cov_matrix


def compute_cholesky_decomposition(cov_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Cholesky decomposition of the covariance matrix for numerical stability.
    
    The Cholesky decomposition L satisfies: cov_matrix = L @ L.T
    This allows efficient computation of:
    - log_det = 2 * sum(log(diag(L)))
    - quadratic_form = x.T @ cov_matrix^-1 @ x = ||L^-1 @ x||^2
    
    Args:
        cov_matrix: The covariance matrix (must be positive-definite).
        
    Returns:
        Tuple of (L, L_inv) where L is lower triangular Cholesky factor
        and L_inv is its inverse.
        
    Raises:
        LinAlgError: If the matrix is not positive-definite.
    """
    try:
        # Compute Cholesky decomposition
        L = cholesky(cov_matrix, lower=True)
        
        # Compute inverse of L for efficient quadratic form calculation
        L_inv = np.linalg.inv(L)
        
        logger.debug(f"Cholesky decomposition successful. L shape: {L.shape}")
        return L, L_inv
        
    except LinAlgError as e:
        logger.error(f"Cholesky decomposition failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Cholesky decomposition: {e}")
        raise


def log_likelihood_newtonian(
    separation: np.ndarray,
    force_obs: np.ndarray,
    cov_matrix: np.ndarray,
    L_inv: Optional[np.ndarray] = None
) -> float:
    """
    Compute the log-likelihood for the Newtonian force model.
    
    The likelihood is based on the multivariate normal distribution:
    log L = -0.5 * (N * log(2π) + log|Σ| + (y - f)^T Σ^-1 (y - f))
    
    where:
    - N is the number of data points
    - Σ is the covariance matrix
    - y is the observed force
    - f is the predicted Newtonian force
    
    Args:
        separation: Array of separation distances (in meters).
        force_obs: Array of observed forces (in Newtons).
        cov_matrix: The covariance matrix.
        L_inv: Pre-computed inverse of Cholesky factor (optional).
        
    Returns:
        The log-likelihood value.
    """
    N = len(separation)
    
    # Compute predicted Newtonian force
    force_pred = newtonian_force(separation)
    
    # Compute residuals
    residuals = force_obs - force_pred
    
    # Compute log determinant of covariance matrix
    if L_inv is None:
        L, _ = compute_cholesky_decomposition(cov_matrix)
        log_det = 2 * np.sum(np.log(np.diag(L)))
    else:
        # If L_inv is provided, we need to get L from it or recompute
        # For efficiency, we'll recompute L if not provided
        L, _ = compute_cholesky_decomposition(cov_matrix)
        log_det = 2 * np.sum(np.log(np.diag(L)))
    
    # Compute quadratic form: residuals^T @ cov^-1 @ residuals
    # Using Cholesky: cov^-1 = L^-T @ L^-1
    # So: residuals^T @ cov^-1 @ residuals = ||L^-1 @ residuals||^2
    if L_inv is None:
        L, L_inv = compute_cholesky_decomposition(cov_matrix)
    
    transformed_residuals = L_inv @ residuals
    quadratic_form = np.dot(transformed_residuals, transformed_residuals)
    
    # Compute log-likelihood
    log_likelihood = -0.5 * (
        N * np.log(2 * np.pi) + 
        log_det + 
        quadratic_form
    )
    
    return float(log_likelihood)


def log_likelihood_yukawa(
    separation: np.ndarray,
    force_obs: np.ndarray,
    cov_matrix: np.ndarray,
    alpha: float,
    lambda_m: float,
    L_inv: Optional[np.ndarray] = None
) -> float:
    """
    Compute the log-likelihood for the Yukawa-modified force model.
    
    The Yukawa potential modifies the Newtonian force with an exponential
    decay term: F = F_Newtonian * (1 + α * exp(-r/λ))
    
    Args:
        separation: Array of separation distances (in meters).
        force_obs: Array of observed forces (in Newtons).
        cov_matrix: The covariance matrix.
        alpha: Strength parameter of the Yukawa modification.
        lambda_m: Range parameter of the Yukawa modification (in meters).
        L_inv: Pre-computed inverse of Cholesky factor (optional).
        
    Returns:
        The log-likelihood value.
    """
    N = len(separation)
    
    # Compute predicted Yukawa force
    force_pred = yukawa_force(separation, alpha, lambda_m)
    
    # Compute residuals
    residuals = force_obs - force_pred
    
    # Compute log determinant of covariance matrix
    if L_inv is None:
        L, _ = compute_cholesky_decomposition(cov_matrix)
        log_det = 2 * np.sum(np.log(np.diag(L)))
    else:
        L, _ = compute_cholesky_decomposition(cov_matrix)
        log_det = 2 * np.sum(np.log(np.diag(L)))
    
    # Compute quadratic form
    if L_inv is None:
        L, L_inv = compute_cholesky_decomposition(cov_matrix)
    
    transformed_residuals = L_inv @ residuals
    quadratic_form = np.dot(transformed_residuals, transformed_residuals)
    
    # Compute log-likelihood
    log_likelihood = -0.5 * (
        N * np.log(2 * np.pi) + 
        log_det + 
        quadratic_form
    )
    
    return float(log_likelihood)


class YukawaLikelihood:
    """
    Class-based interface for Yukawa likelihood computation.
    
    Pre-computes Cholesky decomposition for efficiency when evaluating
    likelihood multiple times with the same covariance matrix.
    """
    
    def __init__(self, separation: np.ndarray, force_obs: np.ndarray, cov_matrix: np.ndarray):
        """
        Initialize the likelihood calculator.
        
        Args:
            separation: Array of separation distances (in meters).
            force_obs: Array of observed forces (in Newtons).
            cov_matrix: The covariance matrix.
        """
        self.separation = np.asarray(separation)
        self.force_obs = np.asarray(force_obs)
        self.cov_matrix = np.asarray(cov_matrix)
        
        # Pre-compute Cholesky decomposition
        self.L, self.L_inv = compute_cholesky_decomposition(self.cov_matrix)
        self.N = len(self.separation)
        
        logger.info(f"Initialized YukawaLikelihood with {self.N} data points")
    
    def __call__(self, alpha: float, lambda_m: float) -> float:
        """
        Compute the log-likelihood for given parameters.
        
        Args:
            alpha: Strength parameter of the Yukawa modification.
            lambda_m: Range parameter of the Yukawa modification (in meters).
            
        Returns:
            The log-likelihood value.
        """
        return log_likelihood_yukawa(
            self.separation,
            self.force_obs,
            self.cov_matrix,
            alpha,
            lambda_m,
            L_inv=self.L_inv
        )


class NewtonianLikelihood:
    """
    Class-based interface for Newtonian likelihood computation.
    
    Pre-computes Cholesky decomposition for efficiency when evaluating
    likelihood multiple times with the same covariance matrix.
    """
    
    def __init__(self, separation: np.ndarray, force_obs: np.ndarray, cov_matrix: np.ndarray):
        """
        Initialize the likelihood calculator.
        
        Args:
            separation: Array of separation distances (in meters).
            force_obs: Array of observed forces (in Newtons).
            cov_matrix: The covariance matrix.
        """
        self.separation = np.asarray(separation)
        self.force_obs = np.asarray(force_obs)
        self.cov_matrix = np.asarray(cov_matrix)
        
        # Pre-compute Cholesky decomposition
        self.L, self.L_inv = compute_cholesky_decomposition(self.cov_matrix)
        self.N = len(self.separation)
        
        logger.info(f"Initialized NewtonianLikelihood with {self.N} data points")
    
    def __call__(self) -> float:
        """
        Compute the log-likelihood for the Newtonian model.
        
        Returns:
            The log-likelihood value.
        """
        return log_likelihood_newtonian(
            self.separation,
            self.force_obs,
            self.cov_matrix,
            L_inv=self.L_inv
        )


def main():
    """
    Main function to demonstrate likelihood computation.
    
    This function loads the harmonized data and covariance matrix,
    then computes likelihood values for both Newtonian and Yukawa models.
    """
    from config import ProjectConfig
    from pathlib import Path
    
    config = ProjectConfig()
    
    # Define paths
    cov_path = config.data_processed_dir / "covariance_matrix.npy"
    data_path = config.data_processed_dir / "harmonized_data.csv"
    
    if not cov_path.exists():
        logger.error(f"Covariance matrix not found at {cov_path}")
        logger.info("Please run T015-COV to generate the covariance matrix first.")
        return
    
    if not data_path.exists():
        logger.error(f"Harmonized data not found at {data_path}")
        logger.info("Please run T014 to generate the harmonized data first.")
        return
    
    # Load data
    import pandas as pd
    df = pd.read_csv(data_path)
    
    separation = df['separation_m'].values
    force_obs = df['force_N'].values
    
    # Load covariance matrix
    cov_matrix = load_covariance_matrix(cov_path)
    
    # Initialize likelihood calculators
    newtonian_ll = NewtonianLikelihood(separation, force_obs, cov_matrix)
    yukawa_ll = YukawaLikelihood(separation, force_obs, cov_matrix)
    
    # Compute likelihoods
    ll_newton = newtonian_ll()
    
    # Example Yukawa parameters (these would be optimized in inference)
    alpha_example = 0.1
    lambda_example = 1e-4  # 100 micrometers
    
    ll_yukawa = yukawa_ll(alpha_example, lambda_example)
    
    logger.info(f"Newtonian log-likelihood: {ll_newton:.4f}")
    logger.info(f"Yukawa log-likelihood (α={alpha_example}, λ={lambda_example}m): {ll_yukawa:.4f}")
    logger.info(f"Bayes factor (Yukawa vs Newtonian): {np.exp(ll_yukawa - ll_newton):.4f}")


if __name__ == "__main__":
    main()