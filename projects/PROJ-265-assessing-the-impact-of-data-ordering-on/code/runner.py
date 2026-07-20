import argparse
import json
import os
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from config import (
    get_project_root,
    get_results_dir,
    get_bootstrap_seed,
    get_shuffle_seed,
    get_data_seed,
    ensure_directories,
)
from data_generation import generate_ar1
from bootstrap_engine import standard_bootstrap, shuffled_bootstrap, calculate_ci_from_resamples
from metrics import (
    calculate_coverage,
    mcnemar_test_logic,
    calculate_coverage_drop_magnitude,
)
from utils import setup_logging, log_simulation_result

# Constants
DEFAULT_PHI_RANGE = (0.0, 0.9)
DEFAULT_PHI_STEP = 0.1
DEFAULT_SAMPLE_SIZES = [50, 100, 200]
DEFAULT_TRIALS = 1000
DEFAULT_RESAMPLES = 1000
CONFIDENCE_LEVEL = 0.95

def run_single_trial_ordered(
    phi: float, n: int, seed: int, n_resamples: int
) -> Dict[str, Any]:
    """Run a single simulation trial with ordered data."""
    data_seed = get_data_seed() + seed
    bootstrap_seed = get_bootstrap_seed() + seed

    # Generate AR(1) data
    data = generate_ar1(phi=phi, n=n, seed=data_seed)
    true_mean = 0.0  # Theoretical mean of AR(1) with intercept 0

    # Bootstrap
    resamples = standard_bootstrap(data, n_resamples, bootstrap_seed)
    ci = calculate_ci_from_resamples(resamples, CONFIDENCE_LEVEL)

    # Coverage check
    is_covered = ci[0] <= true_mean <= ci[1]

    return {
        "phi": phi,
        "n": n,
        "seed": seed,
        "ordered_coverage": float(is_covered),
        "ci_bounds": [float(ci[0]), float(ci[1])],
        "condition": "ordered",
    }

def run_single_trial_shuffled(
    phi: float, n: int, seed: int, n_resamples: int
) -> Dict[str, Any]:
    """Run a single simulation trial with shuffled data."""
    data_seed = get_data_seed() + seed
    shuffle_seed = get_shuffle_seed() + seed

    # Generate AR(1) data
    data = generate_ar1(phi=phi, n=n, seed=data_seed)
    true_mean = 0.0

    # Shuffle and Bootstrap
    resamples = shuffled_bootstrap(data, n_resamples, shuffle_seed)
    ci = calculate_ci_from_resamples(resamples, CONFIDENCE_LEVEL)

    # Coverage check
    is_covered = ci[0] <= true_mean <= ci[1]

    return {
        "phi": phi,
        "n": n,
        "seed": seed,
        "shuffled_coverage": float(is_covered),
        "ci_bounds": [float(ci[0]), float(ci[1])],
        "condition": "shuffled",
    }

def run_paired_trial(
    phi: float, n: int, seed: int, n_resamples: int
) -> Dict[str, Any]:
    """Run a paired trial (ordered + shuffled) for statistical comparison."""
    data_seed = get_data_seed() + seed
    bootstrap_seed = get_bootstrap_seed() + seed
    shuffle_seed = get_shuffle_seed() + seed

    # Generate AR(1) data
    data = generate_ar1(phi=phi, n=n, seed=data_seed)
    true_mean = 0.0

    # Ordered Bootstrap
    ordered_resamples = standard_bootstrap(data, n_resamples, bootstrap_seed)
    ordered_ci = calculate_ci_from_resamples(ordered_resamples, CONFIDENCE_LEVEL)
    ordered_covered = int(ordered_ci[0] <= true_mean <= ordered_ci[1])

    # Shuffled Bootstrap
    shuffled_resamples = shuffled_bootstrap(data, n_resamples, shuffle_seed)
    shuffled_ci = calculate_ci_from_resamples(shuffled_resamples, CONFIDENCE_LEVEL)
    shuffled_covered = int(shuffled_ci[0] <= true_mean <= shuffled_ci[1])

    # McNemar's Test Logic
    # Contingency table:
    #               Shuffled Covered
    #               Yes     No
    # Ordered Yes    a       b
    #       No       c       d
    # We only care about discordant pairs (b and c) for McNemar's.
    # Since we run many trials, we aggregate counts.
    # For a single trial, the "counts" are 0 or 1.
    # However, McNemar's test requires a contingency table of counts over trials.
    # This function returns the single trial outcome to be aggregated later.

    return {
        "phi": phi,
        "n": n,
        "seed": seed,
        "ordered_covered": ordered_covered,
        "shuffled_covered": shuffled_covered,
        "ordered_ci_bounds": [float(ordered_ci[0]), float(ordered_ci[1])],
        "shuffled_ci_bounds": [float(shuffled_ci[0]), float(shuffled_ci[1])],
        "diff": float(ordered_covered - shuffled_covered),
        "condition": "paired",
    }

