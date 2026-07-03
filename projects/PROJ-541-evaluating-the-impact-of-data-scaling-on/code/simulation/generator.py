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


def generate_synthetic_data(config: SimulationConfig, logger: logging.Logger = None) -> Tuple[np.ndarray, np.ndarray, bool, str]:
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

        # Generate base data for group A (mean = 0)
        if distribution_type == "normal":
            group_a = np.random.normal(loc=0.0, scale=std_dev, size=n_samples)
        elif distribution_type == "skewed":
            # Generate skewed data using gamma distribution
            # Shape parameter affects skewness: lower = more skewed
            # Ensure shape is always positive and reasonable
            shape_param = max(1.0, 1.0 / (abs(skewness) + 0.1))
            group_a = np.random.gamma(shape=shape_param, scale=std_dev / shape_param, size=n_samples)
            # Center the data to have mean ~ 0
            group_a = group_a - np.mean(group_a)
        elif distribution_type == "heteroscedastic":
            # Generate data with varying variance
            base_data = np.random.normal(loc=0.0, scale=std_dev, size=n_samples)
            # Apply heteroscedasticity by scaling based on position
            scale_factors = 1.0 + heteroscedasticity * (np.arange(n_samples) / n_samples - 0.5) * 2
            group_a = base_data * scale_factors
        else:
            return None, None, False, f"Unknown distribution type: {distribution_type}"

        # Generate group B with specified mean difference
        if distribution_type == "normal":
            group_b = np.random.normal(loc=mean_diff, scale=std_dev, size=n_samples)
        elif distribution_type == "skewed":
            # Apply mean shift to skewed distribution
            shape_param = max(1.0, 1.0 / (abs(skewness) + 0.1))
            group_b = np.random.gamma(shape=shape_param, scale=std_dev / shape_param, size=n_samples)
            # Center and shift
            group_b = group_b - np.mean(group_b) + mean_diff
        elif distribution_type == "heteroscedastic":
            # Apply mean shift with heteroscedasticity
            base_data = np.random.normal(loc=mean_diff, scale=std_dev, size=n_samples)
            scale_factors = 1.0 + heteroscedasticity * (np.arange(n_samples) / n_samples - 0.5) * 2
            group_b = base_data * scale_factors
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