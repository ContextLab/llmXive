"""
Convergence Check Module for Confidence Interval Robustness Simulation.

This module verifies that the simulation has run for a sufficient number of seeds
to ensure the standard error of the coverage estimate is below a specified threshold
(default: 0.5%).

It reads the aggregated coverage results, calculates the standard error for each
unique condition (dataset, epsilon, noise_type, statistic), and determines if
additional simulation seeds are required.
"""

import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add project root to path for imports if running as script
if "code" not in sys.path:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

import config
from analysis.progress_logger import SimulationProgressLogger
from analysis.logging_config import setup_simulation_logger


def calculate_coverage_se(covered: pd.Series) -> float:
    """
    Calculate the standard error of the coverage proportion.

    Coverage is a binary outcome (0 or 1). The standard error of a proportion p
    is sqrt(p * (1 - p) / n).

    Args:
        covered: A Series of boolean or 0/1 values indicating if the CI covered the truth.

    Returns:
        The standard error of the coverage estimate.
    """
    n = len(covered)
    if n == 0:
        return float('inf')

    p = covered.mean()
    if p == 0 or p == 1:
        # If coverage is perfect or zero, SE is 0 mathematically, but practically
        # we might want to treat it as a boundary case.
        # Standard formula: sqrt(p(1-p)/n) -> 0
        return 0.0

    se = np.sqrt(p * (1 - p) / n)
    return se


def check_convergence(
    coverage_df: pd.DataFrame,
    target_se: float = 0.005,
    grouping_cols: Optional[List[str]] = None
) -> Tuple[bool, Dict[str, Dict[str, float]]]:
    """
    Check if the simulation has converged for all conditions.

    Args:
        coverage_df: DataFrame containing coverage results (must include 'covered' column).
        target_se: The target standard error threshold (default 0.005 for 0.5%).
        grouping_cols: Columns to group by for calculating coverage stats.
                       Defaults to ['dataset', 'epsilon', 'noise_type', 'statistic'].

    Returns:
        A tuple (is_converged, details) where:
            - is_converged: True if all groups have SE < target_se.
            - details: A dictionary mapping group keys to their SE and count.
    """
    if grouping_cols is None:
        grouping_cols = ['dataset', 'epsilon', 'noise_type', 'statistic']

    # Ensure 'covered' is numeric (0/1)
    df = coverage_df.copy()
    if df['covered'].dtype == bool:
        df['covered'] = df['covered'].astype(int)

    # Group by condition
    grouped = df.groupby(grouping_cols)
    results = {}
    all_converged = True

    for name, group in grouped:
        key = tuple(name) if isinstance(name, tuple) else (name,)
        se = calculate_coverage_se(group['covered'])
        count = len(group)
        coverage_rate = group['covered'].mean()

        is_ok = se < target_se
        if not is_ok:
            all_converged = False

        results[str(key)] = {
            'se': se,
            'count': count,
            'coverage_rate': coverage_rate,
            'target_se': target_se,
            'converged': is_ok
        }

    return all_converged, results


def generate_convergence_report(
    convergence_results: Dict[str, Dict[str, float]],
    output_path: Path
) -> None:
    """
    Generate a JSON report of the convergence check results.

    Args:
        convergence_results: The dictionary returned by check_convergence.
        output_path: Path to write the JSON report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(convergence_results, f, indent=2)


def main() -> int:
    """
    Main entry point for the convergence check script.

    Reads `artifacts/coverage_results.csv`, checks convergence, and outputs
    a report to `artifacts/convergence_report.json`.

    Returns:
        Exit code: 0 if converged, 1 if not converged (or error).
    """
    logger = setup_simulation_logger("convergence_check")
    logger.info("Starting convergence check analysis.")

    # Load results
    results_path = Path(config.ARTIFACTS_DIR) / "coverage_results.csv"
    if not results_path.exists():
        logger.error(f"Results file not found: {results_path}")
        return 1

    try:
        df = pd.read_csv(results_path)
        logger.info(f"Loaded {len(df)} coverage records from {results_path}")
    except Exception as e:
        logger.error(f"Failed to load results: {e}")
        return 1

    # Required columns
    required_cols = ['covered']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column in results: {col}")
            return 1

    # Define grouping columns based on task requirements
    grouping_cols = ['dataset', 'epsilon', 'noise_type', 'statistic']
    for col in grouping_cols:
        if col not in df.columns:
            # If a grouping column is missing, we might need to adjust or fail.
            # For now, we assume the main pipeline produces these.
            logger.warning(f"Grouping column '{col}' not found. Attempting to proceed without it.")
            grouping_cols.remove(col)

    # Get target SE from config if available, else default 0.005
    target_se = getattr(config, 'CONVERGENCE_TARGET_SE', 0.005)
    logger.info(f"Checking convergence with target SE: {target_se}")

    is_converged, details = check_convergence(df, target_se=target_se, grouping_cols=grouping_cols)

    # Generate report
    report_path = Path(config.ARTIFACTS_DIR) / "convergence_report.json"
    generate_convergence_report(details, report_path)

    if is_converged:
        logger.info("Convergence check PASSED. All conditions meet the SE target.")
        return 0
    else:
        logger.warning("Convergence check FAILED. Some conditions require more seeds.")
        # Log specific failures
        failed_count = sum(1 for v in details.values() if not v['converged'])
        logger.warning(f"{failed_count} conditions did not converge.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
