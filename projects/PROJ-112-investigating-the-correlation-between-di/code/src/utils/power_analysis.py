"""
Power Analysis Module for Dietary Fiber and Gut Microbiome Study.

This module provides functions to calculate statistical power for Spearman correlations,
effect sizes, and margins of error. It is designed to be CPU-tractable and runs on
standard hardware.

Functions:
  - calculate_effect_size: Computes Cohen's d or correlation-based effect size.
  - calculate_power_spearman: Estimates power for a given sample size and correlation.
  - calculate_margin_of_error: Computes the margin of error for a correlation estimate.
  - run_power_analysis: Main function to perform power analysis on a dataset.
  - main: CLI entry point.
"""

import os
import math
import argparse
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import pandas as pd
import numpy as np
from scipy import stats

# Import logger from the project's utility module
from src.utils.logger import get_logger

# Ensure the logger is configured
logger = get_logger("power_analysis")


def calculate_effect_size(r: float, n: int) -> Dict[str, float]:
    """
    Calculate effect size metrics from a correlation coefficient.

    Args:
        r: Pearson or Spearman correlation coefficient.
        n: Sample size.

    Returns:
        Dictionary containing:
            - r: The correlation coefficient.
            - r_squared: Coefficient of determination.
            - fisher_z: Fisher's z-transformation of r.
            - ci_lower_95: Lower bound of 95% CI for r.
            - ci_upper_95: Upper bound of 95% CI for r.
    """
    if abs(r) >= 1.0:
        # Avoid division by zero or log of zero in Fisher transformation
        r = np.sign(r) * 0.9999

    r_squared = r ** 2
    fisher_z = 0.5 * math.log((1 + r) / (1 - r))
    se_z = 1.0 / math.sqrt(n - 3)

    z_lower = fisher_z - 1.96 * se_z
    z_upper = fisher_z + 1.96 * se_z

    ci_lower = (math.exp(2 * z_lower) - 1) / (math.exp(2 * z_lower) + 1)
    ci_upper = (math.exp(2 * z_upper) - 1) / (math.exp(2 * z_upper) + 1)

    return {
        "r": r,
        "r_squared": r_squared,
        "fisher_z": fisher_z,
        "ci_lower_95": ci_lower,
        "ci_upper_95": ci_upper
    }


def calculate_power_spearman(n: int, rho: float, alpha: float = 0.05) -> float:
    """
    Estimate statistical power for detecting a Spearman correlation.

    Uses the Fisher transformation approximation for power calculation.
    H0: rho = 0, H1: rho = rho (specified)

    Args:
        n: Sample size.
        rho: Expected correlation coefficient (effect size).
        alpha: Significance level (default 0.05).

    Returns:
        Estimated statistical power (probability of rejecting H0 when H1 is true).
    """
    if n <= 3:
        return 0.0

    # Fisher transformation
    if abs(rho) >= 1.0:
        rho = np.sign(rho) * 0.9999

    z_rho = 0.5 * math.log((1 + rho) / (1 - rho))
    se = 1.0 / math.sqrt(n - 3)

    # Critical value for two-tailed test under H0 (rho=0 -> z=0)
    z_crit = stats.norm.ppf(1 - alpha / 2)

    # Power calculation: P(Z > z_crit - z_rho/se) + P(Z < -z_crit - z_rho/se)
    # Under H1, the distribution of z is N(z_rho, se^2)
    # We reject H0 if |z| > z_crit
    # Power = P(z > z_crit | H1) + P(z < -z_crit | H1)
    
    # Standardize under H1
    z_val_upper = (z_crit - z_rho) / se
    z_val_lower = (-z_crit - z_rho) / se

    power = (1 - stats.norm.cdf(z_val_upper)) + stats.norm.cdf(z_val_lower)
    
    return max(0.0, min(1.0, power))


def calculate_margin_of_error(n: int, confidence_level: float = 0.95) -> float:
    """
    Calculate the margin of error for a correlation estimate.

    This is half the width of the confidence interval, calculated using
    Fisher's z-transformation.

    Args:
        n: Sample size.
        confidence_level: Confidence level (default 0.95).

    Returns:
        Margin of error (half-width of the CI).
    """
    if n <= 3:
        return float('inf')

    alpha = 1 - confidence_level
    se = 1.0 / math.sqrt(n - 3)
    z_score = stats.norm.ppf(1 - alpha / 2)

    # Margin of error in z-space
    me_z = z_score * se

    # Convert back to r-space (approximate for small me_z)
    # More precise: calculate CI bounds and take half-width
    # But for reporting, we can approximate or calculate exact bounds
    # Let's calculate exact bounds for a hypothetical r=0 to get the "null" margin
    # Or return the z-margin which is symmetric.
    # To be consistent with typical reporting, we return the margin in r-space
    # assuming r=0 (worst case for symmetry).
    
    r_me = (math.exp(2 * me_z) - 1) / (math.exp(2 * me_z) + 1)
    return r_me


