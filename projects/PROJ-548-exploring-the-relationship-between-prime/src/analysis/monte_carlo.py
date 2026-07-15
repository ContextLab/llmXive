"""
Monte Carlo simulation using the Cramér model to generate a null distribution of the KS statistic.

This module implements a Monte Carlo simulation based on the Cramér random model
for prime distribution. It generates synthetic prime-like sequences, computes
normalized maximal gaps, and compares them against the GUE extreme value distribution
using the Kolmogorov-Smirnov (KS) test. The resulting KS statistics form a null
distribution against which the observed KS statistic from real prime data can be
compared.

Dependencies:
    - numpy: For random number generation and statistical operations
    - scipy.stats: For KS test calculation
    - src.analysis.distribution_test: For GUE extreme value CDF and KS test utilities
    - src.utils.seeds: For deterministic seed management
"""

import os
import sys
import json
import math
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

from src.analysis.distribution_test import gue_extreme_value_cdf, compute_empirical_cdf, run_ks_test
from src.utils.seeds import generate_component_seed, get_rng

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Constants from configuration
DEFAULT_NUM_SIMULATIONS = 1000
DEFAULT_WINDOW_SIZE = 10**6
DEFAULT_PRIME_LIMIT = 10**10
OUTPUT_DIR = Path("results")
OUTPUT_FILE = OUTPUT_DIR / "cramer_null_distribution.json"


def generate_cramer_primes(n_primes: int, rng: np.random.Generator, seed: int) -> List[int]:
    """
    Generate a sequence of 'prime-like' numbers using the Cramér random model.

    In the Cramér model, each integer n >= 2 is considered 'prime' with probability
    1/ln(n). This function generates a sequence of such pseudo-primes.

    Args:
        n_primes: Target number of pseudo-primes to generate
        rng: NumPy random generator for reproducibility
        seed: Seed for reproducibility (passed to rng internally)

    Returns:
        List of pseudo-prime integers
    """
    logger.info(f"Generating {n_primes} pseudo-primes using Cramér model with seed {seed}")

    primes = []
    n = 2
    while len(primes) < n_primes:
        # Probability of n being prime in Cramér model is 1/ln(n)
        prob = 1.0 / math.log(n)
        if rng.random() < prob:
            primes.append(n)
        n += 1
        # Safety check to prevent infinite loops
        if n > DEFAULT_PRIME_LIMIT * 2:
            logger.warning(f"Reached limit n={n} before generating {n_primes} primes")
            break

    logger.info(f"Generated {len(primes)} pseudo-primes, last value: {primes[-1] if primes else 'none'}")
    return primes


def compute_cramer_gaps(primes: List[int], window_size: int) -> List[float]:
    """
    Compute normalized maximal gaps from a sequence of pseudo-primes.

    For each window of size `window_size`, find the maximal gap between consecutive
    primes and normalize it by log^2(p) where p is the prime before the gap.

    Args:
        primes: List of pseudo-prime integers
        window_size: Size of sliding window in terms of prime count

    Returns:
        List of normalized maximal gaps
    """
    if len(primes) < 2:
        return []

    normalized_gaps = []

    # Process in windows
    for i in range(len(primes) - window_size):
        window_primes = primes[i:i + window_size]
        if len(window_primes) < 2:
            continue

        # Find maximal gap in this window
        max_gap = 0
        p_before = window_primes[0]
        for j in range(len(window_primes) - 1):
            gap = window_primes[j + 1] - window_primes[j]
            if gap > max_gap:
                max_gap = gap
                p_before = window_primes[j]

        # Normalize by log^2(p)
        if p_before > 1:
            normalized = max_gap / (math.log(p_before) ** 2)
            normalized_gaps.append(normalized)

    logger.info(f"Computed {len(normalized_gaps)} normalized maximal gaps from {len(primes)} pseudo-primes")
    return normalized_gaps


def run_single_simulation(num_primes: int, window_size: int, rng: np.random.Generator, seed: int) -> float:
    """
    Run a single Monte Carlo simulation: generate Cramér primes, compute gaps,
    and return the KS statistic against the GUE extreme value distribution.

    Args:
        num_primes: Number of pseudo-primes to generate
        window_size: Size of sliding window for maximal gap extraction
        rng: NumPy random generator
        seed: Seed for this simulation

    Returns:
        KS statistic comparing empirical gap distribution to GUE extreme value CDF
    """
    # Generate pseudo-primes
    primes = generate_cramer_primes(num_primes, rng, seed)

    if len(primes) < window_size + 1:
        logger.warning(f"Not enough primes ({len(primes)}) for window size {window_size}")
        return float('nan')

    # Compute normalized maximal gaps
    gaps = compute_cramer_gaps(primes, window_size)

    if len(gaps) < 10:  # Need sufficient data for meaningful KS test
        logger.warning(f"Not enough gaps ({len(gaps)}) for KS test")
        return float('nan')

    # Compute empirical CDF
    empirical_cdf = compute_empirical_cdf(gaps)

    # Compute KS statistic against GUE extreme value distribution
    ks_stat, p_value = run_ks_test(gaps, gue_extreme_value_cdf)

    logger.debug(f"Simulation seed {seed}: KS statistic = {ks_stat:.6f}, p-value = {p_value:.6f}")
    return ks_stat


