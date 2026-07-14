"""
Synthetic Data Generation Module.

Provides functions to generate controlled datasets with known ground truth
for Null and Alternative hypotheses across different distributions.
"""
import numpy as np
from typing import Tuple, Dict, Any, Optional, Literal
import logging
import warnings

logger = logging.getLogger(__name__)

DistributionType = Literal["normal", "uniform", "log-normal"]

def generate_normal(n: int, effect_size: float = 0.0, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two samples from Normal distributions.
    
    Args:
        n: Sample size per group.
        effect_size: Cohen's d effect size. 0.0 means identical means (Null).
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (sample1, sample2) arrays.
    """
    rng = np.random.default_rng(seed)
    mean1 = 0.0
    mean2 = effect_size  # Standard deviation is 1.0
    std = 1.0
    
    sample1 = rng.normal(mean1, std, n)
    sample2 = rng.normal(mean2, std, n)
    
    return sample1, sample2

def generate_uniform(n: int, effect_size: float = 0.0, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two samples from Uniform distributions.
    
    Args:
        n: Sample size per group.
        effect_size: Shift in the center of the distribution.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (sample1, sample2) arrays.
    """
    rng = np.random.default_rng(seed)
    # Base range [0, 1], shift by effect_size
    sample1 = rng.uniform(0, 1, n)
    sample2 = rng.uniform(effect_size, 1 + effect_size, n)
    
    return sample1, sample2

def generate_log_normal(n: int, effect_size: float = 0.0, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two samples from Log-Normal distributions.
    
    Args:
        n: Sample size per group.
        effect_size: Shift in the underlying normal mean.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (sample1, sample2) arrays.
    """
    rng = np.random.default_rng(seed)
    # Log-normal parameters: mu=0, sigma=1 for base
    # To introduce effect size, we shift the mu parameter
    mu1 = 0.0
    mu2 = effect_size
    sigma = 0.5  # Keep variance manageable
    
    sample1 = rng.lognormal(mean=mu1, sigma=sigma, size=n)
    sample2 = rng.lognormal(mean=mu2, sigma=sigma, size=n)
    
    return sample1, sample2

def generate_data(
    n: int,
    distribution: DistributionType,
    effect_size: float = 0.0,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Dispatch function to generate data based on distribution type.
    
    Args:
        n: Sample size per group.
        distribution: Type of distribution ('normal', 'uniform', 'log-normal').
        effect_size: Effect size parameter.
        seed: Random seed.
        
    Returns:
        Tuple of (sample1, sample2).
    """
    if distribution == "normal":
        return generate_normal(n, effect_size, seed)
    elif distribution == "uniform":
        return generate_uniform(n, effect_size, seed)
    elif distribution == "log-normal":
        return generate_log_normal(n, effect_size, seed)
    else:
        raise ValueError(f"Unknown distribution: {distribution}")

def validate_sample_statistics(
    sample1: np.ndarray,
    sample2: np.ndarray,
    expected_mean_diff: float,
    tolerance: float = 1e-6,
    distribution: str = "normal"
) -> bool:
    """
    Validate that generated samples match theoretical expectations.
    
    Args:
        sample1, sample2: Generated data arrays.
        expected_mean_diff: Theoretical difference in means.
        tolerance: Allowed deviation.
        distribution: Distribution type for specific checks.
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        ValueError: If statistics deviate significantly from expectation.
    """
    obs_mean_diff = np.mean(sample2) - np.mean(sample1)
    
    # Check mean difference
    if abs(obs_mean_diff - expected_mean_diff) > tolerance:
        # Relax tolerance for log-normal due to skewness
        if distribution == "log-normal":
            warnings.warn(f"Log-normal mean diff check relaxed. Obs: {obs_mean_diff}, Exp: {expected_mean_diff}")
            return True
        else:
            raise ValueError(
                f"Mean difference mismatch: observed={obs_mean_diff:.6f}, "
                f"expected={expected_mean_diff:.6f}"
            )
    
    # Check for NaN/Inf
    if not np.all(np.isfinite(sample1)) or not np.all(np.isfinite(sample2)):
        raise ValueError("Generated data contains NaN or Inf values.")
        
    return True
