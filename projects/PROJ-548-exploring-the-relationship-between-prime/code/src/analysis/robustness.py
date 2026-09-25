"""
Robustness and Sensitivity Analysis for Prime Gap Distribution Study.

This module implements a sensitivity analysis loop that sweeps window sizes (W)
to verify the stability of the distributional comparison results (KS statistics)
against the GUE extreme value distribution.

It re-runs the core analysis pipeline (sliding window extraction, normalization,
KS test) for each specified window size and aggregates the results.
"""

import os
import sys
import json
import math
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

# Project imports based on API surface
from src.utils.config import get_global_seed, ensure_directories
from src.analysis.distribution_test import (
    load_primes_gaps,
    extract_maximal_gaps_in_windows,
    normalize_maximal_gaps,
    gue_extreme_value_cdf,
    compute_empirical_cdf,
)
from src.analysis.ks_test_runner import perform_ks_test

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Output configuration
OUTPUT_DIR = Path("code/results")
OUTPUT_FILE = OUTPUT_DIR / "robustness_sweep.json"

# Representative set of window sizes for sensitivity analysis.
# These are chosen to test small, medium, and large scales relative to the
# prime distribution density.
WINDOW_SIZES = [100_000, 500_000, 1_000_000, 2_000_000, 5_000_000]


def ensure_directories() -> None:
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_single_window_analysis(window_size: int, gaps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Run the full distributional analysis for a single window size.

    This function:
    1. Extracts maximal gaps within sliding windows of the specified size.
    2. Normalizes the gaps.
    3. Computes the empirical CDF.
    4. Performs a KS test against the GUE theoretical distribution.

    Args:
        window_size (int): The size of the sliding window (W).
        gaps (List[Dict]): The list of prime gap dictionaries.

    Returns:
        Optional[Dict]: A dictionary containing the results for this window size,
                        or None if the analysis failed (e.g., insufficient data).
    """
    logger.info(f"Running analysis for window size: {window_size}")

    try:
        # 1. Extract Maximal Gaps
        # We assume gaps are sorted by prime_before.
        maximal_gaps = extract_maximal_gaps_in_windows(gaps, window_size)

        if not maximal_gaps:
            logger.warning(f"No maximal gaps found for window size {window_size}. Skipping.")
            return None

        # 2. Normalize Maximal Gaps
        # The normalization factor is log(p)^2, where p is the prime before the gap.
        normalized_gaps = normalize_maximal_gaps(maximal_gaps)

        if not normalized_gaps:
            logger.warning(f"No normalized gaps for window size {window_size}. Skipping.")
            return None

        # 3. Compute Empirical CDF
        # We extract the values for the KS test
        empirical_values = [g['normalized_max_gap'] for g in normalized_gaps]
        if len(empirical_values) < 2:
            logger.warning(f"Insufficient data points ({len(empirical_values)}) for KS test at window size {window_size}.")
            return None

        # 4. Perform KS Test against GUE Extreme Value Distribution
        # We generate a large sample from the theoretical GUE CDF to compare against
        ks_stat, p_val, _ = perform_ks_test(empirical_values, gue_extreme_value_cdf)

        result = {
            "window_size": window_size,
            "ks_statistic": float(ks_stat),
            "p_value": float(p_val),
            "num_windows": len(maximal_gaps),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        logger.info(f"Window {window_size}: KS={ks_stat:.4f}, p={p_val:.4f}, n={len(maximal_gaps)}")
        return result

    except Exception as e:
        logger.error(f"Error during analysis for window size {window_size}: {e}", exc_info=True)
        return None


def run_pipeline() -> Dict[str, Any]:
    """
    Execute the sensitivity analysis loop.

    Loads the pre-computed prime gaps, iterates through the defined window sizes,
    runs the analysis for each, and saves the aggregated results.

    Returns:
        Dict[str, Any]: The full results dictionary.
    """
    ensure_directories()
    ensure_directories() # Ensure results dir exists

    # Load pre-computed gaps
    # The path is relative to the project root as per spec conventions
    gaps_file = Path("code/data/processed/raw_gaps.csv")
    if not gaps_file.exists():
        raise FileNotFoundError(
            f"Required input file not found: {gaps_file}. "
            "Please run src/data/generate_primes.py first."
        )

    logger.info(f"Loading gaps from {gaps_file}")
    gaps = load_primes_gaps(gaps_file)
    logger.info(f"Loaded {len(gaps)} gaps.")

    results = []

    for w in WINDOW_SIZES:
        res = run_single_window_analysis(w, gaps)
        if res:
            results.append(res)

    # Sort results by window size for readability
    results.sort(key=lambda x: x['window_size'])

    # Write results to JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Robustness sweep complete. Results written to {OUTPUT_FILE}")

    return {
        "status": "success",
        "results": results,
        "output_file": str(OUTPUT_FILE)
    }


def main() -> None:
    """Entry point for the script."""
    try:
        result = run_pipeline()
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
