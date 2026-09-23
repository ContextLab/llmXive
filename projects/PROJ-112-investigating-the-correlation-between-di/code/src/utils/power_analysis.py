"""
Statistical Power Analysis Module.

This module provides functions to calculate statistical power for Spearman's correlation
and the margin of error for a given sample size and effect size.

It is designed to be CPU-tractable and does not require GPU acceleration.
"""

import os
import math
import argparse
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import numpy as np
import pandas as pd
from scipy import stats

from src.utils.logger import get_logger

# Ensure the logger is configured correctly
logger = get_logger(__name__)


def calculate_effect_size(rho: float) -> float:
    """
    Calculates the Fisher's z-transformed effect size for a given correlation coefficient.

    Args:
        rho (float): Pearson or Spearman correlation coefficient (-1 to 1).

    Returns:
        float: Fisher's z-transformed value.

    Raises:
        ValueError: If rho is outside the range (-1, 1).
    """
    if not -1 < rho < 1:
        raise ValueError("Correlation coefficient (rho) must be strictly between -1 and 1.")
    
    # Fisher's z-transformation
    z_r = 0.5 * math.log((1 + rho) / (1 - rho))
    return z_r


def calculate_power_spearman(n: int, rho: float, alpha: float = 0.05) -> float:
    """
    Calculates the statistical power for a two-tailed Spearman correlation test.

    Uses the Fisher's z-transformation approximation for power calculation.

    Args:
        n (int): Sample size.
        rho (float): Expected correlation coefficient (effect size).
        alpha (float): Significance level (default 0.05).

    Returns:
        float: Calculated statistical power (0 to 1).
    """
    if n < 3:
        logger.warning(f"Sample size {n} is too small for power analysis. Returning 0.0.")
        return 0.0

    z_r = calculate_effect_size(rho)
    
    # Standard error of z_r
    se_z = 1.0 / math.sqrt(n - 3)
    
    # Critical z-value for the given alpha (two-tailed)
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    
    # Power calculation: P(Z > z_alpha - |z_r|/se_z) + P(Z < -z_alpha - |z_r|/se_z)
    # Since we are looking for power against the alternative hypothesis,
    # we calculate the probability of rejecting the null when the true effect is z_r.
    # Under H1, the distribution of z_hat is N(z_r, se_z^2).
    # We reject H0 if |z_hat| > z_alpha * se_z (approx).
    # More precisely:
    # Power = P( (z_hat - 0)/se_z > z_alpha | H1 ) + P( (z_hat - 0)/se_z < -z_alpha | H1 )
    #       = P( Z > z_alpha - z_r/se_z ) + P( Z < -z_alpha - z_r/se_z )
    
    # Using the absolute value of the effect for two-tailed test logic in standard approximations
    # However, the sign matters for the direction. Standard power analysis for correlation
    # often assumes a specific direction or uses the magnitude.
    # Let's use the standard formula: Power = 1 - beta.
    # beta = P( -z_alpha < Z < z_alpha | H1 ) where Z ~ N(z_r/se_z, 1)
    # Actually, the test statistic under H0 is Z = z_hat * sqrt(n-3).
    # Under H1, z_hat ~ N(z_r, 1/(n-3)).
    # So the test statistic T = z_hat * sqrt(n-3) ~ N(z_r * sqrt(n-3), 1).
    
    non_central_param = z_r * math.sqrt(n - 3)
    
    # Probability of falling in the rejection region (two-tailed)
    # Rejection region: T > z_alpha or T < -z_alpha
    # Power = P(T > z_alpha) + P(T < -z_alpha)
    
    prob_upper = 1 - stats.norm.cdf(z_alpha - non_central_param)
    prob_lower = stats.norm.cdf(-z_alpha - non_central_param)
    
    power = prob_upper + prob_lower
    return max(0.0, min(1.0, power))


