"""
Likelihood functions for Yukawa and Newtonian models.

Implements log-likelihood using Cholesky decomposition for numerical stability.
Supports both full and banded covariance matrices.
"""
import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import logging
from scipy.linalg import cholesky, cho_solve, LinAlgError

from models.physics import yukawa_force, newtonian_force
from config import get_logger

logger = get_logger(__name__)


class YukawaLikelihood:
    """
    Yukawa-modified gravity likelihood class.
    
    Parameters:
        log_alpha: log10 of the strength parameter alpha
        log_lambda: log10 of the range parameter lambda (in meters)
    """
    
    def __init__(self, data: dict, cov_matrix: np.ndarray):
        """
        Initialize the likelihood with data and covariance.
        
        Args:
            data: Dictionary containing 'separation' and 'force' arrays.
            cov_matrix: Covariance matrix (full or banded).
        """
        self.separation = np.array(data['separation'])
        self.force = np.array(data['force'])
        self.cov_matrix = np.array(cov_matrix)
        self.n_points = len(self.separation)
        
        # Pre-compute Cholesky decomposition if matrix is positive definite
        self.cholesky_lower = None
        self.cholesky_inverted = False
        
        try:
            self.cholesky_lower = cholesky(self.cov_matrix, lower=True)
            self.cholesky_inverted = True
            logger.debug("Cholesky decomposition successful")
        except LinAlgError as e:
            logger.warning(f"Cholesky decomposition failed: {e}. "
                         "Likelihood evaluation may fail.")
            self.cholesky_lower = None
    
    def log_prob(self, params: np.ndarray) -> float:
        """
        Compute the log-probability (log-likelihood + log-prior).
        
        Args:
            params: Array of [log_alpha, log_lambda]
        
        Returns:
            Log-probability value (or -inf if invalid).
        """
        log_alpha, log_lambda = params
        
        # Prior: Uniform in log space within reasonable bounds
        # log_alpha: -5 to 15
        # log_lambda: -5 to -2 (meters)
        if log_alpha < -5 or log_alpha > 15:
            return -np.inf
        if log_lambda < -5 or log_lambda > -2:
            return -np.inf
        
        # Convert back to linear space
        alpha = 10 ** log_alpha
        lambda_val = 10 ** log_lambda
        
        # Compute model prediction
        try:
            model_force = yukawa_force(self.separation, alpha, lambda_val)
        except Exception as e:
            logger.debug(f"Model computation failed: {e}")
            return -np.inf
        
        # Check for NaN or Inf in model
        if np.any(~np.isfinite(model_force)):
            return -np.inf
        
        # Compute residuals
        residuals = self.force - model_force
        
        # Compute log-likelihood using Cholesky decomposition
        # log L = -0.5 * (N*log(2*pi) + log|C| + r^T C^-1 r)
        if self.cholesky_lower is None:
            # Fallback to direct inversion if Cholesky failed
            try:
                cov_inv = np.linalg.inv(self.cov_matrix)
                log_det = np.log(np.linalg.det(self.cov_matrix))
                chi_sq = residuals @ cov_inv @ residuals
            except Exception as e:
                logger.debug(f"Covariance inversion failed: {e}")
                return -np.inf
        else:
            # Use Cholesky decomposition
            # Solve L y = r for y
            try:
                y = cho_solve((self.cholesky_lower, True), residuals)
                chi_sq = residuals @ y
                # log|C| = 2 * sum(log(diag(L)))
                log_det = 2 * np.sum(np.log(np.diag(self.cholesky_lower)))
            except Exception as e:
                logger.debug(f"Cholesky solve failed: {e}")
                return -np.inf
        
        log_likelihood = -0.5 * (
            self.n_points * np.log(2 * np.pi) + 
            log_det + 
            chi_sq
        )
        
        return log_likelihood


