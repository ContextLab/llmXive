"""
Simulation runner module for orchestrating bootstrap experiments.

Provides functions to run single simulations, full batches, and aggregate results.
"""
import argparse
import json
import os
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from data_generation import generate_ar1
from bootstrap_engine import standard_bootstrap, shuffled_bootstrap, calculate_ci_from_resamples
from metrics import (
    calculate_coverage, 
    calculate_ci_width_stability, 
    calculate_coverage_drop_magnitude,
    mcnemar_test_logic
)
from config import get_data_seed, get_bootstrap_seed, get_shuffle_seed
from utils import setup_logging, log_simulation_result, load_simulation_logs


def run_simulation(phi: float, n: int, seed: Optional[int] = None, 
                   n_resamples: int = 1000, n_trials: int = 100) -> Dict[str, Any]:
    """
    Run a single simulation batch for given phi and n.
    
    Args:
        phi: Autoregressive coefficient.
        n: Time series length.
        seed: Random seed. If None, uses config defaults.
        n_resamples: Number of bootstrap resamples per trial.
        n_trials: Number of independent trials.
    
    Returns:
        Dictionary containing simulation results and metrics.
    """
    if seed is None:
        seed = get_data_seed()
    
    ordered_covered = []
    shuffled_covered = []
    ordered_cis = []
    shuffled_cis = []
    
    rng = np.random.default_rng(seed)
    
    for trial in range(n_trials):
        trial_seed = rng.integers(0, 2**31)
        
        # Generate AR(1) data
        data = generate_ar1(phi, n, seed=int(trial_seed))
        true_mean = 0.0  # Theoretical mean for AR(1) with no intercept
        
        # Standard bootstrap (ordered)
        boot_seed_ordered = rng.integers(0, 2**31)
        resamples_ordered = standard_bootstrap(data, n_resamples, seed=int(boot_seed_ordered))
        ci_ordered = calculate_ci_from_resamples(resamples_ordered)
        ordered_cis.append(ci_ordered)
        ordered_covered.append(ci_ordered[0] <= true_mean <= ci_ordered[1])
        
        # Shuffled bootstrap
        boot_seed_shuffled = rng.integers(0, 2**31)
        resamples_shuffled = shuffled_bootstrap(data, n_resamples, seed=int(boot_seed_shuffled))
        ci_shuffled = calculate_ci_from_resamples(resamples_shuffled)
        shuffled_cis.append(ci_shuffled)
        shuffled_covered.append(ci_shuffled[0] <= true_mean <= ci_shuffled[1])
    
    # Calculate metrics
    ordered_coverage = calculate_coverage(ordered_cis, true_mean)
    shuffled_coverage = calculate_coverage(shuffled_cis, true_mean)
    coverage_drop = calculate_coverage_drop_magnitude(ordered_coverage)
    ci_width_ratio = calculate_ci_width_stability(ordered_cis, shuffled_cis)
    p_value = mcnemar_test_logic(ordered_covered, shuffled_covered)
    
    return {
        'phi': phi,
        'n': n,
        'ordered_coverage': ordered_coverage,
        'shuffled_coverage': shuffled_coverage,
        'coverage_drop': coverage_drop,
        'ci_width_ratio': ci_width_ratio,
        'p_value': p_value,
        'ordered_ci_width': np.mean([c[1] - c[0] for c in ordered_cis]),
        'shuffled_ci_width': np.mean([c[1] - c[0] for c in shuffled_cis])
    }


def run_full_batch(phi_values: List[float], n_values: List[int], 
                   seed: Optional[int] = None, 
                   n_resamples: int = 1000, 
                   n_trials: int = 100) -> List[Dict[str, Any]]:
    """
    Run full simulation batch across phi and n values.
    
    Args:
        phi_values: List of phi values to test.
        n_values: List of sample sizes to test.
        seed: Base random seed.
        n_resamples: Bootstrap resamples per trial.
        n_trials: Independent trials per configuration.
    
    Returns:
        List of result dictionaries for each configuration.
    """
    results = []
    start_time = time.time()
    
    for phi in phi_values:
        for n in n_values:
            logging.info(f"Running simulation: phi={phi}, n={n}")
            result = run_simulation(phi, n, seed, n_resamples, n_trials)
            results.append(result)
            log_simulation_result(result)
    
    elapsed = time.time() - start_time
    logging.info(f"Full batch completed in {elapsed:.2f} seconds")
    
    return results


def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate simulation results into summary statistics.
    
    Args:
        results: List of result dictionaries.
    
    Returns:
        Dictionary with aggregated statistics.
    """
    if not results:
        return {}
    
    return {
        'total_configurations': len(results),
        'mean_ordered_coverage': np.mean([r['ordered_coverage'] for r in results]),
        'mean_shuffled_coverage': np.mean([r['shuffled_coverage'] for r in results]),
        'mean_coverage_drop': np.mean([r['coverage_drop'] for r in results]),
        'mean_ci_width_ratio': np.mean([r['ci_width_ratio'] for r in results]),
        'mean_p_value': np.mean([r['p_value'] for r in results]),
        'significant_results': sum(1 for r in results if r['p_value'] < 0.05)
    }


def main():
    """Main entry point for running simulations."""
    parser = argparse.ArgumentParser(description='Run bootstrap simulation experiments')
    parser.add_argument('--full', action='store_true', help='Run full batch simulation')
    parser.add_argument('--phi', type=float, default=0.8, help='Phi value for single run')
    parser.add_argument('--n', type=int, default=100, help='Sample size for single run')
    parser.add_argument('--resamples', type=int, default=1000, help='Number of bootstrap resamples')
    parser.add_argument('--trials', type=int, default=100, help='Number of independent trials')
    
    args = parser.parse_args()
    
    setup_logging()
    logging.info("Starting bootstrap simulation experiment")
    
    if args.full:
        phi_values = [0.0, 0.3, 0.5, 0.7, 0.8, 0.9]
        n_values = [50, 100, 200]
        results = run_full_batch(phi_values, n_values, n_resamples=args.resamples, n_trials=args.trials)
        summary = aggregate_results(results)
        
        # Save results
        results_path = "results/simulation_logs.json"
        with open(results_path, 'w') as f:
            json.dump({'results': results, 'summary': summary}, f, indent=2)
        logging.info(f"Results saved to {results_path}")
    else:
        result = run_simulation(args.phi, args.n, n_resamples=args.resamples, n_trials=args.trials)
        print(json.dumps(result, indent=2))
        
        # Log single result
        log_simulation_result(result)


if __name__ == "__main__":
    main()