def run_power_analysis(
    input_file: Path,
    output_file: Path,
    fiber_col: str = "fiber_intake",
    taxa_col: str = "taxon_abundance",
    alpha: float = 0.05,
    power_target: float = 0.80,
    min_sample_size: int = 30
) -> Dict[str, Any]:
    """
    Perform power analysis on a dataset.

    This function loads data, calculates descriptive statistics, computes
    the observed correlation, and estimates statistical power and margin of error.

    Args:
        input_file: Path to the input TSV/CSV file containing the data.
        output_file: Path to save the power analysis report (TSV).
        fiber_col: Column name for fiber intake.
        taxa_col: Column name for taxa abundance (or a specific taxon to test).
        alpha: Significance level.
        power_target: Target power for sample size estimation (if needed).
        min_sample_size: Minimum sample size required for analysis.

    Returns:
        Dictionary with analysis results.
    """
    logger.info(f"Starting power analysis for {input_file}")

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Load data
    try:
        df = pd.read_csv(input_file, sep='\t') if input_file.suffix == '.tsv' else pd.read_csv(input_file)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

    # Validate columns
    if fiber_col not in df.columns:
        raise ValueError(f"Column '{fiber_col}' not found in {input_file}. Available: {df.columns.tolist()}")
    
    # If taxa_col is a single column
    if taxa_col not in df.columns:
        # If it's a prefix for multiple taxa, we might need to handle that, 
        # but for this function, we assume a specific column or the first numeric one if not found.
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if taxa_col in numeric_cols:
            pass
        else:
            # Try to find a column that looks like abundance
            possible = [c for c in df.columns if 'abundance' in c.lower() or 'count' in c.lower()]
            if possible:
                taxa_col = possible[0]
                logger.warning(f"Using '{taxa_col}' as taxa column based on heuristic.")
            else:
                raise ValueError(f"Could not find taxa column '{taxa_col}' or suitable alternative.")

    # Clean data
    data_fiber = df[fiber_col].dropna()
    data_taxa = df[taxa_col].dropna()

    # Align indices
    common_idx = data_fiber.index.intersection(data_taxa.index)
    fiber_vals = data_fiber.loc[common_idx]
    taxa_vals = data_taxa.loc[common_idx]

    n = len(fiber_vals)
    logger.info(f"Effective sample size: {n}")

    if n < min_sample_size:
        logger.warning(f"Sample size ({n}) is below minimum ({min_sample_size}). Power estimates may be unreliable.")
    
    # Calculate observed correlation (Spearman)
    if n > 2:
        corr, p_value = stats.spearmanr(fiber_vals, taxa_vals)
        if math.isnan(corr):
            corr = 0.0
            p_value = 1.0
    else:
        corr = 0.0
        p_value = 1.0

    # Calculate metrics
    effect_metrics = calculate_effect_size(corr, n)
    power = calculate_power_spearman(n, abs(corr), alpha)
    margin = calculate_margin_of_error(n)

    # Estimate required sample size for target power (if current power < target)
    required_n = None
    if power < power_target:
        # Simple search for required N
        # Power increases with N. We search from n+1 to a reasonable upper bound.
        for test_n in range(n + 1, 10000):
            p_test = calculate_power_spearman(test_n, abs(corr), alpha)
            if p_test >= power_target:
                required_n = test_n
                break

    # Prepare results
    results = {
        "metric": f"Correlation({fiber_col}, {taxa_col})",
        "sample_size": n,
        "observed_rho": corr,
        "p_value": p_value,
        "r_squared": effect_metrics["r_squared"],
        "fisher_z": effect_metrics["fisher_z"],
        "ci_lower_95": effect_metrics["ci_lower_95"],
        "ci_upper_95": effect_metrics["ci_upper_95"],
        "statistical_power": power,
        "margin_of_error_95": margin,
        "alpha": alpha,
        "target_power": power_target,
        "required_n_for_target": required_n if required_n else "N/A (power sufficient or rho=0)"
    }

    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_results = pd.DataFrame([results])
    
    # Format floats for readability
    float_cols = ["observed_rho", "p_value", "r_squared", "fisher_z", "ci_lower_95", "ci_upper_95", "statistical_power", "margin_of_error_95"]
    for col in float_cols:
        if col in df_results.columns:
            df_results[col] = df_results[col].map(lambda x: f"{x:.4f}" if isinstance(x, float) else x)

    df_results.to_csv(output_file, sep='\t', index=False)
    logger.info(f"Power analysis report saved to {output_file}")

    return results


def main():
    """CLI entry point for power analysis."""
    parser = argparse.ArgumentParser(
        description="Calculate statistical power and margin of error for correlation analysis."
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to input data file (TSV or CSV)."
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        required=True,
        help="Path to output report file (TSV)."
    )
    parser.add_argument(
        "--fiber-col",
        type=str,
        default="fiber_intake",
        help="Column name for fiber intake."
    )
    parser.add_argument(
        "--taxa-col",
        type=str,
        default="taxon_abundance",
        help="Column name for taxa abundance."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)."
    )
    parser.add_argument(
        "--min-sample",
        type=int,
        default=30,
        help="Minimum sample size for analysis."
    )

    args = parser.parse_args()

    # Setup logging
    logger = get_logger("power_analysis_cli")
    logger.info(f"Running power analysis on {args.input}")

    try:
        results = run_power_analysis(
            input_file=args.input,
            output_file=args.output,
            fiber_col=args.fiber_col,
            taxa_col=args.taxa_col,
            alpha=args.alpha,
            min_sample_size=args.min_sample
        )
        logger.info(f"Analysis complete. Power: {results['statistical_power']:.4f}")
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
