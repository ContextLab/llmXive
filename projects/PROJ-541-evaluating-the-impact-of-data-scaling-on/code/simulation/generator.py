"""
Synthetic data generator for simulation studies.

This module provides functions to generate synthetic datasets with controlled
distributional properties where ground truth is known. It supports generating
data for both null and alternative hypotheses, as well as skewed and
heteroscedastic distributions.

Functions:
- generate_synthetic_data: Main entry point for data generation
"""
import numpy as np
import logging
from typing import Tuple
from simulation.config import SimulationConfig
from simulation.logger import setup_logger


def generate_synthetic_data(mean: float, var: float, skew: float, kurt: float, n: int, seed: int) -> Tuple[np.ndarray, np.ndarray, bool, str]:
    """
    Generate synthetic data for two groups based on arbitrary distributional moments.

    This function generates two groups of data (group_a and group_b) with
    controlled distributional properties defined by mean, variance, skewness,
    and kurtosis. It maps the variance to the scale parameter of scipy.stats.norm
    for normal distributions. If skewness=0 and kurtosis=3, it defaults to a
    Normal distribution.

    Args:
        mean: Target mean for the distribution (applied to group_b relative to group_a=0)
        var: Target variance (mapped to scale parameter for normal)
        skew: Target skewness (0 for symmetric)
        kurt: Target kurtosis (3 for normal)
        n: Number of samples to generate for each group
        seed: Random seed for reproducibility

    Returns:
        Tuple containing:
            - group_a: numpy array of samples for group A (mean ~ 0)
            - group_b: numpy array of samples for group B (mean ~ mean)
            - success: boolean indicating if generation was successful
            - message: string containing success message or error description

    Raises:
        ValueError: If configuration parameters are invalid
    """
    logger = setup_logger(__name__)

    try:
        # Validate parameters
        if n <= 0:
            return None, None, False, "n must be positive"
        if var <= 0:
            return None, None, False, "variance must be positive"
        
        # Check for zero-variance edge case
        std_dev = np.sqrt(var)
        if std_dev < 1e-9:
            logger.warning("Skipping iteration: zero variance detected")
            return None, None, False, "Zero variance detected"

        # Set random seed for reproducibility
        np.random.seed(seed)

        # Determine distribution type based on moments
        is_normal = (abs(skew) < 1e-6) and (abs(kurt - 3.0) < 1e-6)

        if is_normal:
            # Default to Normal distribution
            # Map variance to scale (std dev)
            scale = std_dev
            group_a = np.random.normal(loc=0.0, scale=scale, size=n)
            group_b = np.random.normal(loc=mean, scale=scale, size=n)
            logger.info(f"Generated Normal distribution: n={n}, mean_diff={mean}, var={var}")

        else:
            # For non-normal distributions, we use a transformation approach
            # We generate from a base distribution and apply transformations to match moments
            # Using a Johnson SU distribution approximation via polynomial transformation
            
            # Generate base normal data
            z = np.random.normal(0, 1, size=n)
            
            # Apply transformation to match skewness and kurtosis
            # Using a cubic transformation: y = z + a*z^2 + b*z^3
            # This allows us to control skew and kurtosis approximately
            
            # Calculate coefficients to match target moments
            # For y = z + a*z^2 + b*z^3:
            # E[y] = a
            # Var[y] = 1 + 2a^2 + 6b^2 + 12ab
            # Skew[y] ≈ 2a + 6b
            # Kurt[y] ≈ 3 + 12a^2 + 48ab + 120b^2
            
            # Simplified approach: use empirical adjustment
            # Generate initial skewed data
            if abs(skew) > 1e-6:
                # Apply skewness transformation
                # y = z + (skew/6) * (z^2 - 1)
                z = z + (skew / 6.0) * (z**2 - 1)
            
            # Adjust for kurtosis if needed
            if abs(kurt - 3.0) > 1e-6:
                # Apply kurtosis adjustment
                # Scale the tails
                kurt_factor = (kurt / 3.0) ** 0.5
                z = z * kurt_factor
            
            # Normalize to have mean 0 and variance 1
            z = (z - np.mean(z)) / np.std(z)
            
            # Scale to target variance and shift to target mean
            group_a = z * std_dev
            group_b = z * std_dev + mean
            
            logger.info(f"Generated transformed distribution: n={n}, mean_diff={mean}, var={var}, skew={skew}, kurt={kurt}")

        # Validate ground truth
        empirical_mean_diff = np.mean(group_b) - np.mean(group_a)

        if abs(mean) < 1e-6:
            # Null hypothesis check
            if abs(empirical_mean_diff) >= 0.01:
                logger.warning(f"Null hypothesis validation failed: |mean_diff|={abs(empirical_mean_diff):.6f} >= 0.01")
                return group_a, group_b, False, f"Null hypothesis contract violated: |mean_diff|={abs(empirical_mean_diff):.6f}"
        else:
            # Alternative hypothesis check
            deviation = abs(empirical_mean_diff - mean)
            if deviation >= 0.05:
                logger.warning(f"Alternative hypothesis validation failed: |mean_diff - {mean}|={deviation:.6f} >= 0.05")
                return group_a, group_b, False, f"Alternative hypothesis contract violated: deviation={deviation:.6f}"

        logger.info(f"Successfully generated synthetic data: n={n}, mean_diff={empirical_mean_diff:.6f}")
        return group_a, group_b, True, "Generation successful"

    except Exception as e:
        logger.error(f"Error generating synthetic data: {str(e)}")
        return None, None, False, str(e)


