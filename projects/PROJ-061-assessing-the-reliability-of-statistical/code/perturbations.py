"""
Perturbation modules for injecting statistical assumption violations into datasets.

Implements:
1. Heavy-tailed noise injection (t-distribution)
2. AR(1) autocorrelation injection
3. Effect size heterogeneity via mixing two sub-populations
"""
import logging
from typing import Tuple, Optional, Dict, Any
import numpy as np
from scipy import stats
from config import RANDOM_SEED

logger = logging.getLogger(__name__)

def inject_heavy_tailed_noise(
    data: np.ndarray,
    contamination_rate: float = 0.1,
    degrees_of_freedom: float = 3.0,
    scale_factor: float = 5.0
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject heavy-tailed noise by replacing a fraction of data points with 
    values drawn from a t-distribution (heavy-tailed).
    
    Args:
        data: Input numpy array
        contamination_rate: Fraction of data to replace (0.0 to 1.0)
        degrees_of_freedom: df for t-distribution (lower = heavier tails)
        scale_factor: Scale multiplier for the t-distribution noise
        
    Returns:
        Tuple of (perturbed_data, metadata_dict)
    """
    if not 0.0 <= contamination_rate <= 1.0:
        raise ValueError("contamination_rate must be between 0.0 and 1.0")
    
    rng = np.random.default_rng(RANDOM_SEED)
    n = len(data)
    n_contaminated = int(n * contamination_rate)
    
    if n_contaminated == 0:
        logger.warning("contamination_rate too low, no points injected")
        return data.copy(), {
            "type": "heavy_tailed_noise",
            "contamination_rate": contamination_rate,
            "actual_contaminated": 0,
            "degrees_of_freedom": degrees_of_freedom
        }
    
    # Select random indices to contaminate
    indices = rng.choice(n, size=n_contaminated, replace=False)
    
    # Generate heavy-tailed noise
    # Center t-distribution at 0, then scale
    noise = rng.standard_t(df=degrees_of_freedom, size=n_contaminated) * scale_factor * np.std(data)
    
    # Create copy and inject noise
    perturbed_data = data.copy()
    perturbed_data[indices] = noise
    
    logger.info(f"Heavy-tailed noise injected: {n_contaminated}/{n} points ({contamination_rate*100:.1f}%)")
    
    return perturbed_data, {
        "type": "heavy_tailed_noise",
        "contamination_rate": contamination_rate,
        "actual_contaminated": n_contaminated,
        "degrees_of_freedom": degrees_of_freedom,
        "scale_factor": scale_factor
    }

def inject_ar1_autocorrelation(
    data: np.ndarray,
    ar_coefficient: float = 0.5,
    noise_std: Optional[float] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject AR(1) autocorrelation into the data.
    
    The AR(1) process is: x_t = phi * x_{t-1} + epsilon_t
    where epsilon_t ~ N(0, sigma^2)
    
    Args:
        data: Input numpy array (assumed to be time-ordered)
        ar_coefficient: The phi parameter (|phi| < 1 for stationarity)
        noise_std: Standard deviation of the innovation noise. If None, 
                  uses 10% of the original data's std.
                
    Returns:
        Tuple of (perturbed_data, metadata_dict)
    """
    if not -1.0 < ar_coefficient < 1.0:
        raise ValueError("ar_coefficient must be between -1.0 and 1.0 for stationarity")
    
    rng = np.random.default_rng(RANDOM_SEED)
    n = len(data)
    
    if noise_std is None:
        noise_std = 0.1 * np.std(data)
        if noise_std == 0:
            noise_std = 1.0
    
    # Initialize AR(1) process
    perturbed_data = np.zeros(n)
    perturbed_data[0] = data[0]  # Start with first point
    
    # Generate innovations
    innovations = rng.normal(0, noise_std, n)
    
    # Apply AR(1) recursion
    for t in range(1, n):
        perturbed_data[t] = ar_coefficient * perturbed_data[t-1] + innovations[t]
    
    # Scale to match original mean/variance roughly
    # This preserves the autocorrelation structure while keeping data magnitude similar
    target_mean = np.mean(data)
    target_std = np.std(data)
    current_mean = np.mean(perturbed_data)
    current_std = np.std(perturbed_data)
    
    if current_std > 0:
        perturbed_data = (perturbed_data - current_mean) / current_std * target_std + target_mean
    
    logger.info(f"AR(1) autocorrelation injected: phi={ar_coefficient}, noise_std={noise_std:.4f}")
    
    return perturbed_data, {
        "type": "ar1_autocorrelation",
        "ar_coefficient": ar_coefficient,
        "noise_std": noise_std,
        "original_mean": float(np.mean(data)),
        "original_std": float(np.std(data))
    }

def verify_ar1_coefficient(
    data: np.ndarray,
    target_coefficient: float,
    tolerance: float = 0.05
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Verify if the AR(1) coefficient in the data matches the target within tolerance.
    
    Uses the lag-1 autocorrelation as an estimate of the AR(1) coefficient.
    
    Args:
        data: Input numpy array
        target_coefficient: Expected AR(1) coefficient
        tolerance: Acceptable difference between estimated and target
        
    Returns:
        Tuple of (is_valid, estimated_coefficient, metadata_dict)
    """
    if len(data) < 3:
        return False, 0.0, {"error": "Insufficient data points for AR(1) estimation"}
    
    # Estimate lag-1 autocorrelation
    lag1 = data[1:]
    lag0 = data[:-1]
    
    # Simple correlation estimate
    numerator = np.mean((lag1 - np.mean(lag1)) * (lag0 - np.mean(lag0)))
    denominator = np.std(lag0) * np.std(lag1)
    
    if denominator == 0:
        estimated_coeff = 0.0
    else:
        estimated_coeff = numerator / denominator
    
    is_valid = abs(estimated_coeff - target_coefficient) <= tolerance
    
    logger.info(
        f"AR(1) verification: target={target_coefficient:.4f}, "
        f"estimated={estimated_coeff:.4f}, diff={abs(estimated_coeff - target_coefficient):.4f}, "
        f"valid={is_valid}"
    )
    
    return is_valid, estimated_coeff, {
        "type": "ar1_verification",
        "target_coefficient": target_coefficient,
        "estimated_coefficient": float(estimated_coeff),
        "tolerance": tolerance,
        "is_valid": is_valid,
        "difference": float(abs(estimated_coeff - target_coefficient))
    }

def inject_effect_size_heterogeneity(
    data: np.ndarray,
    group1_mean: float = 0.0,
    group2_mean: float = 1.5,
    mixing_ratio: float = 0.2,
    scale: Optional[float] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject effect size heterogeneity by mixing two sub-populations.
    
    Creates a mixture distribution where a fraction (mixing_ratio) of the data
    comes from a second population with a different mean (separation distance).
    
    Args:
        data: Input numpy array
        group1_mean: Mean of the primary population (usually 0 for standardized data)
        group2_mean: Mean of the secondary population (separation distance in SD units)
        mixing_ratio: Fraction of data to come from the second population (0.0 to 1.0)
        scale: Standard deviation for the distributions. If None, uses std of input data.
        
    Returns:
        Tuple of (perturbed_data, metadata_dict)
        
    Note:
        Based on spec US-2 Acceptance 3: mixing_ratio=0.2, separation=1.5 SD
    """
    if not 0.0 <= mixing_ratio <= 1.0:
        raise ValueError("mixing_ratio must be between 0.0 and 1.0")
    
    rng = np.random.default_rng(RANDOM_SEED)
    n = len(data)
    
    if scale is None:
        scale = np.std(data)
        if scale == 0:
            scale = 1.0
    
    # Determine number of points from group 2
    n_group2 = int(n * mixing_ratio)
    
    # Create indices for group 2
    group2_indices = rng.choice(n, size=n_group2, replace=False)
    
    # Create perturbed data
    perturbed_data = data.copy()
    
    # Replace group 2 points with new values from the second population
    # The second population has mean shifted by group2_mean * scale
    perturbed_data[group2_indices] = rng.normal(
        loc=group1_mean + group2_mean * scale,
        scale=scale,
        size=n_group2
    )
    
    logger.info(
        f"Effect size heterogeneity injected: "
        f"mixing_ratio={mixing_ratio}, separation={group2_mean:.2f} SD, "
        f"n_group2={n_group2}/{n}"
    )
    
    return perturbed_data, {
        "type": "effect_size_heterogeneity",
        "mixing_ratio": mixing_ratio,
        "group1_mean": group1_mean,
        "group2_mean": group2_mean,
        "separation_distance": group2_mean,
        "scale": scale,
        "actual_n_group2": n_group2,
        "total_n": n
    }