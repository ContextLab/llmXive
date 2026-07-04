"""
Power Analysis Module for Dietary Fiber and Gut Microbiome Study.

This module provides functions to calculate statistical power and margin of error
for correlation studies, specifically tailored for the correlation between
dietary fiber intake and gut microbiome composition.

It supports CPU-tractable calculations using standard statistical methods.
"""

import os
import math
import argparse
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import pandas as pd
import numpy as np
from scipy import stats

# Import the logger utility established in T005
from utils.logger import get_logger

# Initialize logger for this module
logger = get_logger("power_analysis")


def calculate_effect_size(r: float) -> float:
    """
    Calculate Cohen's d equivalent or effect size metric from correlation coefficient.
    For correlation studies, we often use r directly, but can convert to d for power tables.
    d = 2r / sqrt(1 - r^2)

    Args:
        r: Pearson correlation coefficient (-1 to 1)

    Returns:
        Effect size d
    """
    if abs(r) >= 1.0:
        return float('inf') if r > 0 else float('-inf')
    return (2 * r) / math.sqrt(1 - r**2)


def calculate_power_spearman(
    n: int,
    rho: float,
    alpha: float = 0.05,
    alternative: str = "two-sided"
) -> float:
    """
    Calculate statistical power for a Spearman correlation test.

    Uses the Fisher transformation approximation for power calculation.
    Power = P(Z > z_crit - z_rho) for one-sided, adjusted for two-sided.

    Args:
        n: Sample size
        rho: Expected Spearman correlation coefficient (effect size)
        alpha: Significance level (default 0.05)
        alternative: "two-sided", "greater", or "less"

    Returns:
        Statistical power (0 to 1)
    """
    if n < 3:
        return 0.0

    # Fisher's z-transformation
    # z = 0.5 * ln((1+r)/(1-r))
    if abs(rho) >= 1.0:
        # Perfect correlation, power is essentially 1 if n > 0
        return 1.0

    z_rho = 0.5 * math.log((1 + rho) / (1 - rho))
    
    # Standard error of Fisher's z
    se_z = 1.0 / math.sqrt(n - 3)

    # Critical z value for significance
    if alternative == "two-sided":
        z_crit = stats.norm.ppf(1 - alpha / 2)
    elif alternative == "greater":
        z_crit = stats.norm.ppf(1 - alpha)
        if rho < 0:
            return 0.0 # Impossible to detect positive effect with negative rho in greater test
    elif alternative == "less":
        z_crit = -stats.norm.ppf(1 - alpha)
        if rho > 0:
            return 0.0
    else:
        raise ValueError("alternative must be 'two-sided', 'greater', or 'less'")

    # Calculate power
    # Under H1, the distribution is shifted by z_rho / se_z
    # Power = P(Z > z_crit - (z_rho / se_z)) for positive effect
    # Power = P(Z < -z_crit - (z_rho / se_z)) for negative effect in two-sided
    
    # General formula for two-sided power:
    # Power = 1 - beta = P(reject H0 | H1 true)
    # Approximation: Power = Phi(z_rho/se_z - z_crit) + Phi(-z_rho/se_z - z_crit)
    # But simpler: Power = 1 - Phi(z_crit - delta) + Phi(-z_crit - delta)
    
    delta = z_rho / se_z
    
    if alternative == "two-sided":
        power = stats.norm.cdf(delta - z_crit) + stats.norm.cdf(-delta - z_crit)
    elif alternative == "greater":
        power = stats.norm.cdf(delta - z_crit)
    else: # less
        power = stats.norm.cdf(-delta - z_crit)

    return max(0.0, min(1.0, power))


def calculate_margin_of_error(
    n: int,
    rho: float,
    alpha: float = 0.05
) -> float:
    """
    Calculate the margin of error for a correlation coefficient.
    Uses the Fisher transformation to construct the confidence interval.

    MOE = z_crit * SE_z

    Args:
        n: Sample size
        rho: Observed or expected correlation coefficient
        alpha: Significance level

    Returns:
        Margin of error for the correlation coefficient (in original scale)
    """
    if n < 3:
        return float('inf')

    z_rho = 0.5 * math.log((1 + rho) / (1 - rho))
    se_z = 1.0 / math.sqrt(n - 3)
    z_crit = stats.norm.ppf(1 - alpha / 2)

    # Confidence interval in Z space
    z_lower = z_rho - z_crit * se_z
    z_upper = z_rho + z_crit * se_z

    # Transform back to r space
    r_lower = (math.exp(2 * z_lower) - 1) / (math.exp(2 * z_lower) + 1)
    r_upper = (math.exp(2 * z_upper) - 1) / (math.exp(2 * z_upper) + 1)

    # Margin of error is half the width (approx, assuming symmetry in Z space)
    # Or simply the distance from rho to the bounds
    moe_upper = r_upper - rho
    moe_lower = rho - r_lower
    
    # Return the maximum deviation
    return max(moe_upper, moe_lower)


