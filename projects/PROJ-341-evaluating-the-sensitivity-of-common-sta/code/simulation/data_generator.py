"""
Base data generator utilities for the llmXive simulation pipeline.

Supports generation of synthetic data following Normal and Multinomial distributions
based on specified parameters. This module is designed to work with the deterministic
random seed manager from code/simulation/__init__.py.

Dependencies:
    - numpy: For vectorized random number generation.
    - scipy.stats: For statistical distribution handling (optional, used for validation).
"""

import numpy as np
from typing import Tuple, Union, Optional, List
import json
import os

# Import the seed manager from the sibling module
from code.simulation import get_rng

def generate_normal_data(
    n: int,
    mu: float = 0.0,
    sigma: float = 1.0,
    groups: int = 2,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates synthetic data from a Normal (Gaussian) distribution.

    This function is used to simulate data for t-tests and ANOVA scenarios.
    It generates data for multiple groups if specified, allowing for effect
    size manipulation by shifting the mean of subsequent groups.

    Args:
        n (int): Sample size per group.
        mu (float): Mean of the reference group (Group 0).
        sigma (float): Standard deviation (assumed equal across groups).
        groups (int): Number of groups to generate (default 2 for t-test).
        seed (int, optional): Override the global seed manager for this specific call.
                              If None, uses the global deterministic seed.

    Returns:
        Tuple[np.ndarray, np.ndarray]:
            - data: Array of shape (groups, n) containing the generated values.
            - labels: Array of shape (groups,) containing group identifiers (0 to groups-1).
    """
    rng = get_rng(seed)

    # Generate base data for all groups
    # We generate from N(0, 1) first, then scale and shift to ensure
    # we can control effect sizes precisely if needed later.
    # Here we directly generate based on mu and sigma.
    data = rng.normal(loc=mu, scale=sigma, size=(groups, n))

    # If groups > 1, we might want to introduce an effect size for specific groups
    # based on the research design. For now, this function returns the raw generation.
    # The caller (test_runner) will likely manipulate the means of specific groups
    # to simulate an effect size (Cohen's d).
    # However, to be useful as a standalone utility, we return the generated data.
    # Note: If the caller wants to inject an effect, they should shift the 'data' array
    # for specific groups before passing to the statistical test.

    labels = np.arange(groups)

    return data, labels


def generate_multinomial_data(
    n: int,
    probabilities: List[float],
    categories: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generates synthetic data from a Multinomial distribution.

    This function is used to simulate contingency table data for Chi-squared tests.
    It generates counts for a single sample of size 'n' distributed across 'categories'.

    Args:
        n (int): Total sample size (number of trials).
        probabilities (List[float]): List of probabilities for each category.
                                     Must sum to 1.0.
        categories (int): Number of categories (cells in the contingency table).
        seed (int, optional): Override the global seed manager for this specific call.
                              If None, uses the global deterministic seed.

    Returns:
        np.ndarray: Array of shape (categories,) containing the observed counts.
    """
    rng = get_rng(seed)

    # Validate probabilities
    if len(probabilities) != categories:
        raise ValueError(f"Length of probabilities ({len(probabilities)}) must match categories ({categories}).")

    total_prob = sum(probabilities)
    if not np.isclose(total_prob, 1.0):
        # Normalize if close, otherwise error
        if np.isclose(total_prob, 1.0, atol=1e-6):
            probabilities = [p / total_prob for p in probabilities]
        else:
            raise ValueError(f"Probabilities must sum to 1.0. Sum is {total_prob}.")

    # Generate counts
    counts = rng.multinomial(n=n, pvals=probabilities)

    return counts


def generate_contingency_table_data(
    n: int,
    rows: int,
    cols: int,
    effect_size: float = 0.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generates a synthetic contingency table for Chi-squared tests.

    This function creates a table of counts based on a null hypothesis (equal distribution)
    or introduces an effect size to simulate a deviation from independence.

    Args:
        n (int): Total sample size.
        rows (int): Number of rows in the contingency table.
        cols (int): Number of columns in the contingency table.
        effect_size (float): Magnitude of deviation from independence.
                             0.0 = Null hypothesis (independence).
                             > 0.0 = Alternative hypothesis (dependence).
        seed (int, optional): Override the global seed manager for this specific call.

    Returns:
        np.ndarray: 2D array of shape (rows, cols) containing the observed counts.
    """
    rng = get_rng(seed)

    # Base probabilities: uniform distribution under null
    base_probs = np.ones((rows, cols)) / (rows * cols)

    if effect_size != 0.0:
        # Introduce a simple deviation pattern for the alternative hypothesis
        # We boost the diagonal elements and reduce off-diagonal to create dependence
        deviation = np.zeros((rows, cols))
        for i in range(rows):
            for j in range(cols):
                if i == j:
                    deviation[i, j] = effect_size
                else:
                    deviation[i, j] = -effect_size / (rows * cols - 1)

        # Apply deviation and renormalize
        adjusted_probs = base_probs + deviation
        # Ensure no negative probabilities
        adjusted_probs = np.maximum(adjusted_probs, 1e-9)
        adjusted_probs = adjusted_probs / adjusted_probs.sum()
    else:
        adjusted_probs = base_probs

    # Flatten probabilities for multinomial generation
    flat_probs = adjusted_probs.flatten()

    # Generate total counts
    flat_counts = rng.multinomial(n=n, pvals=flat_probs)

    # Reshape to 2D table
    table = flat_counts.reshape(rows, cols)

    return table

def validate_distribution_params(
    data: np.ndarray,
    expected_mean: float,
    expected_std: float,
    tolerance: float = 0.1
) -> bool:
    """
    Validates that generated data roughly matches expected distribution parameters.
    Used for testing the generator itself.

    Args:
        data: The generated data array.
        expected_mean: Expected mean.
        expected_std: Expected standard deviation.
        tolerance: Allowed relative deviation (default 10%).

    Returns:
        bool: True if data is within tolerance, False otherwise.
    """
    if len(data) == 0:
        return False

    obs_mean = np.mean(data)
    obs_std = np.std(data)

    # Check mean
    mean_diff = abs(obs_mean - expected_mean)
    if mean_diff > tolerance * abs(expected_mean) and expected_mean != 0:
        return False

    # Check std (relative)
    if expected_std > 0:
        std_diff = abs(obs_std - expected_std)
        if std_diff > tolerance * expected_std:
            return False

    return True
