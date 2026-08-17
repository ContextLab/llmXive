"""
Likelihood functions for Yukawa and Newtonian force models.

Implements log-likelihood calculations using the covariance matrix
from T015 (full or banded) with Cholesky decomposition for numerical stability.
"""
import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import logging
from scipy.linalg import cholesky, cho_solve, LinAlgError

from models.physics import yukawa_force, newtonian_force
from config import get_logger

logger = get_logger(__name__)

def load_covariance_matrix(cov_path: Path) -> np.ndarray:
    """
    Load the covariance matrix from disk.
    
    Args:
        cov_path: Path to the .npy file containing the covariance matrix.
        
    Returns:
        The covariance matrix as a numpy array.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid numpy array or is not square.
    """
    if not cov_path.exists():
        raise FileNotFoundError(f"Covariance matrix file not found: {cov_path}")
    
    try:
        cov_matrix = np.load(cov_path)
    except Exception as e:
        raise ValueError(f"Failed to load covariance matrix from {cov_path}: {e}")
    
    if cov_matrix.ndim != 2 or cov_matrix.shape[0] != cov_matrix.shape[1]:
        raise ValueError(f"Covariance matrix must be square. Got shape: {cov_matrix.shape}")
    
    logger.info(f"Loaded covariance matrix with shape {cov_matrix.shape} from {cov_path}")
    return cov_matrix

