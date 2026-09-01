"""
Error Propagation Analysis for Photo-Fries Rearrangement Kinetics.

This module calculates and reports error margins for all derived quantities
(lifetimes, correlation coefficients) by propagating uncertainties from raw
measurements through the entire analysis pipeline.

It addresses Marie Curie's concern for stated error margins by ensuring
standard deviations and confidence intervals are reported for every metric.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Import project configuration and utilities
from config import get_processed_data_path, ensure_directories
from utils.seeds import set_seed
from utils.logging import setup_logging

# Configure logger
logger = logging.getLogger(__name__)


def load_kinetic_metrics() -> pd.DataFrame:
    """
    Load the kinetic metrics CSV containing lifetimes and replicate statistics.

    Returns:
        pd.DataFrame: DataFrame with columns including 'lifetime', 'std_dev', 'n_replicates', 'solvent'.
    """
    metrics_path = get_processed_data_path() / "kinetic_metrics.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Kinetic metrics file not found at {metrics_path}")

    df = pd.read_csv(metrics_path)
    logger.info(f"Loaded kinetic metrics from {metrics_path} ({len(df)} rows)")
    return df


def load_correlation_results() -> Dict[str, Any]:
    """
    Load the correlation results JSON containing regression parameters.

    Returns:
        Dict[str, Any]: Dictionary with posterior distributions and statistics.
    """
    corr_path = get_processed_data_path() / "correlation_results.json"
    if not corr_path.exists():
        raise FileNotFoundError(f"Correlation results file not found at {corr_path}")

    with open(corr_path, 'r') as f:
        data = json.load(f)

    logger.info(f"Loaded correlation results from {corr_path}")
    return data


def propagate_lifetime_uncertainty(
    mean_lifetime: float,
    std_dev: float,
    n_replicates: int,
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Propagate uncertainty for a single lifetime measurement based on replicate statistics.

    Calculates the Standard Error of the Mean (SEM) and the Confidence Interval (CI).

    Args:
        mean_lifetime: The mean lifetime value.
        std_dev: The standard deviation of the replicates.
        n_replicates: The number of replicates.
        confidence_level: The confidence level (default 0.95).

    Returns:
        Dict containing 'sem', 'ci_lower', 'ci_upper', 'relative_error'.
    """
    if n_replicates < 2:
        logger.warning(f"n_replicates < 2 for lifetime {mean_lifetime}. Cannot calculate SEM/CI. Using std_dev as error estimate.")
        sem = std_dev
        # If n=1, we cannot calculate t-statistic. Return a placeholder or raise.
        # For safety, we return the std_dev as the error bound but note the limitation.
        ci_half_width = std_dev  # Approximation for n=1
    else:
        # Standard Error of the Mean
        sem = std_dev / np.sqrt(n_replicates)

        # t-statistic for confidence interval
        # Degrees of freedom = n - 1
        df = n_replicates - 1
        t_val = stats.t.ppf((1 + confidence_level) / 2, df)
        ci_half_width = t_val * sem

    ci_lower = mean_lifetime - ci_half_width
    ci_upper = mean_lifetime + ci_half_width
    relative_error = (ci_half_width / mean_lifetime) * 100 if mean_lifetime != 0 else 0.0

    return {
        "sem": float(sem),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "ci_half_width": float(ci_half_width),
        "relative_error_percent": float(relative_error),
        "confidence_level": confidence_level
    }