class NewtonianLikelihood:
    """
    Pure Newtonian gravity likelihood class (alpha = 0).
    """
    
    def __init__(self, data: dict, cov_matrix: np.ndarray):
        """
        Initialize the likelihood with data and covariance.
        """
        self.separation = np.array(data['separation'])
        self.force = np.array(data['force'])
        self.cov_matrix = np.array(cov_matrix)
        self.n_points = len(self.separation)
        
        # Pre-compute Cholesky decomposition
        self.cholesky_lower = None
        try:
            self.cholesky_lower = cholesky(self.cov_matrix, lower=True)
        except LinAlgError:
            logger.warning("Cholesky decomposition failed for Newtonian likelihood")
            self.cholesky_lower = None
    
    def log_prob(self, params: np.ndarray) -> float:
        """
        Compute log-probability for Newtonian model.
        
        Args:
            params: Unused (model has no free parameters beyond known constants)
        
        Returns:
            Log-likelihood value.
        """
        # Compute model prediction (pure Newtonian)
        try:
            model_force = newtonian_force(self.separation)
        except Exception as e:
            logger.debug(f"Newtonian model computation failed: {e}")
            return -np.inf
        
        if np.any(~np.isfinite(model_force)):
            return -np.inf
        
        residuals = self.force - model_force
        
        # Compute log-likelihood
        if self.cholesky_lower is None:
            try:
                cov_inv = np.linalg.inv(self.cov_matrix)
                log_det = np.log(np.linalg.det(self.cov_matrix))
                chi_sq = residuals @ cov_inv @ residuals
            except Exception:
                return -np.inf
        else:
            try:
                y = cho_solve((self.cholesky_lower, True), residuals)
                chi_sq = residuals @ y
                log_det = 2 * np.sum(np.log(np.diag(self.cholesky_lower)))
            except Exception:
                return -np.inf
        
        log_likelihood = -0.5 * (
            self.n_points * np.log(2 * np.pi) + 
            log_det + 
            chi_sq
        )
        
        return log_likelihood


def load_covariance_matrix(path: Path) -> np.ndarray:
    """Load covariance matrix from file."""
    if not path.exists():
        raise FileNotFoundError(f"Covariance matrix not found at {path}")
    return np.load(path)


def compute_cholesky_decomposition(cov_matrix: np.ndarray) -> Optional[np.ndarray]:
    """Compute Cholesky decomposition of covariance matrix."""
    try:
        return cholesky(cov_matrix, lower=True)
    except LinAlgError:
        logger.error("Cholesky decomposition failed: matrix is not positive definite")
        return None


def log_likelihood_yukawa(
    params: np.ndarray, 
    separation: np.ndarray, 
    force: np.ndarray, 
    cov_matrix: np.ndarray
) -> float:
    """
    Compute log-likelihood for Yukawa model.
    
    Args:
        params: [log_alpha, log_lambda]
        separation: Separation distances
        force: Measured forces
        cov_matrix: Covariance matrix
    
    Returns:
        Log-likelihood value.
    """
    likelihood = YukawaLikelihood({"separation": separation, "force": force}, cov_matrix)
    return likelihood.log_prob(params)


def log_likelihood_newtonian(
    separation: np.ndarray, 
    force: np.ndarray, 
    cov_matrix: np.ndarray
) -> float:
    """
    Compute log-likelihood for Newtonian model.
    
    Returns:
        Log-likelihood value.
    """
    likelihood = NewtonianLikelihood({"separation": separation, "force": force}, cov_matrix)
    return likelihood.log_prob(np.array([]))


def main():
    """Test likelihood functions."""
    logger.info("Testing likelihood functions")
    
    # Create dummy data
    separation = np.logspace(-5, -3, 50)
    force = newtonian_force(separation) * (1 + 0.01 * np.random.randn(len(separation)))
    
    # Create dummy covariance matrix
    cov_matrix = np.eye(len(separation)) * 1e-20
    
    # Test Yukawa likelihood
    params = np.array([0.0, -4.0])  # alpha=1, lambda=100um
    ll_yukawa = log_likelihood_yukawa(params, separation, force, cov_matrix)
    logger.info(f"Yukawa log-likelihood: {ll_yukawa}")
    
    # Test Newtonian likelihood
    ll_newton = log_likelihood_newtonian(separation, force, cov_matrix)
    logger.info(f"Newtonian log-likelihood: {ll_newton}")
    
    logger.info("Likelihood tests completed")


if __name__ == "__main__":
    main()
