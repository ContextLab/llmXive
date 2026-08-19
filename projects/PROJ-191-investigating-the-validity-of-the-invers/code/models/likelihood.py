import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import logging
from scipy.linalg import cholesky, cho_solve, LinAlgError
from models.physics import yukawa_force, newtonian_force
from config import get_logger, ProjectConfig

logger = get_logger(__name__)

def load_covariance_matrix(filepath: Optional[Path] = None) -> np.ndarray:
    """
    Load the covariance matrix from disk.
    
    Args:
        filepath: Path to the .npy file. Defaults to ProjectConfig paths.
        
    Returns:
        np.ndarray: The loaded covariance matrix.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or invalid.
    """
    if filepath is None:
        config = ProjectConfig()
        filepath = config.data_processed_dir / "covariance_matrix.npy"
    
    if not filepath.exists():
        raise FileNotFoundError(f"Covariance matrix not found at {filepath}")
    
    try:
        cov_matrix = np.load(filepath)
    except Exception as e:
        raise ValueError(f"Failed to load covariance matrix: {e}")
    
    if cov_matrix.size == 0:
        raise ValueError("Covariance matrix is empty.")
        
    logger.info(f"Loaded covariance matrix of shape {cov_matrix.shape}")
    return cov_matrix

def compute_cholesky_decomposition(cov_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Cholesky decomposition of the covariance matrix for numerical stability.
    
    Args:
        cov_matrix: The covariance matrix (N x N).
        
    Returns:
        Tuple containing:
            - L: Lower triangular Cholesky factor.
            - L_inv: Inverse of the Cholesky factor (used for solving linear systems).
            
    Raises:
        LinAlgError: If the matrix is not positive-definite.
    """
    try:
        L = cholesky(cov_matrix, lower=True)
        # We need L_inv for solving L * x = b => x = L_inv * b
        # However, cho_solve expects the Cholesky factor directly.
        # To support both direct solve and pre-computed inverse usage, we return L.
        # The actual solve is done via cho_solve(L, b) for stability.
        return L, None 
    except LinAlgError as e:
        logger.error(f"Covariance matrix is not positive-definite. Shape: {cov_matrix.shape}")
        raise LinAlgError(f"Cholesky decomposition failed: {e}")

def log_likelihood_newtonian(
    separation: np.ndarray,
    force: np.ndarray,
    cov_matrix: np.ndarray,
    L: np.ndarray
) -> float:
    """
    Compute the log-likelihood for the Newtonian model.
    
    Model: F_pred = newtonian_force(separation)
    Likelihood: log P(data | model) = -0.5 * (residual^T * Cov^-1 * residual + log|Cov| + N*log(2*pi))
    
    Args:
        separation: Array of separation distances (m).
        force: Array of measured forces (N).
        cov_matrix: Full covariance matrix.
        L: Lower triangular Cholesky factor of cov_matrix.
        
    Returns:
        float: The log-likelihood value.
    """
    pred = newtonian_force(separation)
    residual = force - pred
    n = len(force)
    
    # Solve L * z = residual for z
    # Then residual^T * Cov^-1 * residual = z^T * z
    try:
        z = cho_solve((L, True), residual) # (L, True) implies L is lower triangular
    except LinAlgError:
        logger.error("Cholesky solve failed during likelihood computation.")
        return -np.inf
        
    chi_sq = np.dot(residual, z)
    log_det_cov = 2.0 * np.sum(np.log(np.diag(L)))
    
    log_likelihood = -0.5 * (chi_sq + log_det_cov + n * np.log(2.0 * np.pi))
    return log_likelihood

def log_likelihood_yukawa(
    separation: np.ndarray,
    force: np.ndarray,
    cov_matrix: np.ndarray,
    L: np.ndarray,
    alpha: float,
    lambda_val: float
) -> float:
    """
    Compute the log-likelihood for the Yukawa-modified model.
    
    Model: F_pred = yukawa_force(separation, alpha, lambda_val)
    Likelihood: log P(data | model) = -0.5 * (residual^T * Cov^-1 * residual + log|Cov| + N*log(2*pi))
    
    Args:
        separation: Array of separation distances (m).
        force: Array of measured forces (N).
        cov_matrix: Full covariance matrix.
        L: Lower triangular Cholesky factor of cov_matrix.
        alpha: Strength parameter for Yukawa potential.
        lambda_val: Range parameter for Yukawa potential (m).
        
    Returns:
        float: The log-likelihood value.
    """
    pred = yukawa_force(separation, alpha, lambda_val)
    residual = force - pred
    n = len(force)
    
    try:
        z = cho_solve((L, True), residual)
    except LinAlgError:
        logger.error("Cholesky solve failed during Yukawa likelihood computation.")
        return -np.inf
        
    chi_sq = np.dot(residual, z)
    log_det_cov = 2.0 * np.sum(np.log(np.diag(L)))
    
    log_likelihood = -0.5 * (chi_sq + log_det_cov + n * np.log(2.0 * np.pi))
    return log_likelihood

class YukawaLikelihood:
    """Callable class for Yukawa likelihood, suitable for MCMC samplers."""
    def __init__(self, separation: np.ndarray, force: np.ndarray, L: np.ndarray):
        self.separation = separation
        self.force = force
        self.L = L
        self.n = len(force)
        self.log_det_cov = 2.0 * np.sum(np.log(np.diag(L)))
        self.const_term = self.n * np.log(2.0 * np.pi)

    def __call__(self, params: np.ndarray) -> float:
        alpha, lambda_val = params
        # Basic sanity checks to avoid NaNs in physics model
        if alpha < 0 or lambda_val <= 0:
            return -np.inf
        try:
            return log_likelihood_yukawa(self.separation, self.force, None, self.L, alpha, lambda_val)
        except Exception:
            return -np.inf

class NewtonianLikelihood:
    """Callable class for Newtonian likelihood."""
    def __init__(self, separation: np.ndarray, force: np.ndarray, L: np.ndarray):
        self.separation = separation
        self.force = force
        self.L = L
        self.n = len(force)
        self.log_det_cov = 2.0 * np.sum(np.log(np.diag(L)))
        self.const_term = self.n * np.log(2.0 * np.pi)

    def __call__(self, params: np.ndarray) -> float:
        # Newtonian model has no free parameters in this context (alpha=0, lambda irrelevant)
        # We accept params for interface compatibility but ignore them.
        try:
            return log_likelihood_newtonian(self.separation, self.force, None, self.L)
        except Exception:
            return -np.inf

def main():
    """
    Main entry point to validate likelihood computation.
    Loads the covariance matrix, computes Cholesky, and prints likelihoods for
    dummy parameters to ensure the pipeline works.
    """
    logger.info("Starting likelihood validation...")
    config = ProjectConfig()
    
    # Paths
    cov_path = config.data_processed_dir / "covariance_matrix.npy"
    data_path = config.data_processed_dir / "harmonized_data.csv"
    
    if not cov_path.exists():
        logger.error(f"Covariance matrix not found at {cov_path}. Run harmonization first.")
        return
    
    if not data_path.exists():
        logger.error(f"Harmonized data not found at {data_path}. Run harmonization first.")
        return

    try:
        cov_matrix = load_covariance_matrix(cov_path)
        L, _ = compute_cholesky_decomposition(cov_matrix)
        
        # Load data
        df = pd.read_csv(data_path)
        # Ensure columns exist
        required_cols = ['separation_m', 'force_n']
        if not all(c in df.columns for c in required_cols):
            logger.error(f"Data missing required columns. Found: {df.columns.tolist()}")
            return

        separation = df['separation_m'].values
        force = df['force_n'].values

        # Test Newtonian
        ll_newt = log_likelihood_newtonian(separation, force, cov_matrix, L)
        logger.info(f"Newtonian Log-Likelihood: {ll_newt:.4f}")

        # Test Yukawa with dummy params
        ll_yuk = log_likelihood_yukawa(separation, force, cov_matrix, L, alpha=0.1, lambda_val=1e-4)
        logger.info(f"Yukawa Log-Likelihood (alpha=0.1, lambda=1e-4): {ll_yuk:.4f}")

        # Test Class interface
        yuk_lik = YukawaLikelihood(separation, force, L)
        ll_class = yuk_lik(np.array([0.1, 1e-4]))
        logger.info(f"Yukawa Likelihood (Class): {ll_class:.4f}")

        logger.info("Likelihood validation successful.")

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()