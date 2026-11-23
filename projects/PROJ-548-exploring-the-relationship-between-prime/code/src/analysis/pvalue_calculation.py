"""
P-value calculation for observed distributional alignment against the Cramér null distribution.

This module implements the final statistical validation step for User Story 2.
It calculates the p-value by comparing the observed KS statistic (from T022)
against the distribution of KS statistics generated from the Cramér model (from T023).

Addresses: FR-005, SC-001
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
OBSERVED_KS_FILE = project_root / "results" / "ks_test_results.json"
CRAMER_NULL_FILE = project_root / "results" / "cramer_null_distribution.json"
PVALUE_OUTPUT_FILE = project_root / "results" / "pvalue_results.json"


def load_observed_ks_statistic(filepath: Path) -> float:
    """
    Load the observed KS statistic from the KS test results file.

    Args:
        filepath: Path to ks_test_results.json

    Returns:
        The observed KS statistic value.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If the expected key is missing.
        ValueError: If the value cannot be parsed as a float.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Observed KS results file not found: {filepath}")

    with open(filepath, 'r') as f:
        data = json.load(f)

    if 'ks_statistic' not in data:
        raise KeyError(f"Key 'ks_statistic' not found in {filepath}")

    try:
        ks_stat = float(data['ks_statistic'])
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid value for 'ks_statistic': {data['ks_statistic']}") from e

    logger.info(f"Loaded observed KS statistic: {ks_stat}")
    return ks_stat


def load_cramer_null_distribution(filepath: Path) -> list:
    """
    Load the Cramér null distribution of KS statistics.

    Args:
        filepath: Path to cramer_null_distribution.json

    Returns:
        List of KS statistics from the Cramér model simulations.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If the expected key is missing.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Cramér null distribution file not found: {filepath}")

    with open(filepath, 'r') as f:
        data = json.load(f)

    if 'null_ks_statistics' not in data:
        raise KeyError(f"Key 'null_ks_statistics' not found in {filepath}")

    null_stats = data['null_ks_statistics']
    if not isinstance(null_stats, list) or len(null_stats) == 0:
        raise ValueError(f"Null distribution is empty or invalid in {filepath}")

    logger.info(f"Loaded {len(null_stats)} samples from Cramér null distribution")
    return null_stats


def calculate_pvalue(observed_ks: float, null_distribution: list) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate the p-value for the observed KS statistic against the Cramér null distribution.

    The p-value is defined as the proportion of null KS statistics that are greater than
    or equal to the observed KS statistic.

    P-value = (Count(null_ks >= observed_ks) + 1) / (N + 1)
    (Using the standard unbiased estimator with +1 correction)

    Args:
        observed_ks: The observed KS statistic from real prime data.
        null_distribution: List of KS statistics from Cramér model simulations.

    Returns:
        Tuple containing:
            - p_value (float): The calculated p-value.
            - stats (dict): Summary statistics of the calculation.
    """
    n = len(null_distribution)
    count_ge = sum(1 for val in null_distribution if val >= observed_ks)

    # Calculate p-value with +1 correction to avoid p=0
    p_value = (count_ge + 1) / (n + 1)

    stats = {
        "observed_ks": observed_ks,
        "null_sample_size": n,
        "count_ge_observed": count_ge,
        "null_mean": sum(null_distribution) / n,
        "null_std": (sum((x - sum(null_distribution)/n)**2 for x in null_distribution) / n) ** 0.5,
        "null_min": min(null_distribution),
        "null_max": max(null_distribution)
    }

    logger.info(f"Calculated p-value: {p_value:.6f} (count >= {observed_ks} was {count_ge} out of {n})")
    return p_value, stats


def run_pipeline() -> Dict[str, Any]:
    """
    Execute the full p-value calculation pipeline.

    1. Loads observed KS statistic from results/ks_test_results.json
    2. Loads Cramér null distribution from results/cramer_null_distribution.json
    3. Calculates p-value
    4. Writes results to results/pvalue_results.json

    Returns:
        Dictionary containing the final results and metadata.
    """
    ensure_directories()

    logger.info("Starting P-value calculation pipeline...")

    try:
        # Load inputs
        observed_ks = load_observed_ks_statistic(OBSERVED_KS_FILE)
        null_dist = load_cramer_null_distribution(CRAMER_NULL_FILE)

        # Calculate p-value
        p_value, calc_stats = calculate_pvalue(observed_ks, null_dist)

        # Prepare output
        result = {
            "p_value": p_value,
            "methodology": "Monte Carlo p-value estimation against Cramér null distribution",
            "reference_observed_ks_file": str(OBSERVED_KS_FILE),
            "reference_null_dist_file": str(CRAMER_NULL_FILE),
            "calculation_stats": calc_stats
        }

        # Write output
        with open(PVALUE_OUTPUT_FILE, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"P-value calculation complete. Results written to {PVALUE_OUTPUT_FILE}")
        return result

    except Exception as e:
        logger.error(f"P-value calculation failed: {e}", exc_info=True)
        raise


def main():
    """Entry point for command-line execution."""
    try:
        result = run_pipeline()
        print(f"Success. P-value: {result['p_value']:.6f}")
        sys.exit(0)
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()