def run_power_analysis(
    input_file: str,
    output_file: str,
    target_correlation: float = 0.3,
    alpha: float = 0.05,
    power_target: float = 0.8
) -> Dict[str, Any]:
    """
    Run a comprehensive power analysis on the harmonized dataset.

    1. Loads the harmonized dataset.
    2. Calculates actual sample size (n) after filtering.
    3. Calculates observed power for the target correlation.
    4. Calculates margin of error for the observed sample size.
    5. Calculates required sample size to achieve target power.
    6. Saves results to a TSV file.

    Args:
        input_file: Path to the harmonized dataset (merged_harmonized.tsv)
        output_file: Path to output the power analysis report (TSV)
        target_correlation: The effect size (rho) to test power against
        alpha: Significance level
        power_target: Desired power level (e.g., 0.8)

    Returns:
        Dictionary containing the analysis results
    """
    logger.info(f"Starting power analysis. Input: {input_file}, Output: {output_file}")

    # Ensure input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        # We still return a result indicating failure, but do not crash the script
        # The calling process (T006b) might handle the missing file logic, 
        # but for this module to be robust, we handle it here too.
        results = {
            "status": "failed",
            "reason": "Input file not found",
            "input_file": input_file,
            "output_file": output_file
        }
        # Write a minimal report
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write("status\treason\n")
            f.write(f"failed\tInput file not found: {input_file}\n")
        return results

    try:
        # Load data
        df = pd.read_csv(input_file, sep='\t')
        
        # We need 'fiber_intake' and a representative abundance column for power calc
        # Since power depends on N and effect size, we use N from the dataset
        # and the provided target_correlation.
        
        # Identify sample size
        n = len(df)
        
        if n < 3:
            logger.warning(f"Sample size too small ({n}) for power analysis.")
            results = {
                "status": "failed",
                "reason": f"Sample size ({n}) too small",
                "n": n
            }
            return results

        # Calculate Power
        observed_power = calculate_power_spearman(n, target_correlation, alpha)
        
        # Calculate Margin of Error
        moe = calculate_margin_of_error(n, target_correlation, alpha)
        
        # Calculate Required Sample Size for Target Power
        # Iterative approach to find n such that Power(n, rho) >= power_target
        required_n = n
        if observed_power < power_target:
            # Binary search or simple increment
            low, high = n, 100000
            found = False
            while low <= high:
                mid = (low + high) // 2
                p = calculate_power_spearman(mid, target_correlation, alpha)
                if p >= power_target:
                    required_n = mid
                    high = mid - 1
                    found = True
                else:
                    low = mid + 1
            if not found:
                required_n = "Infeasible (>100k)"
        
        results = {
            "status": "success",
            "sample_size": n,
            "target_correlation": target_correlation,
            "alpha": alpha,
            "calculated_power": observed_power,
            "margin_of_error": moe,
            "target_power": power_target,
            "required_sample_size": required_n
        }

        logger.info(f"Power analysis complete. Power: {observed_power:.4f}, MOE: {moe:.4f}")

        # Write output
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write("metric\tvalue\n")
            f.write(f"status\t{results['status']}\n")
            f.write(f"sample_size\t{results['sample_size']}\n")
            f.write(f"target_correlation\t{results['target_correlation']}\n")
            f.write(f"alpha\t{results['alpha']}\n")
            f.write(f"calculated_power\t{results['calculated_power']:.6f}\n")
            f.write(f"margin_of_error\t{results['margin_of_error']:.6f}\n")
            f.write(f"target_power\t{results['target_power']}\n")
            f.write(f"required_sample_size\t{results['required_sample_size']}\n")

        return results

    except Exception as e:
        logger.error(f"Error during power analysis: {e}", exc_info=True)
        return {
            "status": "failed",
            "reason": str(e)
        }


def main():
    """
    Entry point for the power analysis script.
    Parses command line arguments and runs the analysis.
    """
    parser = argparse.ArgumentParser(
        description="Calculate statistical power and margin of error for correlation studies."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/merged_harmonized.tsv",
        help="Path to the harmonized dataset (TSV)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/results/power_analysis_report.tsv",
        help="Path to save the power analysis report (TSV)."
    )
    parser.add_argument(
        "--target-rho",
        type=float,
        default=0.3,
        help="Target correlation coefficient (effect size) for power calculation."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)."
    )
    parser.add_argument(
        "--target-power",
        type=float,
        default=0.8,
        help="Target statistical power (default: 0.8)."
    )

    args = parser.parse_args()

    logger.info(f"Running power analysis with args: {vars(args)}")
    
    results = run_power_analysis(
        input_file=args.input,
        output_file=args.output,
        target_correlation=args.target_rho,
        alpha=args.alpha,
        power_target=args.target_power
    )

    if results["status"] == "success":
        print(f"Power analysis completed successfully.")
        print(f"Sample Size: {results['sample_size']}")
        print(f"Calculated Power: {results['calculated_power']:.4f}")
        print(f"Margin of Error: {results['margin_of_error']:.4f}")
        print(f"Required Sample Size for {args.target_power} power: {results['required_sample_size']}")
    else:
        print(f"Power analysis failed: {results.get('reason', 'Unknown error')}")
        # Exit with error code to indicate failure
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
