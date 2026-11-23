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
    Load the full covariance matrix from a .npy file.
    
    Args:
        path: Path to the covariance matrix file (.npy).
        
    Returns:
        The covariance matrix as a numpy array.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid numpy array or is not square.
    """
    if not path.exists():
        raise FileNotFoundError(f"Covariance matrix file not found: {path}")
        
    cov_matrix = np.load(path)
    
    if cov_matrix.ndim != 2 or cov_matrix.shape[0] != cov_matrix.shape[1]:
        raise ValueError(f"Covariance matrix must be a 2D square array. Got shape: {cov_matrix.shape}")
        
    logger.info(f"Loaded covariance matrix of shape {cov_matrix.shape} from {path}")
    return cov_matrix

def compute_cholesky_decomposition(cov_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Cholesky decomposition of the covariance matrix for numerical stability.
    
    The decomposition returns L such that cov_matrix = L @ L.T.
    We also compute the log-determinant as 2 * sum(log(diag(L))).
    
    Args:
        cov_matrix: The full covariance matrix.
        
    Returns:
        Tuple of (L, log_det) where:
            L: Lower triangular Cholesky factor.
            log_det: Log-determinant of the covariance matrix.
            
    Raises:
        LinAlgError: If the matrix is not positive definite.
    """
    try:
        L = cholesky(cov_matrix, lower=True, check_finite=False)
        log_det = 2.0 * np.sum(np.log(np.diag(L)))
        logger.debug("Cholesky decomposition successful")
        return L, log_det
    except LinAlgError as e:
        logger.error(f"Cholesky decomposition failed: {e}")
        logger.error("Covariance matrix might not be positive definite.")
        raise

def log_likelihood_newtonian(
    separation_m: np.ndarray,
    force_n: np.ndarray,
    L: np.ndarray,
    log_det: float
) -> float:
    """
    Compute the log-likelihood for the Newtonian force model using Cholesky decomposition.
    
    Likelihood function:
        ln L = -0.5 * (N * ln(2*pi) + ln|C| + (F - F_model)^T * C^-1 * (F - F_model))
    
    Using Cholesky:
        C^-1 = (L * L^T)^-1 = L^-T * L^-1
        (F - F_model)^T * C^-1 * (F - F_model) = || L^-1 * (F - F_model) ||^2
    
    Args:
        separation_m: Separation distances in meters (1D array).
        force_n: Measured force values in Newtons (1D array).
        L: Lower triangular Cholesky factor of the covariance matrix.
        log_det: Log-determinant of the covariance matrix.
        
    Returns:
        The log-likelihood value.
    """
    # Calculate Newtonian force model (alpha=0, so just standard gravity/Newtonian)
    # Assuming the physics model handles the specific force law. 
    # For pure Newtonian in this context, it's often the baseline without Yukawa modification.
    # We assume the model function returns the predicted force vector.
    model_force = newtonian_force(separation_m)
    
    residuals = force_n - model_force
    
    # Solve L @ x = residuals for x, then compute ||x||^2
    # This is equivalent to residuals^T * inv(C) * residuals
    try:
        # cho_solve expects (L, lower) tuple
        residuals_transformed = cho_solve((L, True), residuals)
        chi_sq = np.dot(residuals, residuals_transformed)
    except LinAlgError:
        logger.error("cho_solve failed during likelihood computation.")
        return -np.inf
        
    N = len(force_n)
    log_likelihood = -0.5 * (N * np.log(2 * np.pi) + log_det + chi_sq)
    
    return float(log_likelihood)

