"""
Power Analysis Module.

This module provides functions for calculating statistical power
for correlation tests and determining if the sample size is sufficient
to detect the expected effect size.

Functions:
    calculate_power_for_correlation: Estimates power for a given sample size and effect size.
    check_power_sufficiency: Validates if power meets the required threshold.
    run_power_analysis: Orchestrates power analysis for the dataset.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from scipy import stats

from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_power_for_correlation(n: int, effect_size: float = 0.5, alpha: float = 0.05) -> float:
    """
    Calculates statistical power for a correlation test.

    Args:
        n: Sample size.
        effect_size: Expected effect size (r).
        alpha: Significance level.

    Returns:
        Power value (0-1).
    """
    if n < 3:
        return 0.0
    
    # Approximation using Fisher's z-transformation
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    # Fisher z for correlation
    z_r = 0.5 * np.log((1 + effect_size) / (1 - effect_size))
    # Standard error of z_r
    se_z = 1 / np.sqrt(n - 3)
    
    # Power calculation
    z_beta = (np.sqrt(n - 3) * z_r) - z_alpha
    power = stats.norm.cdf(z_beta)
    return max(0.0, min(1.0, power))

def check_power_sufficiency(power: float, threshold: float = 0.20) -> bool:
    """
    Checks if the calculated power is sufficient.

    Args:
        power: The calculated power value.
        threshold: Minimum acceptable power (default 0.20).

    Returns:
        True if power is sufficient, False otherwise.
    """
    return power >= threshold

def run_power_analysis(df: pd.DataFrame, effect_size: float = 0.5) -> Dict[str, Any]:
    """
    Runs power analysis for the current dataset.

    Args:
        df: The input DataFrame.
        effect_size: Expected effect size.

    Returns:
        Dictionary containing power results.
    """
    n = len(df)
    power = calculate_power_for_correlation(n, effect_size)
    is_sufficient = check_power_sufficiency(power)
    
    return {
        'sample_size': n,
        'effect_size': effect_size,
        'power': power,
        'is_sufficient': is_sufficient,
        'status': 'Inconclusive due to low power' if not is_sufficient else 'Sufficient power'
    }

def main():
    """
    Entry point for testing the power analysis module directly.
    """
    logger.info("Power analysis module initialized.")