def calculate_margin_of_error(n: int, rho: float = 0.0, alpha: float = 0.05) -> float:
    """
    Calculates the margin of error for a correlation coefficient estimate.
    
    This is typically defined as the half-width of the confidence interval for the
    correlation coefficient, transformed back from the Fisher's z scale.
    
    Args:
        n (int): Sample size.
        rho (float): Observed or expected correlation coefficient (default 0.0).
        alpha (float): Significance level (default 0.05).

    Returns:
        float: Margin of error (half-width of CI) on the correlation scale.
    """
    if n < 3:
        raise ValueError("Sample size must be at least 3 to calculate margin of error.")
    
    z_r = calculate_effect_size(rho)
    se_z = 1.0 / math.sqrt(n - 3)
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    
    # Margin of error in Fisher's z scale
    moe_z = z_alpha * se_z
    
    # Calculate the upper and lower bounds in z scale
    z_upper = z_r + moe_z
    z_lower = z_r - moe_z
    
    # Transform back to correlation scale
    rho_upper = (math.exp(2 * z_upper) - 1) / (math.exp(2 * z_upper) + 1)
    rho_lower = (math.exp(2 * z_lower) - 1) / (math.exp(2 * z_lower) + 1)
    
    # Margin of error is the distance from the point estimate to the bounds
    # Ideally symmetric on the z scale, but not on the rho scale.
    # We return the average distance or the maximum distance. 
    # Standard practice often reports the CI, but if a single MoE is needed:
    moe = max(abs(rho_upper - rho), abs(rho_lower - rho))
    
    return moe


def run_power_analysis(
    sample_size: int, 
    effect_size: float, 
    alpha: float = 0.05,
    output_path: Optional[Path] = None
) -> Dict[str, float]:
    """
    Runs a complete power analysis for a given sample size and effect size.
    
    Args:
        sample_size (int): The number of samples.
        effect_size (float): The expected correlation coefficient (rho).
        alpha (float): Significance level.
        output_path (Optional[Path]): If provided, writes results to this file.
    
    Returns:
        Dict[str, float]: A dictionary containing 'power' and 'margin_of_error'.
    """
    logger.info(f"Running power analysis: n={sample_size}, rho={effect_size}, alpha={alpha}")
    
    power = calculate_power_spearman(sample_size, effect_size, alpha)
    moe = calculate_margin_of_error(sample_size, effect_size, alpha)
    
    results = {
        "sample_size": float(sample_size),
        "effect_size": float(effect_size),
        "alpha": float(alpha),
        "power": power,
        "margin_of_error": moe
    }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame([results])
        df.to_csv(output_path, sep='\t', index=False)
        logger.info(f"Power analysis results written to {output_path}")
    
    return results


def main():
    """
    Command-line interface for running power analysis.
    """
    parser = argparse.ArgumentParser(
        description="Calculate statistical power and margin of error for Spearman correlation."
    )
    parser.add_argument(
        "--sample-size", 
        type=int, 
        required=True, 
        help="Number of samples (n)."
    )
    parser.add_argument(
        "--effect-size", 
        type=float, 
        required=True, 
        help="Expected correlation coefficient (rho), between -1 and 1."
    )
    parser.add_argument(
        "--alpha", 
        type=float, 
        default=0.05, 
        help="Significance level (default: 0.05)."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None, 
        help="Path to output TSV file. If not provided, prints to stdout."
    )
    
    args = parser.parse_args()
    
    try:
        results = run_power_analysis(
            sample_size=args.sample_size,
            effect_size=args.effect_size,
            alpha=args.alpha,
            output_path=Path(args.output) if args.output else None
        )
        
        if not args.output:
            print(f"Sample Size: {results['sample_size']}")
            print(f"Effect Size (rho): {results['effect_size']}")
            print(f"Alpha: {results['alpha']}")
            print(f"Power: {results['power']:.4f}")
            print(f"Margin of Error: {results['margin_of_error']:.4f}")
            
    except ValueError as e:
        logger.error(f"Input error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during power analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