def run_paired_simulation_batch(
    phi: float, n: int, trials: int, n_resamples: int
) -> List[Dict[str, Any]]:
    """Run a batch of paired trials for a specific phi and n."""
    results = []
    seeds = list(range(trials))

    for seed in seeds:
        trial_result = run_paired_trial(phi, n, seed, n_resamples)
        results.append(trial_result)

    return results

def aggregate_batch_results(batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate a batch of paired results into coverage metrics and p-value."""
    if not batch_results:
        return {}

    phi = batch_results[0]["phi"]
    n = batch_results[0]["n"]

    ordered_covered_count = sum(r["ordered_covered"] for r in batch_results)
    shuffled_covered_count = sum(r["shuffled_covered"] for r in batch_results)

    ordered_coverage = ordered_covered_count / len(batch_results)
    shuffled_coverage = shuffled_covered_count / len(batch_results)

    # Prepare contingency table for McNemar's test
    # We need counts of:
    # a: Ordered Yes, Shuffled Yes
    # b: Ordered Yes, Shuffled No
    # c: Ordered No, Shuffled Yes
    # d: Ordered No, Shuffled No
    a = b = c = d = 0
    for r in batch_results:
        o = r["ordered_covered"]
        s = r["shuffled_covered"]
        if o == 1 and s == 1:
            a += 1
        elif o == 1 and s == 0:
            b += 1
        elif o == 0 and s == 1:
            c += 1
        else:
            d += 1

    # Perform McNemar's test
    # Using statsmodels.stats.contingency_tables.mcnemar
    from statsmodels.stats.contingency_tables import mcnemar

    table = np.array([[a, b], [c, d]])
    try:
        result = mcnemar(table, exact=True)
        p_value = float(result.pvalue)
    except Exception:
        # Fallback to asymptotic if exact fails (e.g., large numbers)
        try:
            result = mcnemar(table, exact=False)
            p_value = float(result.pvalue)
        except Exception:
            p_value = 1.0

    diff = ordered_coverage - shuffled_coverage

    return {
        "phi": phi,
        "n": n,
        "ordered_coverage": ordered_coverage,
        "shuffled_coverage": shuffled_coverage,
        "diff": diff,
        "p_value": p_value,
        "condition": "paired",
        "contingency_table": {"a": a, "b": b, "c": c, "d": d},
    }

def run_full_batch_paired(
    phi_range: tuple,
    phi_step: float,
    sample_sizes: List[int],
    trials: int,
    n_resamples: int,
) -> List[Dict[str, Any]]:
    """Run the full simulation batch for all phi and n combinations."""
    all_results = []
    phis = np.arange(phi_range[0], phi_range[1] + 1e-9, phi_step)

    for phi in phis:
        for n in sample_sizes:
            logging.info(f"Running batch for phi={phi:.1f}, n={n}")
            batch = run_paired_simulation_batch(phi, n, trials, n_resamples)
            aggregated = aggregate_batch_results(batch)
            all_results.append(aggregated)

    return all_results

def save_results_to_json(results: List[Dict[str, Any]], filepath: str):
    """Save simulation results to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(results, f, indent=2)
    logging.info(f"Results saved to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Run bootstrap simulation")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full simulation batch (synthetic only)",
    )
    parser.add_argument(
        "--phi",
        type=float,
        default=None,
        help="Specific phi value to run (default: range 0.0 to 0.9)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Specific sample size to run (default: 50, 100, 200)",
    )
    parser.add_argument(
        "--resamples",
        type=int,
        default=DEFAULT_RESAMPLES,
        help="Number of bootstrap resamples",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=DEFAULT_TRIALS,
        help="Number of trials per configuration",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Base seed for reproducibility",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Initialize project directories",
    )

    args = parser.parse_args()

    if args.setup:
        ensure_directories()
        logging.info("Directories initialized.")
        return

    setup_logging()
    ensure_directories()

    start_time = time.time()

    if args.full:
        logging.info("Running full simulation batch (Synthetic Only)...")
        phis = (
            np.arange(DEFAULT_PHI_RANGE[0], DEFAULT_PHI_RANGE[1] + 1e-9, DEFAULT_PHI_STEP)
            if args.phi is None
            else [args.phi]
        )
        sample_sizes = (
            DEFAULT_SAMPLE_SIZES if args.n is None else [args.n]
        )

        results = run_full_batch_paired(
            phi_range=(phis[0], phis[-1]),
            phi_step=DEFAULT_PHI_STEP,
            sample_sizes=sample_sizes,
            trials=args.trials,
            n_resamples=args.resamples,
        )

        results_dir = get_results_dir()
        log_path = os.path.join(results_dir, "simulation_logs.json")
        save_results_to_json(results, log_path)

        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"Full simulation completed in {duration:.2f} seconds.")
        logging.info(f"Results written to {log_path}")

    else:
        # Single trial mode for debugging
        logging.warning("Running single trial mode. Use --full for batch.")
        phi = args.phi if args.phi is not None else 0.8
        n = args.n if args.n is not None else 100
        seed = args.seed if args.seed is not None else 42

        result = run_paired_trial(phi, n, seed, args.resamples)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