def log_likelihood_yukawa(
    separation_m: np.ndarray,
    force_n: np.ndarray,
    L: np.ndarray,
    log_det: float,
    alpha: float,
    lambda_m: float
) -> float:
    """
    Compute the log-likelihood for the Yukawa-modified force model using Cholesky decomposition.
    
    Likelihood function:
        ln L = -0.5 * (N * ln(2*pi) + ln|C| + (F - F_model)^T * C^-1 * (F - F_model))
    
    Using Cholesky:
        C^-1 = (L * L^T)^-1 = L^-T * L^-1
        (F - F_model)^T * C^-1 * (F - F_model) = || L^-1 * (F - F_model) ||^2
    
    Args:
        separation_m: Separation distances in meters (1D array).
        force_n: Measured force values in Newtons (1D array).
        L: Lower triangular Cholesky factor of the covariance matrix.
        log_det: Log-determinant of the covariance matrix.
        alpha: Yukawa strength parameter (dimensionless).
        lambda_m: Yukawa range parameter in meters.
        
    Returns:
        The log-likelihood value.
    """
    # Calculate Yukawa-modified force model
    model_force = yukawa_force(separation_m, alpha=alpha, lambda_m=lambda_m)
    
    residuals = force_n - model_force
    
    # Solve L @ x = residuals for x, then compute ||x||^2
    try:
        residuals_transformed = cho_solve((L, True), residuals)
        chi_sq = np.dot(residuals, residuals_transformed)
    except LinAlgError:
        logger.error("cho_solve failed during Yukawa likelihood computation.")
        return -np.inf
        
    N = len(force_n)
    log_likelihood = -0.5 * (N * np.log(2 * np.pi) + log_det + chi_sq)
    
    return float(log_likelihood)

def main():
    """
    Main entry point for testing the likelihood functions.
    This script loads the harmonized data and covariance matrix,
    computes the Cholesky decomposition, and evaluates the log-likelihood
    for both Newtonian and Yukawa models.
    """
    config = get_logger(__name__)
    config.info("Starting likelihood module test.")
    
    # Paths based on project structure
    # Assuming T015 outputs are in data/processed/
    cov_path = Path("data/processed/covariance_matrix_diagonal.npy")
    # Fallback to banded if diagonal doesn't exist (based on T015-Z-RESOLVE-COV logic)
    if not cov_path.exists():
        cov_path = Path("data/processed/covariance_matrix_banded.npy")
        
    data_path = Path("data/processed/harmonized_data.json") # Assuming output of harmonize.py
    
    if not cov_path.exists():
        logger.error(f"Covariance matrix not found at {cov_path}. Please run T015 first.")
        return
        
    if not data_path.exists():
        logger.error(f"Harmonized data not found at {data_path}. Please run T014 first.")
        return

    # Load data
    try:
        import json
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        separation_m = np.array(data['separation_m'])
        force_n = np.array(data['force_n'])
        
        if len(separation_m) == 0 or len(force_n) == 0:
            logger.error("Data arrays are empty.")
            return
            
        logger.info(f"Loaded data: {len(separation_m)} points")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    # Load Covariance
    try:
        cov_matrix = load_covariance_matrix(cov_path)
    except Exception as e:
        logger.error(f"Failed to load covariance: {e}")
        return

    # Compute Cholesky
    try:
        L, log_det = compute_cholesky_decomposition(cov_matrix)
        logger.info(f"Cholesky decomposition complete. Log-det: {log_det}")
    except LinAlgError as e:
        logger.error(f"Covariance matrix is not positive definite: {e}")
        return

    # Evaluate Newtonian
    ll_newton = log_likelihood_newtonian(separation_m, force_n, L, log_det)
    logger.info(f"Newtonian Log-Likelihood: {ll_newton}")

    # Evaluate Yukawa (with example parameters)
    # These are just for demonstration; real inference will vary them.
    alpha_test = 0.0
    lambda_test = 1e-4 # 0.1 mm
    ll_yukawa = log_likelihood_yukawa(separation_m, force_n, L, log_det, alpha_test, lambda_test)
    logger.info(f"Yukawa Log-Likelihood (alpha={alpha_test}, lambda={lambda_test}): {ll_yukawa}")

    logger.info("Likelihood evaluation complete.")

if __name__ == "__main__":
    main()