def propagate_correlation_uncertainty(
    slope: float,
    slope_std: float,
    intercept: float,
    intercept_std: float,
    r_squared: float,
    n_points: int,
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Propagate uncertainty for correlation metrics (slope, intercept, R²).

    Args:
        slope: The regression slope.
        slope_std: The standard deviation (uncertainty) of the slope.
        intercept: The regression intercept.
        intercept_std: The standard deviation (uncertainty) of the intercept.
        r_squared: The R-squared value.
        n_points: Number of data points (solvents).
        confidence_level: Confidence level for intervals.

    Returns:
        Dict containing propagated uncertainties and confidence intervals.
    """
    if n_points < 2:
        logger.warning("n_points < 2 for correlation. Cannot calculate robust CI.")
        df = 0
        t_val = 1.0
    else:
        df = n_points - 2
        t_val = stats.t.ppf((1 + confidence_level) / 2, df)

    # Confidence Intervals for Slope and Intercept
    slope_ci_half = t_val * slope_std
    intercept_ci_half = t_val * intercept_std

    slope_ci_lower = slope - slope_ci_half
    slope_ci_upper = slope + slope_ci_half
    intercept_ci_lower = intercept - intercept_ci_half
    intercept_ci_upper = intercept + intercept_ci_half

    # Relative errors
    rel_slope_err = (slope_ci_half / abs(slope) * 100) if slope != 0 else 0.0
    rel_intercept_err = (intercept_ci_half / abs(intercept) * 100) if intercept != 0 else 0.0

    # Uncertainty in R-squared (approximate using Fisher's Z-transformation logic or bootstrap)
    # For simplicity in this deterministic pass, we propagate the standard error of R²
    # assuming normal approximation for large N, or simply report the CI width based on std.
    # A more rigorous approach would require the full covariance matrix from the Bayesian model.
    # Here we estimate R² uncertainty as: 2 * (1 - R²) / sqrt(N) (rough approximation for small N)
    # Or use the provided std if available. If not, we estimate based on N.
    # Since we only have r_squared and N, let's use a conservative estimate:
    r2_std_est = (1 - r_squared) / np.sqrt(n_points) if n_points > 1 else 0.1
    r2_ci_half = t_val * r2_std_est
    r2_ci_lower = max(0.0, r_squared - r2_ci_half)
    r2_ci_upper = min(1.0, r_squared + r2_ci_half)

    return {
        "slope_ci_lower": float(slope_ci_lower),
        "slope_ci_upper": float(slope_ci_upper),
        "slope_relative_error_percent": float(rel_slope_err),
        "intercept_ci_lower": float(intercept_ci_lower),
        "intercept_ci_upper": float(intercept_ci_upper),
        "intercept_relative_error_percent": float(rel_intercept_err),
        "r_squared_ci_lower": float(r2_ci_lower),
        "r_squared_ci_upper": float(r2_ci_upper),
        "confidence_level": confidence_level,
        "degrees_of_freedom": int(df)
    }


def run_error_propagation_analysis(
    confidence_level: float = 0.95,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main function to run the full error propagation pipeline.

    1. Loads kinetic metrics and calculates propagated lifetime uncertainties.
    2. Loads correlation results and calculates propagated regression uncertainties.
    3. Aggregates all results into a comprehensive report.
    4. Writes the report to a JSON file.

    Args:
        confidence_level: The confidence level for all intervals (default 0.95).
        output_path: Optional path to write the output. Defaults to data/processed/error_propagation_report.json.

    Returns:
        Dict containing the full error propagation report.
    """
    set_seed(42) # Ensure reproducibility if any stochastic elements were added
    ensure_directories()

    if output_path is None:
        output_path = get_processed_data_path() / "error_propagation_report.json"

    logger.info(f"Starting Error Propagation Analysis. Output: {output_path}")

    # 1. Process Kinetic Metrics
    try:
        kinetic_df = load_kinetic_metrics()
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        return {"error": str(e), "status": "failed"}

    propagated_kinetics = []
    for _, row in kinetic_df.iterrows():
        solvent = row.get('solvent', 'unknown')
        mean_tau = row.get('lifetime', 0.0)
        std_tau = row.get('std_dev', 0.0)
        n_rep = row.get('n_replicates', 1)

        result = propagate_lifetime_uncertainty(mean_tau, std_tau, n_rep, confidence_level)
        result['solvent'] = solvent
        result['raw_lifetime'] = float(mean_tau)
        result['raw_std_dev'] = float(std_tau)
        result['n_replicates'] = int(n_rep)
        propagated_kinetics.append(result)

    # 2. Process Correlation Results
    try:
        corr_data = load_correlation_results()
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        return {"error": str(e), "status": "failed"}

    # Extract parameters from correlation results
    # Assuming structure from T030b: posterior_slope, credible_intervals, etc.
    # We need slope, slope_std (or derive from CI), intercept, intercept_std, r_squared, n_points.

    slope = corr_data.get('posterior_slope', {}).get('mean', 0.0)
    # If posterior_slope has 'std', use it. Otherwise estimate from credible interval width.
    if 'std' in corr_data.get('posterior_slope', {}):
        slope_std = corr_data['posterior_slope']['std']
    else:
        # Estimate std from 95% CI width if available
        ci = corr_data.get('credible_intervals', {}).get('slope', [0, 0])
        if len(ci) == 2 and ci[1] > ci[0]:
            # 95% CI approx mean +/- 1.96*std
            slope_std = (ci[1] - ci[0]) / (2 * 1.96)
        else:
            slope_std = 0.0

    intercept = corr_data.get('posterior_intercept', {}).get('mean', 0.0)
    if 'std' in corr_data.get('posterior_intercept', {}):
        intercept_std = corr_data['posterior_intercept']['std']
    else:
        ci = corr_data.get('credible_intervals', {}).get('intercept', [0, 0])
        if len(ci) == 2 and ci[1] > ci[0]:
            intercept_std = (ci[1] - ci[0]) / (2 * 1.96)
        else:
            intercept_std = 0.0

    r_squared = corr_data.get('bayesian_r2', 0.0)
    n_points = len(propagated_kinetics) # Number of solvents

    propagated_corr = propagate_correlation_uncertainty(
        slope, slope_std, intercept, intercept_std, r_squared, n_points, confidence_level
    )
    propagated_corr['raw_slope'] = float(slope)
    propagated_corr['raw_intercept'] = float(intercept)
    propagated_corr['raw_r_squared'] = float(r_squared)
    propagated_corr['n_solvents'] = n_points

    # 3. Compile Final Report
    report = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "confidence_level": confidence_level,
            "pipeline_version": "1.0.0",
            "description": "Error propagation analysis for lifetimes and correlation metrics."
        },
        "kinetic_metrics_propagation": propagated_kinetics,
        "correlation_metrics_propagation": propagated_corr,
        "summary": {
            "total_solvents_analyzed": n_points,
            "average_lifetime_relative_error_percent": np.mean([k['relative_error_percent'] for k in propagated_kinetics]) if propagated_kinetics else 0.0,
            "slope_relative_error_percent": propagated_corr.get('slope_relative_error_percent', 0.0),
            "intercept_relative_error_percent": propagated_corr.get('intercept_relative_error_percent', 0.0)
        }
    }

    # 4. Write Output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Error propagation report written to {output_path}")
    return report


def main():
    """CLI entry point for error propagation analysis."""
    parser = argparse.ArgumentParser(description="Run error propagation analysis for kinetic and correlation metrics.")
    parser.add_argument(
        '--confidence-level',
        type=float,
        default=0.95,
        help="Confidence level for intervals (default: 0.95)"
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help="Output file path (default: data/processed/error_propagation_report.json)"
    )

    args = parser.parse_args()

    setup_logging()

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = None

    try:
        report = run_error_propagation_analysis(
            confidence_level=args.confidence_level,
            output_path=output_path
        )
        if "error" in report:
            logger.error(f"Analysis failed: {report['error']}")
            sys.exit(1)
        else:
            logger.info("Analysis completed successfully.")
            # Print summary to stdout
            print(json.dumps(report['summary'], indent=2))
    except Exception as e:
        logger.exception(f"Unexpected error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
