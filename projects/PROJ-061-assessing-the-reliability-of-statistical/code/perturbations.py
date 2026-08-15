"""
Perturbation modules for injecting assumption violations into datasets.
All logic is CPU-only (no GPU dependencies).
"""
import logging
from typing import Tuple, Optional, Dict, Any, List
import numpy as np
from scipy import stats
from config import RANDOM_SEED

logger = logging.getLogger(__name__)

def inject_heavy_tailed_noise(
    data: np.ndarray,
    contamination_rate: float = 0.1,
    degrees_of_freedom: float = 3.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Inject heavy-tailed noise (t-distribution) into the data.
    CPU-only implementation using numpy.
    
    Args:
        data: Input array
        contamination_rate: Proportion of data to replace with heavy-tailed noise
        degrees_of_freedom: DF for t-distribution (lower = heavier tails)
        seed: Random seed for reproducibility
        
    Returns:
        Perturbed data array
    """
    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(RANDOM_SEED)
        
    n = len(data)
    n_contaminated = int(n * contamination_rate)
    
    # Generate indices for contamination
    indices = np.random.choice(n, size=n_contaminated, replace=False)
    
    # Generate heavy-tailed noise
    # Scale noise to match data variance roughly
    data_std = np.std(data)
    noise = stats.t.rvs(df=degrees_of_freedom, size=n_contaminated, scale=data_std)
    
    # Create copy and inject noise
    perturbed_data = data.copy()
    perturbed_data[indices] += noise
    
    logger.info(f"Injected heavy-tailed noise into {n_contaminated}/{n} samples (df={degrees_of_freedom})")
    return perturbed_data

def inject_ar1_autocorrelation(
    data: np.ndarray,
    ar_coefficient: float = 0.5,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Inject AR(1) autocorrelation into the data.
    CPU-only implementation using numpy.
    
    Args:
        data: Input array (assumed to be time-ordered)
        ar_coefficient: AR(1) coefficient (0 < phi < 1)
        seed: Random seed for reproducibility
        
    Returns:
        Perturbed data array with AR(1) structure
    """
    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(RANDOM_SEED)
        
    n = len(data)
    if n < 2:
        logger.warning("Array too short for AR(1) injection")
        return data
        
    # Generate white noise
    noise_std = np.std(data) * np.sqrt(1 - ar_coefficient**2)
    white_noise = np.random.normal(0, noise_std, n)
    
    # Apply AR(1) process: y_t = phi * y_{t-1} + epsilon_t
    ar_data = np.zeros(n)
    ar_data[0] = data[0] + white_noise[0]
    
    for t in range(1, n):
        ar_data[t] = ar_coefficient * ar_data[t-1] + (1 - ar_coefficient) * data[t] + white_noise[t]
    
    # Normalize to preserve original mean and variance approximately
    ar_data = (ar_data - np.mean(ar_data)) * (np.std(data) / np.std(ar_data)) + np.mean(data)
    
    logger.info(f"Injected AR(1) autocorrelation with coefficient {ar_coefficient}")
    return ar_data

def verify_ar1_coefficient(
    data: np.ndarray,
    target_coefficient: float,
    tolerance: float = 0.05
) -> Tuple[bool, float]:
    """
    Verify that the AR(1) coefficient in the data matches the target.
    CPU-only implementation using numpy/scipy.
    
    Args:
        data: Input array
        target_coefficient: Expected AR(1) coefficient
        tolerance: Acceptable deviation from target
        
    Returns:
        Tuple of (is_valid, achieved_coefficient)
    """
    n = len(data)
    if n < 3:
        logger.warning("Insufficient data to verify AR(1) coefficient")
        return False, 0.0
        
    # Estimate AR(1) coefficient using lag-1 autocorrelation
    data_centered = data - np.mean(data)
    numerator = np.sum(data_centered[:-1] * data_centered[1:])
    denominator = np.sum(data_centered[:-1] ** 2)
    
    if denominator == 0:
        estimated_phi = 0.0
    else:
        estimated_phi = numerator / denominator
        
    is_valid = abs(estimated_phi - target_coefficient) <= tolerance
    logger.info(f"AR(1) verification: target={target_coefficient}, achieved={estimated_phi:.4f}, valid={is_valid}")
    
    return is_valid, estimated_phi

def inject_effect_size_heterogeneity(
    data: np.ndarray,
    group_labels: np.ndarray,
    mixing_ratio: float = 0.2,
    separation_distance: float = 1.5,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Inject effect size heterogeneity by mixing two sub-populations.
    CPU-only implementation using numpy.
    
    Args:
        data: Input array
        group_labels: Binary labels (0 or 1) indicating group membership
        mixing_ratio: Proportion of the minority group to introduce
        separation_distance: Effect size difference in standard deviations
        seed: Random seed for reproducibility
        
    Returns:
        Perturbed data array with heterogeneous effect sizes
    """
    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(RANDOM_SEED)
        
    n = len(data)
    data_std = np.std(data)
    data_mean = np.mean(data)
    
    # Identify indices for the minority group
    # We'll create a new mixed population
    n_mixed = int(n * mixing_ratio)
    mixed_indices = np.random.choice(n, size=n_mixed, replace=False)
    
    # Create perturbed values for the mixed group
    # Shift by separation_distance * std
    perturbation = separation_distance * data_std * np.sign(np.random.randn(n_mixed))
    data[mixed_indices] += perturbation
    
    logger.info(f"Injected effect size heterogeneity: {n_mixed} samples shifted by {separation_distance} std")
    return data

def main():
    """
    Demonstration of perturbation functions (CPU-only).
    This function is for testing purposes and does not produce persistent artifacts.
    """
    logger.info("Running perturbation module demonstration (CPU-only)")
    
    # Create sample data
    np.random.seed(RANDOM_SEED)
    sample_data = np.random.normal(0, 1, 1000)
    sample_labels = np.random.randint(0, 2, 1000)
    
    # Test heavy-tailed noise
    result_ht = inject_heavy_tailed_noise(sample_data.copy(), contamination_rate=0.1, degrees_of_freedom=3.0)
    logger.info(f"Heavy-tailed noise: mean={np.mean(result_ht):.4f}, std={np.std(result_ht):.4f}")
    
    # Test AR(1)
    result_ar = inject_ar1_autocorrelation(sample_data.copy(), ar_coefficient=0.5)
    is_valid, achieved = verify_ar1_coefficient(result_ar, 0.5)
    logger.info(f"AR(1) verification: valid={is_valid}, achieved={achieved:.4f}")
    
    # Test effect size heterogeneity
    result_het = inject_effect_size_heterogeneity(sample_data.copy(), sample_labels, mixing_ratio=0.2, separation_distance=1.5)
    logger.info(f"Heterogeneity injection: mean={np.mean(result_het):.4f}, std={np.std(result_het):.4f}")
    
    logger.info("All perturbation tests completed successfully (CPU-only)")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()