def run_monte_carlo_simulation(
    num_simulations: int = DEFAULT_NUM_SIMULATIONS,
    num_primes: int = 100000,
    window_size: int = DEFAULT_WINDOW_SIZE,
    master_seed: Optional[int] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full Monte Carlo simulation to generate a null distribution of KS statistics.

    This function:
    1. Initializes a deterministic RNG based on the master seed
    2. Runs multiple simulations of the Cramér model
    3. Computes KS statistics for each simulation
    4. Aggregates results into a null distribution
    5. Saves results to a JSON file

    Args:
        num_simulations: Number of Monte Carlo simulations to run
        num_primes: Number of pseudo-primes per simulation
        window_size: Window size for maximal gap extraction
        master_seed: Master seed for reproducibility (default: from config)
        output_path: Path to save results (default: results/cramer_null_distribution.json)

    Returns:
        Dictionary containing simulation results and statistics
    """
    if output_path is None:
        output_path = OUTPUT_FILE

    logger.info(f"Starting Monte Carlo simulation: {num_simulations} runs, {num_primes} primes each")

    # Initialize RNG
    if master_seed is None:
        master_seed = 42  # Default seed if not specified
    rng = get_rng(master_seed, "monte_carlo")

    # Run simulations
    ks_statistics = []
    for i in range(num_simulations):
        # Generate a unique seed for each simulation
        sim_seed = generate_component_seed(master_seed, "simulation", i)
        ks_stat = run_single_simulation(num_primes, window_size, rng, sim_seed)

        if not math.isnan(ks_stat):
            ks_statistics.append(ks_stat)

        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{num_simulations} simulations")

    if len(ks_statistics) == 0:
        raise RuntimeError("No valid KS statistics generated from simulations")

    # Compute statistics of the null distribution
    mean_ks = float(np.mean(ks_statistics))
    std_ks = float(np.std(ks_statistics))
    min_ks = float(np.min(ks_statistics))
    max_ks = float(np.max(ks_statistics))
    median_ks = float(np.median(ks_statistics))

    # Create result dictionary
    results = {
        "parameters": {
            "num_simulations": len(ks_statistics),
            "num_primes_per_simulation": num_primes,
            "window_size": window_size,
            "master_seed": master_seed
        },
        "statistics": {
            "mean_ks_statistic": mean_ks,
            "std_ks_statistic": std_ks,
            "min_ks_statistic": min_ks,
            "max_ks_statistic": max_ks,
            "median_ks_statistic": median_ks
        },
        "null_distribution": ks_statistics,
        "description": "KS statistics from Cramér model Monte Carlo simulations against GUE extreme value distribution"
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved null distribution to {output_path}")
    logger.info(f"Null distribution: mean={mean_ks:.6f}, std={std_ks:.6f}, range=[{min_ks:.6f}, {max_ks:.6f}]")

    return results


def main():
    """Main entry point for the Monte Carlo simulation."""
    import argparse

    parser = argparse.ArgumentParser(description="Monte Carlo simulation for Cramér model KS statistic null distribution")
    parser.add_argument("--simulations", type=int, default=DEFAULT_NUM_SIMULATIONS,
                        help=f"Number of simulations (default: {DEFAULT_NUM_SIMULATIONS})")
    parser.add_argument("--primes", type=int, default=100000,
                        help="Number of pseudo-primes per simulation (default: 100000)")
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW_SIZE,
                        help=f"Window size for gap extraction (default: {DEFAULT_WINDOW_SIZE})")
    parser.add_argument("--seed", type=int, default=None,
                        help="Master seed for reproducibility")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE),
                        help=f"Output file path (default: {OUTPUT_FILE})")

    args = parser.parse_args()

    output_path = Path(args.output)

    try:
        results = run_monte_carlo_simulation(
            num_simulations=args.simulations,
            num_primes=args.primes,
            window_size=args.window,
            master_seed=args.seed,
            output_path=output_path
        )

        print(f"\nMonte Carlo simulation completed successfully.")
        print(f"Generated {len(results['null_distribution'])} KS statistics.")
        print(f"Null distribution: mean={results['statistics']['mean_ks_statistic']:.6f}, "
              f"std={results['statistics']['std_ks_statistic']:.6f}")
        print(f"Results saved to: {output_path}")

    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise


if __name__ == "__main__":
    main()