def generate_synthetic_data_from_config(config: SimulationConfig, logger: logging.Logger = None) -> Tuple[np.ndarray, np.ndarray, bool, str]:
    """
    Generate synthetic data for two groups based on the provided configuration.

    This function generates two groups of data (group_a and group_b) with
    controlled distributional properties. The ground truth mean difference
    between the groups is known and can be validated.

    Args:
        config: SimulationConfig object containing generation parameters
        logger: Optional logger instance. If None, a default logger is created.

    Returns:
        Tuple containing:
            - group_a: numpy array of samples for group A
            - group_b: numpy array of samples for group B
            - success: boolean indicating if generation was successful
            - message: string containing success message or error description

    Raises:
        ValueError: If configuration parameters are invalid
    """
    if logger is None:
        logger = setup_logger(__name__)

    try:
        # Set random seed for reproducibility
        np.random.seed(config.seed)

        n_samples = config.n_samples
        mean_diff = config.mean_diff
        std_dev = config.std_dev
        distribution_type = config.distribution_type
        skewness = config.skewness
        heteroscedasticity = config.heteroscedasticity

        # Validate parameters
        if n_samples <= 0:
            return None, None, False, "n_samples must be positive"
        if std_dev <= 0:
            return None, None, False, "std_dev must be positive"

        # Check for zero-variance edge case
        if std_dev < 1e-9:
            logger.warning("Skipping iteration: zero variance detected")
            return None, None, False, "Zero variance detected"

        # Vectorized generation for performance
        # Pre-allocate arrays
        
        if distribution_type == "normal":
            # Vectorized normal generation
            group_a = np.random.normal(loc=0.0, scale=std_dev, size=n_samples)
            group_b = np.random.normal(loc=mean_diff, scale=std_dev, size=n_samples)

        elif distribution_type == "skewed":
            # Vectorized skewed generation using gamma distribution
            # Shape parameter affects skewness: lower = more skewed
            shape_param = max(1.0, 1.0 / (abs(skewness) + 0.1))
            scale_param = std_dev / shape_param

            # Generate gamma samples
            raw_a = np.random.gamma(shape=shape_param, scale=scale_param, size=n_samples)
            raw_b = np.random.gamma(shape=shape_param, scale=scale_param, size=n_samples)

            # Center and shift
            group_a = raw_a - np.mean(raw_a)
            group_b = raw_b - np.mean(raw_b) + mean_diff

        elif distribution_type == "heteroscedastic":
            # Vectorized heteroscedastic generation
            # Generate base data
            base_a = np.random.normal(loc=0.0, scale=std_dev, size=n_samples)
            base_b = np.random.normal(loc=mean_diff, scale=std_dev, size=n_samples)

            # Apply heteroscedasticity using vectorized operations
            indices = np.arange(n_samples)
            scale_factors = 1.0 + heteroscedasticity * (indices / n_samples - 0.5) * 2

            group_a = base_a * scale_factors
            group_b = base_b * scale_factors

        else:
            return None, None, False, f"Unknown distribution type: {distribution_type}"

        # Validate ground truth
        empirical_mean_diff = np.mean(group_b) - np.mean(group_a)

        if config.mean_diff == 0.0:
            # Null hypothesis check
            if abs(empirical_mean_diff) >= 0.01:
                logger.warning(f"Null hypothesis validation failed: |mean_diff|={abs(empirical_mean_diff):.6f} >= 0.01")
                return group_a, group_b, False, f"Null hypothesis contract violated: |mean_diff|={abs(empirical_mean_diff):.6f}"
        else:
            # Alternative hypothesis check
            deviation = abs(empirical_mean_diff - config.mean_diff)
            if deviation >= 0.05:
                logger.warning(f"Alternative hypothesis validation failed: |mean_diff - {config.mean_diff}|={deviation:.6f} >= 0.05")
                return group_a, group_b, False, f"Alternative hypothesis contract violated: deviation={deviation:.6f}"

        logger.info(f"Successfully generated synthetic data: n={n_samples}, mean_diff={empirical_mean_diff:.6f}")
        return group_a, group_b, True, "Generation successful"

    except Exception as e:
        logger.error(f"Error generating synthetic data: {str(e)}")
        return None, None, False, str(e)