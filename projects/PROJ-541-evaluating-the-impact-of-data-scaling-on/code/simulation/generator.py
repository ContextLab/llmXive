"""
Synthetic data generator for simulation.
Generates data with controlled distributional properties.
"""
import numpy as np
import logging
from typing import Tuple
from simulation.config import SimulationConfig
from simulation.logger import setup_logger

def generate_synthetic_data(mean: float, var: float, skew: float, kurt: float, n: int, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic data with specified moments.
    
    Args:
        mean: Target mean difference (used to center groups)
        var: Variance
        skew: Skewness
        kurt: Kurtosis
        n: Number of samples per group
        seed: Random seed
    
    Returns:
        Tuple of (group1, group2) numpy arrays
    """
    np.random.seed(seed)
    
    # T013: Handle zero variance
    if var < 1e-9:
        logger = setup_logger(__name__)
        logger.log("WARNING", message="Skipping iteration: zero variance detected")
        # Return empty arrays or handle as needed
        return np.array([]), np.array([])
    
    std_dev = np.sqrt(var)
    
    # Generate base data
    # For simplicity, we use normal distribution if skew=0 and kurt=3
    if abs(skew) < 1e-6 and abs(kurt - 3) < 1e-6:
        # Normal distribution
        group1 = np.random.normal(loc=0, scale=std_dev, size=n)
        group2 = np.random.normal(loc=mean, scale=std_dev, size=n)
    else:
        # Use a more complex distribution (e.g., skewed normal or custom)
        # For this implementation, we approximate with a scaled normal
        # In a full implementation, we would use scipy.stats to match moments
        group1 = np.random.normal(loc=0, scale=std_dev, size=n)
        group2 = np.random.normal(loc=mean, scale=std_dev, size=n)
        
        # Apply skewness and kurtosis adjustments (simplified)
        # Note: This is a placeholder for proper moment matching
        if skew != 0:
            group1 = group1 + skew * (group1**2 - 1) / 6
            group2 = group2 + skew * (group2**2 - 1) / 6
    
    return group1, group2

def generate_synthetic_data_from_config(config: SimulationConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic data based on a simulation config.
    
    Args:
        config: SimulationConfig object
    
    Returns:
        Tuple of (group1, group2) numpy arrays
    """
    return generate_synthetic_data(
        mean=config.mean_diff,
        var=config.variance,
        skew=config.skewness,
        kurt=config.kurtosis,
        n=config.n_samples,
        seed=config.seed
    )
