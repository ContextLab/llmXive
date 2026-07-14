"""
T031b: Execute the Synthetic Ground Truth test (T031a) and act as a blocking gate.

This script runs the synthetic data generation and power recovery test defined in T031a.
It verifies that the empirical power recovery rate is within 5% of the true theoretical power.

If the check fails, it exits with a non-zero code and prints a failure message.
If it passes, it writes the results to data/results/synthetic_gate_results.json
and exits successfully.
"""
import json
import sys
import logging
from pathlib import Path

import numpy as np
from scipy import stats

# Project imports
from config import RANDOM_SEED, DATASET_LIST
from utils import setup_logging, save_json
from power_empirical import run_synthetic_power_test

def main():
    logger = setup_logging()
    logger.info("Starting Synthetic Ground Truth Test (T031b)...")
    
    # Configuration for the test
    # We use a standard effect size (Cohen's d = 0.5) and sample size
    # to ensure we have a known theoretical power to compare against.
    effect_size = 0.5
    n_per_group = 64  # Standard sample size for d=0.5 to get ~80% power
    alpha = 0.05
    n_bootstrap_samples = 1000
    n_simulations = 500  # Number of synthetic datasets to generate for the test
    
    logger.info(f"Parameters: d={effect_size}, n={n_per_group}, alpha={alpha}")
    logger.info(f"Running {n_simulations} simulations with {n_bootstrap_samples} bootstrap samples...")
    
    # Run the synthetic test
    # This function generates data with known parameters and checks recovery
    result = run_synthetic_power_test(
        effect_size=effect_size,
        n_per_group=n_per_group,
        alpha=alpha,
        n_bootstrap_samples=n_bootstrap_samples,
        n_simulations=n_simulations,
        random_seed=RANDOM_SEED
    )
    
    theoretical_power = result['theoretical_power']
    empirical_power = result['empirical_power']
    recovery_rate = result['recovery_rate']
    tolerance = 0.05  # 5% tolerance
    
    logger.info(f"Theoretical Power: {theoretical_power:.4f}")
    logger.info(f"Empirical Power (Recovery Rate): {empirical_power:.4f}")
    logger.info(f"Difference: {abs(theoretical_power - empirical_power):.4f}")
    
    # Validation Logic
    passed = abs(theoretical_power - empirical_power) <= tolerance
    
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "synthetic_gate_results.json"
    
    report = {
        "task_id": "T031b",
        "status": "passed" if passed else "failed",
        "parameters": {
            "effect_size": effect_size,
            "n_per_group": n_per_group,
            "alpha": alpha,
            "n_bootstrap_samples": n_bootstrap_samples,
            "n_simulations": n_simulations
        },
        "results": {
            "theoretical_power": float(theoretical_power),
            "empirical_power": float(empirical_power),
            "recovery_rate": float(recovery_rate),
            "absolute_error": float(abs(theoretical_power - empirical_power)),
            "tolerance": tolerance
        },
        "gate_result": passed,
        "message": "Synthetic Ground Truth validation PASSED. Real data processing can proceed." if passed else "Synthetic Ground Truth validation FAILED. Real data processing is BLOCKED."
    }
    
    save_json(report, output_file)
    logger.info(f"Results written to {output_file}")
    
    if not passed:
        logger.error("GATE FAILED: Recovery rate is not within 5% of theoretical power.")
        logger.error("No real-data processing (Phase 3+) can begin.")
        sys.exit(1)
    
    logger.info("GATE PASSED: Validation successful. Proceeding to real data processing.")
    sys.exit(0)

if __name__ == "__main__":
    main()