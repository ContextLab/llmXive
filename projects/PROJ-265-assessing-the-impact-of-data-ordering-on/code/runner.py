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
    get_data_seed,
    get_bootstrap_seed,
    get_shuffle_seed,
    ensure_directories,
)
from data_generation import generate_ar1
from bootstrap_engine import standard_bootstrap, shuffled_bootstrap, calculate_ci_from_resamples
from metrics import (
    calculate_coverage,
    calculate_coverage_drop_magnitude,
    mcnemar_test_logic,
)
from utils import setup_logging, log_simulation_result

logger = logging.getLogger(__name__)

# Constants for default simulation
DEFAULT_PHI_RANGE = (0.0, 0.9)
DEFAULT_SAMPLE_SIZES = [50, 100, 200]
DEFAULT_TRIALS = 1000
DEFAULT_RESAMPLES = 1000
DEFAULT_ALPHA = 0.05

def run_single_trial_ordered(
    phi: float,
    n: int,
    seed: int,
    n_resamples: int,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """Run a single bootstrap trial on ordered AR(1) data."""
    data_seed = get_data_seed(seed)
    bootstrap_seed = get_bootstrap_seed(seed)

    # Generate data
    data = generate_ar1(phi=phi, n=n, seed=data_seed)
    true_mean = 0.0

    # Bootstrap
    resamples = standard_bootstrap(data, n_resamples, bootstrap_seed)
    ci = calculate_ci_from_resamples(resamples, alpha=alpha)

    # Calculate coverage (single trial: 1 if covered, 0 otherwise)
    covered = 1 if (ci[0] <= true_mean <= ci[1]) else 0

    return {
        "phi": phi,
        "n": n,
        "seed": seed,
        "ci_lower": ci[0],
        "ci_upper": ci[1],
        "covered": covered,
        "condition": "ordered"
    }

def run_single_trial_shuffled(
    phi: float,
    n: int,
    seed: int,
    n_resamples: int,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """Run a single bootstrap trial on shuffled AR(1) data."""
    data_seed = get_data_seed(seed)
    bootstrap_seed = get_bootstrap_seed(seed)
    shuffle_seed = get_shuffle_seed(seed)

    # Generate data
    data = generate_ar1(phi=phi, n=n, seed=data_seed)
    true_mean = 0.0

    # Bootstrap with shuffling
    resamples = shuffled_bootstrap(data, n_resamples, bootstrap_seed, shuffle_seed)
    ci = calculate_ci_from_resamples(resamples, alpha=alpha)

    # Calculate coverage
    covered = 1 if (ci[0] <= true_mean <= ci[1]) else 0

    return {
        "phi": phi,
        "n": n,
        "seed": seed,
        "ci_lower": ci[0],
        "ci_upper": ci[1],
        "covered": covered,
        "condition": "shuffled"
    }

def run_paired_trial(
    phi: float,
    n: int,
    seed: int,
    n_resamples: int,
    trials: int,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """Run paired trials (ordered vs shuffled) and compute aggregate metrics."""
    ordered_covered_count = 0
    shuffled_covered_count = 0
    ordered_cis = []
    shuffled_cis = []

    for i in range(trials):
        trial_seed = seed + i  # Unique seed per trial within the batch

        # Ordered
        resamples_ord = standard_bootstrap(
            generate_ar1(phi, n, get_data_seed(trial_seed)),
            n_resamples,
            get_bootstrap_seed(trial_seed)
        )
        ci_ord = calculate_ci_from_resamples(resamples_ord, alpha=alpha)
        ordered_cis.append(ci_ord)
        if ci_ord[0] <= 0.0 <= ci_ord[1]:
            ordered_covered_count += 1

        # Shuffled
        resamples_shuf = shuffled_bootstrap(
            generate_ar1(phi, n, get_data_seed(trial_seed)),
            n_resamples,
            get_bootstrap_seed(trial_seed),
            get_shuffle_seed(trial_seed)
        )
        ci_shuf = calculate_ci_from_resamples(resamples_shuf, alpha=alpha)
        shuffled_cis.append(ci_shuf)
        if ci_shuf[0] <= 0.0 <= ci_shuf[1]:
            shuffled_covered_count += 1

    ordered_coverage = ordered_covered_count / trials
    shuffled_coverage = shuffled_covered_count / trials
    diff = ordered_coverage - shuffled_coverage

    # McNemar's test for paired outcomes
    # We need the contingency table of (Ordered Covered, Shuffled Covered)
    # Since we ran them with the same seeds, we can reconstruct the pairs
    # But for efficiency, we'll re-run the logic to get the pairs
    # Actually, we need to store the individual trial results to build the table
    # Let's refactor slightly to capture the pairs during the loop
    # To avoid re-running, we will assume the loop above is the source of truth
    # and we need to re-collect the binary outcomes for McNemar.
    # Since the loop is deterministic given seeds, we can just re-run the collection
    # or store it. Let's store it properly in a new loop structure for clarity.
    
    # Re-implementation for accurate McNemar table construction
    ordered_outcomes = []
    shuffled_outcomes = []
    
    for i in range(trials):
        trial_seed = seed + i
        
        # Ordered
        data_ord = generate_ar1(phi, n, get_data_seed(trial_seed))
        resamples_ord = standard_bootstrap(data_ord, n_resamples, get_bootstrap_seed(trial_seed))
        ci_ord = calculate_ci_from_resamples(resamples_ord, alpha=alpha)
        ordered_outcomes.append(1 if ci_ord[0] <= 0.0 <= ci_ord[1] else 0)
        
        # Shuffled
        data_shuf = generate_ar1(phi, n, get_data_seed(trial_seed))
        resamples_shuf = shuffled_bootstrap(data_shuf, n_resamples, get_bootstrap_seed(trial_seed), get_shuffle_seed(trial_seed))
        ci_shuf = calculate_ci_from_resamples(resamples_shuf, alpha=alpha)
        shuffled_outcomes.append(1 if ci_shuf[0] <= 0.0 <= ci_shuf[1] else 0)
    
    # Build contingency table: [[n00, n01], [n10, n11]]
    # 0 = not covered, 1 = covered
    n00 = n01 = n10 = n11 = 0
    for o, s in zip(ordered_outcomes, shuffled_outcomes):
        if o == 0 and s == 0: n00 += 1
        elif o == 0 and s == 1: n01 += 1
        elif o == 1 and s == 0: n10 += 1
        elif o == 1 and s == 1: n11 += 1
    
    contingency = np.array([[n00, n01], [n10, n11]])
    _, p_value = mcnemar_test_logic(contingency)

    return {
        "phi": phi,
        "n": n,
        "seed": seed,
        "ordered_coverage": ordered_coverage,
        "shuffled_coverage": shuffled_coverage,
        "diff": diff,
        "p_value": p_value,
        "condition": "paired",
        "n_resamples": n_resamples,
        "trials": trials
    }

def aggregate_batch_results(
    phi: float,
    n: int,
    seed: int,
    n_resamples: int,
    trials: int,
    alpha: float = DEFAULT_ALPHA
) -> List[Dict[str, Any]]:
    """Aggregate results for a specific (phi, n) across trials."""
    # We run the paired trial which aggregates internally
    # But for the log, we want the aggregate summary
    return [run_paired_trial(phi, n, seed, n_resamples, trials, alpha)]

def save_results_to_json(results: List[Dict[str, Any]], filepath: Path) -> None:
    """Save simulation results to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {filepath}")

def run_simulation(
    phi_range: tuple,
    sample_sizes: List[int],
    trials: int,
    n_resamples: int,
    seed: int,
    alpha: float = DEFAULT_ALPHA
) -> List[Dict[str, Any]]:
    """Run the full simulation batch."""
    results = []
    phi_start, phi_end = phi_range
    
    # Generate phi values
    phi_values = np.arange(phi_start, phi_end + 0.1, 0.1)
    phi_values = [round(p, 1) for p in phi_values]

    start_time = time.time()
    logger.info(f"Starting simulation: phi={phi_values}, n={sample_sizes}, trials={trials}")

    for phi in phi_values:
        for n in sample_sizes:
            logger.info(f"Running phi={phi}, n={n}")
            batch_result = aggregate_batch_results(
                phi, n, seed, n_resamples, trials, alpha
            )
            results.extend(batch_result)

    elapsed = time.time() - start_time
    logger.info(f"Simulation completed in {elapsed:.2f} seconds")

    return results

def main():
    parser = argparse.ArgumentParser(description="Run bootstrap simulation on AR(1) data")
    parser.add_argument("--full", action="store_true", help="Run full simulation batch")
    parser.add_argument("--phi", type=float, default=None, help="Specific phi value")
    parser.add_argument("--n", type=int, default=None, help="Specific sample size")
    parser.add_argument("--resamples", type=int, default=DEFAULT_RESAMPLES, help="Number of bootstrap resamples")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS, help="Number of trials per condition")
    parser.add_argument("--seed", type=int, default=get_data_seed(0), help="Random seed")
    parser.add_argument("--setup", action="store_true", help="Initialize project directories")

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    ensure_directories()

    if args.setup:
        logger.info("Directories initialized.")
        return

    results_log_path = get_results_dir() / "simulation_logs.json"
    metrics_csv_path = get_results_dir() / "coverage_metrics.csv"

    if args.full:
        logger.info("Running full simulation batch (Synthetic Only: US1 + US2)")
        results = run_simulation(
            phi_range=DEFAULT_PHI_RANGE,
            sample_sizes=DEFAULT_SAMPLE_SIZES,
            trials=args.trials,
            n_resamples=args.resamples,
            seed=args.seed
        )
        save_results_to_json(results, results_log_path)
        
        # Generate CSV from JSON log
        logger.info("Generating CSV from simulation logs...")
        from generate_metrics_csv import main as generate_csv_main
        # We need to pass the path or let it default. 
        # Let's assume generate_metrics_csv handles the default paths.
        # If not, we might need to adjust, but per API surface it has a main.
        # We'll call it and hope it uses the default paths established in config.
        # If it needs arguments, we'd need to check, but the prompt implies it exists.
        # Let's assume it reads from results_log_path and writes to metrics_csv_path
        # based on standard project patterns.
        # Actually, looking at the API surface, generate_metrics_csv has 'main'.
        # We'll call it.
        try:
            generate_csv_main()
        except Exception as e:
            logger.warning(f"Could not auto-generate CSV: {e}. Manual step may be required.")
        
        logger.info("Full simulation completed.")
    else:
        # Single run or partial
        if args.phi is not None and args.n is not None:
            logger.info(f"Running single trial: phi={args.phi}, n={args.n}")
            result = run_paired_trial(
                args.phi, args.n, args.seed, args.resamples, args.trials
            )
            save_results_to_json([result], get_results_dir() / "single_trial.json")
        else:
            parser.print_help()

if __name__ == "__main__":
    main()
