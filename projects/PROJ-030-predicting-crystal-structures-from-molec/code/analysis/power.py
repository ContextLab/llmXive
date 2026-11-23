"""
Power analysis module for determining target sample size.

This module calculates the required sample size for the crystal structure
prediction study based on the actual dataset size and desired effect size.
It adheres to the constraint of NOT modifying static config.py, instead
writing dynamic results to data/results/power_analysis.json.
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from scipy.stats import chi2
import pandas as pd

# Import from local project modules
from logging_config import get_logger, log_event
from config import get_path_absolute, ensure_directory

logger = get_logger(__name__)

# Constants for power analysis
DEFAULT_EFFECT_SIZE_W = 0.15  # Cohen's w for small-to-medium effect
DEFAULT_POWER = 0.80          # Desired statistical power
DEFAULT_ALPHA = 0.05          # Significance level

def calculate_sample_size(
    actual_dataset_size: int,
    effect_size_w: float = DEFAULT_EFFECT_SIZE_W,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    num_groups: int = 10  # Approximate number of space group categories
) -> Dict[str, Any]:
    """
    Calculate target sample size based on actual dataset size and statistical parameters.

    Args:
        actual_dataset_size: The number of samples in the actual dataset (from T013).
        effect_size_w: Cohen's w effect size (default 0.15).
        power: Desired statistical power (default 0.80).
        alpha: Significance level (default 0.05).
        num_groups: Number of groups/categories for the chi-squared test.

    Returns:
        Dictionary containing power analysis results.
    """
    logger.info(f"Calculating power analysis for dataset size: {actual_dataset_size}")
    logger.info(f"Parameters: w={effect_size_w}, power={power}, alpha={alpha}, groups={num_groups}")

    # Degrees of freedom for chi-squared test
    df = num_groups - 1

    # Calculate non-centrality parameter for desired power
    # We use a simplified approach: required N = (lambda / effect_size_w^2)
    # where lambda is the non-centrality parameter for the desired power.

    # For chi-squared test, the non-centrality parameter lambda is related to
    # power and effect size. We approximate using standard tables or calculation.

    # Using the approximation: lambda = (Z_{1-alpha} + Z_{power})^2 for 1df,
    # but for multiple df we use the relationship: lambda = N * effect_size_w^2

    # Standard normal quantiles
    from scipy.stats import norm
    z_alpha = norm.ppf(1 - alpha)
    z_power = norm.ppf(power)

    # Approximate non-centrality parameter needed
    # For chi-squared with df > 1, this is a simplified approximation
    lambda_needed = (z_alpha + z_power) ** 2 * df / 2.0

    # Calculate required sample size
    required_n = int(lambda_needed / (effect_size_w ** 2))

    # Ensure we don't request more than available
    target_sample_size = min(required_n, actual_dataset_size)

    # Calculate achieved power with actual dataset size
    # lambda_achieved = actual_dataset_size * effect_size_w^2
    lambda_achieved = actual_dataset_size * (effect_size_w ** 2)
    # Power is the probability that chi2(df, lambda) > chi2.ppf(1-alpha, df)
    critical_value = chi2.ppf(1 - alpha, df)
    achieved_power = 1 - chi2.cdf(critical_value, df, lambda_achieved)

    results = {
        "actual_dataset_size": actual_dataset_size,
        "target_sample_size": target_sample_size,
        "effect_size_w": effect_size_w,
        "desired_power": power,
        "alpha": alpha,
        "num_groups": num_groups,
        "degrees_of_freedom": df,
        "required_n_calculation": required_n,
        "achieved_power_with_actual": float(achieved_power),
        "sufficient_for_analysis": achieved_power >= power,
        "notes": [
            f"Dataset size {actual_dataset_size} {'exceeds' if actual_dataset_size >= required_n else 'is below'} required N of {required_n}",
            f"Achieved power with actual dataset: {achieved_power:.4f} (target: {power})"
        ]
    }

    log_event(logger, "POWER_ANALYSIS_COMPLETE", results)
    return results

def run_power_analysis(
    dataset_path: Optional[str] = None,
    output_path: Optional[str] = None,
    effect_size_w: float = DEFAULT_EFFECT_SIZE_W,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    num_groups: int = 10
) -> Dict[str, Any]:
    """
    Run power analysis on the dataset and save results.

    Args:
        dataset_path: Path to the processed dataset CSV (from T013).
        output_path: Path to write the power analysis JSON output.
        effect_size_w: Cohen's w effect size.
        power: Desired statistical power.
        alpha: Significance level.
        num_groups: Number of groups for chi-squared test.

    Returns:
        Dictionary containing the power analysis results.
    """
    # Determine dataset path if not provided
    if dataset_path is None:
        dataset_path = get_path_absolute("data/processed/crystal_dataset.csv")

    # Determine output path if not provided
    if output_path is None:
        output_path = get_path_absolute("data/results/power_analysis.json")

    # Ensure output directory exists
    ensure_directory(output_path)

    logger.info(f"Running power analysis on dataset: {dataset_path}")
    logger.info(f"Output will be written to: {output_path}")

    # Load dataset to get actual size
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    try:
        df = pd.read_csv(dataset_path)
        actual_size = len(df)
        logger.info(f"Loaded dataset with {actual_size} rows")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # Calculate power analysis
    results = calculate_sample_size(
        actual_dataset_size=actual_size,
        effect_size_w=effect_size_w,
        power=power,
        alpha=alpha,
        num_groups=num_groups
    )

    # Add metadata
    results["dataset_path"] = dataset_path
    results["output_path"] = output_path
    results["parameters"] = {
        "effect_size_w": effect_size_w,
        "desired_power": power,
        "alpha": alpha,
        "num_groups": num_groups
    }

    # Save results to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Power analysis results saved to: {output_path}")
    log_event(logger, "POWER_ANALYSIS_SAVED", {"path": output_path, "target_size": results["target_sample_size"]})

    return results

def main():
    """
    Main entry point for power analysis script.
    Parses command-line arguments and runs the analysis.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate target sample size for crystal structure prediction study."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to the processed dataset CSV (default: data/processed/crystal_dataset.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write power analysis JSON (default: data/results/power_analysis.json)"
    )
    parser.add_argument(
        "--effect-size",
        type=float,
        default=DEFAULT_EFFECT_SIZE_W,
        help=f"Cohen's w effect size (default: {DEFAULT_EFFECT_SIZE_W})"
    )
    parser.add_argument(
        "--power",
        type=float,
        default=DEFAULT_POWER,
        help=f"Desired statistical power (default: {DEFAULT_POWER})"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help=f"Significance level (default: {DEFAULT_ALPHA})"
    )
    parser.add_argument(
        "--num-groups",
        type=int,
        default=10,
        help="Number of groups for chi-squared test (default: 10)"
    )

    args = parser.parse_args()

    try:
        results = run_power_analysis(
            dataset_path=args.dataset,
            output_path=args.output,
            effect_size_w=args.effect_size,
            power=args.power,
            alpha=args.alpha,
            num_groups=args.num_groups
        )

        print(json.dumps(results, indent=2))
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()