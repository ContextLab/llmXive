from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import numpy as np
import hashlib
from scipy import stats
from .config import get_run_seed

@dataclass
class SyntheticDataset:
    X: np.ndarray
    T: np.ndarray
    Y: np.ndarray
    ground_truth_ate: float
    seed: int

class SCMGenerator:
    pass

def regenerate_ground_truth(seed: int, beta: float) -> Tuple[float, float]:
    """
    Deterministically regenerate the exact tau_true and beta parameters for a given seed.
    
    Constitution Principle VI compliance: ensures that for any seed and beta, 
    the ground truth parameters are reproducible.
    
    Args:
        seed: Random seed for reproducibility
        beta: MNAR mechanism parameter
        
    Returns:
        Tuple of (tau_true, beta) where tau_true is hardcoded to 0.5 for this experiment
    """
    # For this specific experiment, tau_true is fixed at 0.5
    # The seed is used to ensure reproducibility of the random processes
    # that depend on these parameters, but tau_true itself is a constant
    tau_true = 0.5
    
    return tau_true, beta

def generate_scm(seed: int, n: int, tau_true: float) -> SyntheticDataset:
    """
    Generate a synthetic SCM dataset with known ground-truth ATE.
    
    Args:
        seed: Random seed for reproducibility
        n: Sample size
        tau_true: True average treatment effect
        
    Returns:
        SyntheticDataset with X, T, Y, ground_truth_ate, and seed
    """
    rng = np.random.default_rng(seed)
    
    # Generate confounder X
    X = rng.normal(0, 1, n)
    
    # Generate treatment T based on X and random noise
    # P(T=1|X) = sigmoid(alpha + gamma*X)
    alpha_t = 0.0
    gamma_t = 0.5
    logit_p = alpha_t + gamma_t * X
    p_t = 1 / (1 + np.exp(-logit_p))
    T = (rng.random(n) < p_t).astype(int)
    
    # Generate outcome Y based on T, X, and random noise
    # Y = tau_true * T + beta_x * X + epsilon
    beta_x = 0.3
    epsilon = rng.normal(0, 1, n)
    Y = tau_true * T + beta_x * X + epsilon
    
    return SyntheticDataset(
        X=X,
        T=T,
        Y=Y,
        ground_truth_ate=tau_true,
        seed=seed
    )

def check_collinearity(X: np.ndarray, threshold: float = 0.95) -> bool:
    """
    Check for near-perfect collinearity in the feature matrix.
    
    Args:
        X: Feature matrix
        threshold: Correlation threshold for flagging collinearity
        
    Returns:
        True if collinearity is detected, False otherwise
    """
    if X.shape[1] < 2:
        return False
    
    corr_matrix = np.corrcoef(X.T)
    # Check off-diagonal elements
    mask = ~np.eye(corr_matrix.shape[0], dtype=bool)
    max_corr = np.abs(corr_matrix[mask]).max()
    
    return max_corr > threshold
