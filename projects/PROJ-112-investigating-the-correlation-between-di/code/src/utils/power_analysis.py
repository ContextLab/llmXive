"""
Statistical Power Analysis Module for Dietary Fiber-Gut Microbiome Study.

This module provides functions to calculate statistical power for Spearman correlation,
margin of error, and effect size estimation. It is designed to be CPU-tractable and
operates on real data provided via CSV/TSV files.
"""

import os
import math
import argparse
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import pandas as pd
import numpy as np

# Import logger from the project's existing utility module
from src.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_effect_size(r: float) -> float:
    """
    Calculate Cohen's q effect size for correlation differences or simply return r.
    For a single correlation, we often treat r itself as the effect size metric,
    but Cohen's q is used for comparing two correlations. Here we return r as the primary metric.

    Args:
        r (float): Pearson or Spearman correlation coefficient.

    Returns:
        float: The correlation coefficient (effect size).
    """
    return r


def calculate_power_spearman(n: int, rho: float, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate statistical power for a Spearman rank correlation test.
    Uses the Fisher transformation approximation for the power calculation.

    Formula:
    1. Transform rho to Fisher's z: z_rho = 0.5 * ln((1+rho)/(1-rho))
    2. Standard error of z: se_z = 1 / sqrt(n - 3)
    3. Critical z value for alpha (two-tailed): z_crit = norm.ppf(1 - alpha/2)
    4. Power = Phi( z_rho * sqrt(n-3) - z_crit ) + Phi( -z_rho * sqrt(n-3) - z_crit )
       (Approximation for two-sided test)

    Args:
        n (int): Sample size.
        rho (float): Expected correlation coefficient (Spearman).
        alpha (float): Significance level (default 0.05).

    Returns:
        Tuple[float, float]: (power, z_statistic)
    """
    if n <= 3:
        return 0.0, 0.0

    # Avoid division by zero or log of negative/zero if rho is exactly +/- 1
    if abs(rho) >= 1.0:
        # Perfect correlation, power is effectively 1 for any n > 3
        return 1.0, float('inf')

    # Fisher transformation
    z_rho = 0.5 * math.log((1 + rho) / (1 - rho))

    # Standard error of the transformed correlation
    se_z = 1.0 / math.sqrt(n - 3)

    # Critical value for two-tailed test
    # Using math.erfcinv for inverse error function to approximate norm.ppf
    # norm.ppf(1 - alpha/2)
    z_crit = math.sqrt(2) * math.erfcinv(alpha)

    # Calculate power
    # Power = P(Z > z_crit - delta) + P(Z < -z_crit - delta)
    # where delta = z_rho / se_z = z_rho * sqrt(n-3)
    delta = z_rho / se_z

    # Using cumulative distribution function approximation via error function
    # Phi(x) = 0.5 * erfc(-x / sqrt(2))
    def phi(x):
        return 0.5 * math.erfc(-x / math.sqrt(2))

    power = phi(delta - z_crit) + phi(-delta - z_crit)

    return max(0.0, min(1.0, power)), delta


def calculate_margin_of_error(n: int, rho: float, alpha: float = 0.05) -> float:
    """
    Calculate the Margin of Error (MoE) for the correlation coefficient.
    MoE is defined as the half-width of the confidence interval.

    Args:
        n (int): Sample size.
        rho (float): Correlation coefficient.
        alpha (float): Significance level.

    Returns:
        float: Margin of Error.
    """
    if n <= 3 or abs(rho) >= 1.0:
        return float('inf')

    z_rho = 0.5 * math.log((1 + rho) / (1 - rho))
    se_z = 1.0 / math.sqrt(n - 3)
    z_crit = math.sqrt(2) * math.erfcinv(alpha)

    # Confidence interval in z-space
    z_lower = z_rho - z_crit * se_z
    z_upper = z_rho + z_crit * se_z

    # Transform back to r-space
    r_lower = (math.exp(2 * z_lower) - 1) / (math.exp(2 * z_lower) + 1)
    r_upper = (math.exp(2 * z_upper) - 1) / (math.exp(2 * z_upper) + 1)

    # MoE is the max distance from rho to the bounds
    moe = max(abs(r_upper - rho), abs(r_lower - rho))
    return moe


def run_power_analysis(
    input_file: str,
    output_file: str,
    correlation_col: str = "spearman_rho",
    sample_size_col: str = "sample_size",
    alpha: float = 0.05,
    target_power: float = 0.80
) -> Dict[str, Any]:
    """
    Run power analysis on a dataset containing correlation results and sample sizes.
    Calculates power and margin of error for each row.

    Args:
        input_file (str): Path to input TSV/CSV file.
        output_file (str): Path to output TSV file.
        correlation_col (str): Column name for correlation coefficients.
        sample_size_col (str): Column name for sample sizes.
        alpha (float): Significance level.
        target_power (float): Target power threshold for reporting.

    Returns:
        Dict[str, Any]: Summary statistics of the power analysis.
    """
    logger.info(f"Loading data from {input_file}")
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    df = pd.read_csv(input_file, sep='\t')

    if correlation_col not in df.columns:
        raise ValueError(f"Column '{correlation_col}' not found in input file.")
    if sample_size_col not in df.columns:
        raise ValueError(f"Column '{sample_size_col}' not found in input file.")

    logger.info(f"Calculating power and margin of error for {len(df)} rows")

    results = []
    for idx, row in df.iterrows():
        n = int(row[sample_size_col])
        r = float(row[correlation_col])

        power, _ = calculate_power_spearman(n, r, alpha)
        moe = calculate_margin_of_error(n, r, alpha)

        results.append({
            "row_index": idx,
            "sample_size": n,
            "correlation": r,
            "power": power,
            "margin_of_error": moe,
            "is_powered": power >= target_power
        })

    results_df = pd.DataFrame(results)

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(output_file, sep='\t', index=False)
    logger.info(f"Power analysis results saved to {output_file}")

    # Summary stats
    summary = {
        "total_rows": len(df),
        "powered_rows": int((results_df["is_powered"] == True).sum()),
        "mean_power": float(results_df["power"].mean()),
        "min_power": float(results_df["power"].min()),
        "max_power": float(results_df["power"].max()),
        "mean_moe": float(results_df["margin_of_error"].mean())
    }

    logger.info(f"Summary: Mean Power={summary['mean_power']:.3f}, Powered Rows={summary['powered_rows']}/{summary['total_rows']}")
    return summary


def main():
    """
    CLI entry point for running power analysis on a dataset.
    Expected usage:
    python -m src.utils.power_analysis --input data/processed/results/spearman_correlations.tsv --output data/processed/results/power_analysis_report.tsv
    """
    parser = argparse.ArgumentParser(description="Calculate statistical power and margin of error.")
    parser.add_argument("--input", type=str, required=True, help="Path to input TSV file with correlation results.")
    parser.add_argument("--output", type=str, required=True, help="Path to output TSV file for power analysis report.")
    parser.add_argument("--correlation-col", type=str, default="spearman_rho", help="Column name for correlation coefficients.")
    parser.add_argument("--sample-size-col", type=str, default="sample_size", help="Column name for sample sizes.")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level.")
    parser.add_argument("--target-power", type=float, default=0.80, help="Target power threshold.")

    args = parser.parse_args()

    try:
        summary = run_power_analysis(
            input_file=args.input,
            output_file=args.output,
            correlation_col=args.correlation_col,
            sample_size_col=args.sample_size_col,
            alpha=args.alpha,
            target_power=args.target_power
        )
        print(f"Power analysis completed successfully.")
        print(f"Summary: {summary}")
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