def compute_cholesky_decomposition(cov_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Cholesky decomposition of the covariance matrix.
    
    Args:
        cov_matrix: The covariance matrix (must be positive definite).
        
    Returns:
        A tuple (L, L_inv) where L is the lower triangular Cholesky factor
        and L_inv is its inverse.
        
    Raises:
        LinAlgError: If the matrix is not positive definite.
    """
    try:
        L = cholesky(cov_matrix, lower=True)
        # Solve L * X = I to get L_inv
        L_inv = cho_solve((L, True), np.eye(L.shape[0]))
        logger.debug("Cholesky decomposition computed successfully.")
        return L, L_inv
    except LinAlgError as e:
        logger.error(f"Cholesky decomposition failed: {e}")
        raise

def log_likelihood_newtonian(
    r: np.ndarray,
    F_obs: np.ndarray,
    L: np.ndarray,
    L_inv: np.ndarray
) -> float:
    """
    Compute the log-likelihood for the Newtonian force model.
    
    The model assumes F = newtonian_force(r).
    Likelihood is proportional to exp(-0.5 * chi^2).
    
    Args:
        r: Array of separation distances (meters).
        F_obs: Array of observed force values (Newtons).
        L: Lower triangular Cholesky factor of the covariance matrix.
        L_inv: Inverse of the lower triangular Cholesky factor.
        
    Returns:
        The log-likelihood value.
    """
    F_model = newtonian_force(r)
    residuals = F_obs - F_model
    
    # Solve L * y = residuals for y (i.e., y = L^{-1} * residuals)
    # Then chi^2 = y^T * y
    try:
        y = cho_solve((L, True), residuals)
        chi_sq = np.dot(y, y)
    except Exception as e:
        logger.error(f"Error solving linear system for Newtonian likelihood: {e}")
        return -np.inf
    
    log_det = 2 * np.sum(np.log(np.diag(L)))
    n = len(residuals)
    log_likelihood = -0.5 * (chi_sq + n * np.log(2 * np.pi) + log_det)
    
    return log_likelihood

def log_likelihood_yukawa(
    r: np.ndarray,
    F_obs: np.ndarray,
    alpha: float,
    lambda_val: float,
    L: np.ndarray,
    L_inv: np.ndarray
) -> float:
    """
    Compute the log-likelihood for the Yukawa-modified force model.
    
    The model assumes F = yukawa_force(r, alpha, lambda).
    Likelihood is proportional to exp(-0.5 * chi^2).
    
    Args:
        r: Array of separation distances (meters).
        F_obs: Array of observed force values (Newtons).
        alpha: Strength parameter of the Yukawa interaction (dimensionless).
        lambda_val: Range parameter of the Yukawa interaction (meters).
        L: Lower triangular Cholesky factor of the covariance matrix.
        L_inv: Inverse of the lower triangular Cholesky factor.
        
    Returns:
        The log-likelihood value.
    """
    if lambda_val <= 0:
        return -np.inf
        
    F_model = yukawa_force(r, alpha, lambda_val)
    residuals = F_obs - F_model
    
    # Solve L * y = residuals for y (i.e., y = L^{-1} * residuals)
    # Then chi^2 = y^T * y
    try:
        y = cho_solve((L, True), residuals)
        chi_sq = np.dot(y, y)
    except Exception as e:
        logger.error(f"Error solving linear system for Yukawa likelihood: {e}")
        return -np.inf
    
    log_det = 2 * np.sum(np.log(np.diag(L)))
    n = len(residuals)
    log_likelihood = -0.5 * (chi_sq + n * np.log(2 * np.pi) + log_det)
    
    return log_likelihood

class YukawaLikelihood:
    """
    A callable class representing the Yukawa log-likelihood function.
    
    This class pre-computes the Cholesky decomposition of the covariance matrix
    to speed up repeated likelihood evaluations during MCMC or nested sampling.
    """
    def __init__(self, r: np.ndarray, F_obs: np.ndarray, cov_matrix: np.ndarray):
        """
        Initialize the Yukawa likelihood.
        
        Args:
            r: Array of separation distances (meters).
            F_obs: Array of observed force values (Newtons).
            cov_matrix: The covariance matrix.
        """
        self.r = np.asarray(r)
        self.F_obs = np.asarray(F_obs)
        self.L, self.L_inv = compute_cholesky_decomposition(cov_matrix)
        logger.info("YukawaLikelihood initialized with pre-computed Cholesky decomposition.")
    
    def __call__(self, params: Tuple[float, float]) -> float:
        """
        Evaluate the log-likelihood for given parameters.
        
        Args:
            params: A tuple (alpha, lambda_val).
            
        Returns:
            The log-likelihood value.
        """
        alpha, lambda_val = params
        return log_likelihood_yukawa(self.r, self.F_obs, alpha, lambda_val, self.L, self.L_inv)

class NewtonianLikelihood:
    """
    A callable class representing the Newtonian log-likelihood function.
    
    This class pre-computes the Cholesky decomposition of the covariance matrix
    to speed up repeated likelihood evaluations.
    """
    def __init__(self, r: np.ndarray, F_obs: np.ndarray, cov_matrix: np.ndarray):
        """
        Initialize the Newtonian likelihood.
        
        Args:
            r: Array of separation distances (meters).
            F_obs: Array of observed force values (Newtons).
            cov_matrix: The covariance matrix.
        """
        self.r = np.asarray(r)
        self.F_obs = np.asarray(F_obs)
        self.L, self.L_inv = compute_cholesky_decomposition(cov_matrix)
        logger.info("NewtonianLikelihood initialized with pre-computed Cholesky decomposition.")
    
    def __call__(self, params: Tuple[()]) -> float:
        """
        Evaluate the log-likelihood. No parameters for Newtonian model.
        
        Args:
            params: Empty tuple (ignored).
            
        Returns:
            The log-likelihood value.
        """
        return log_likelihood_newtonian(self.r, self.F_obs, self.L, self.L_inv)

def main():
    """
    Main entry point for testing the likelihood functions.
    
    This function loads the covariance matrix and harmonized data,
    then demonstrates the likelihood calculations.
    """
    from config import ProjectConfig
    from data.loaders import HarmonizedDataset
    
    config = ProjectConfig()
    cov_path = config.data_dir / "processed" / "covariance_matrix.npy"
    
    if not cov_path.exists():
        logger.error(f"Covariance matrix not found at {cov_path}. Please run harmonization first.")
        return
    
    try:
        cov_matrix = load_covariance_matrix(cov_path)
        L, L_inv = compute_cholesky_decomposition(cov_matrix)
        logger.info("Successfully loaded and decomposed covariance matrix.")
        
        # Load harmonized data
        data_path = config.data_dir / "processed" / "harmonized_data.csv"
        if not data_path.exists():
            logger.error(f"Harmonized data not found at {data_path}.")
            return
        
        df = HarmonizedDataset.load_from_csv(data_path)
        r = df['separation_m']
        F_obs = df['force_N']
        
        # Test Newtonian likelihood
        ll_newton = log_likelihood_newtonian(r, F_obs, L, L_inv)
        logger.info(f"Newtonian log-likelihood: {ll_newton}")
        
        # Test Yukawa likelihood with sample parameters
        alpha_test = 1.0
        lambda_test = 1e-4  # 0.1 mm
        ll_yukawa = log_likelihood_yukawa(r, F_obs, alpha_test, lambda_test, L, L_inv)
        logger.info(f"Yukawa log-likelihood (alpha={alpha_test}, lambda={lambda_test}): {ll_yukawa}")
        
        # Test class-based likelihood
        yukawa_lik = YukawaLikelihood(r, F_obs, cov_matrix)
        ll_class = yukawa_lik((alpha_test, lambda_test))
        logger.info(f"Yukawa log-likelihood (class-based): {ll_class}")
        
    except Exception as e:
        logger.error(f"Error in main likelihood test: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()