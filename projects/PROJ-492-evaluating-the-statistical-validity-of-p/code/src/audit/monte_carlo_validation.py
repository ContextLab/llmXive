"""
Monte-Carlo validation module for statistical test correctness (FR-026).

This module validates the statistical reconstruction logic by running Monte-Carlo
simulations for z-test, Fisher's exact test, Welch's t-test, and binomial test.
It compares empirical p-values against theoretical expectations to ensure the
absolute difference is <= 0.005.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from code.src.config import SEED, set_rng_seed
from code.src.audit.monte_carlo_core import (
    set_seeds,
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
    run_monte_carlo_validation_core
)
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
NUM_REPLICATES = 10000
TOLERANCE = 0.005
ALPHA = 0.05

logger = get_default_logger(__name__)

def validate_z_test(
    n1: int, n2: int, p1: float, p2: float,
    num_replicates: int = NUM_REPLICATES,
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Validate two-proportion z-test using Monte-Carlo simulation.

    Args:
        n1, n2: Sample sizes for group 1 and 2
        p1, p2: True proportions for group 1 and 2 (under null hypothesis, p1 approx p2)
        num_replicates: Number of simulation replicates
        seed: Random seed for reproducibility

    Returns:
        Dictionary with validation results
    """
    set_rng_seed(seed)
    logger.info(f"Running z-test validation with {num_replicates} replicates...")
    start_time = time.time()

    # Generate null data and compute empirical p-value
    # Under null hypothesis, we assume p1 = p2 = pooled proportion
    pooled_p = (p1 * n1 + p2 * n2) / (n1 + n2)

    empirical_p, z_stats = run_monte_carlo_validation_core(
        simulate_func=lambda: simulate_z_test_statistic(n1, n2, pooled_p),
        num_replicates=num_replicates,
        alpha=ALPHA
    )

    # Theoretical p-value from scipy (using the same pooled proportion)
    from scipy import stats
    # Calculate observed counts
    x1 = int(round(n1 * p1))
    x2 = int(round(n2 * p2))
    
    # Two-proportion z-test
    stat, theoretical_p = stats.proportions_ztest([x1, x2], [n1, n2])

    elapsed = time.time() - start_time
    diff = abs(empirical_p - theoretical_p)

    result = {
        "test": "z_test",
        "n1": n1,
        "n2": n2,
        "p1": p1,
        "p2": p2,
        "num_replicates": num_replicates,
        "empirical_p_value": empirical_p,
        "theoretical_p_value": theoretical_p,
        "absolute_difference": diff,
        "passed": diff <= TOLERANCE,
        "elapsed_seconds": elapsed
    }

    if result["passed"]:
        logger.info(f"Z-test validation PASSED: diff={diff:.6f} <= {TOLERANCE}")
    else:
        logger.warning(f"Z-test validation FAILED: diff={diff:.6f} > {TOLERANCE}")

    return result

def validate_fisher_exact(
    n1: int, n2: int, p1: float, p2: float,
    num_replicates: int = NUM_REPLICATES,
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Validate Fisher's exact test using Monte-Carlo simulation.

    Args:
        n1, n2: Sample sizes
        p1, p2: True proportions
        num_replicates: Number of simulation replicates
        seed: Random seed

    Returns:
        Dictionary with validation results
    """
    set_rng_seed(seed)
    logger.info(f"Running Fisher's exact test validation with {num_replicates} replicates...")
    start_time = time.time()

    # Generate contingency table under null
    x1 = int(round(n1 * p1))
    x2 = int(round(n2 * p2))
    
    # Run Monte-Carlo simulation for Fisher's exact
    empirical_p, tables = run_monte_carlo_validation_core(
        simulate_func=lambda: simulate_fisher_exact_table(n1, n2, x1, x2),
        num_replicates=num_replicates,
        alpha=ALPHA
    )

    # Theoretical p-value
    from scipy import stats
    table = [[x1, n1 - x1], [x2, n2 - x2]]
    _, theoretical_p = stats.fisher_exact(table, alternative='two-sided')

    elapsed = time.time() - start_time
    diff = abs(empirical_p - theoretical_p)

    result = {
        "test": "fisher_exact",
        "n1": n1,
        "n2": n2,
        "p1": p1,
        "p2": p2,
        "num_replicates": num_replicates,
        "empirical_p_value": empirical_p,
        "theoretical_p_value": theoretical_p,
        "absolute_difference": diff,
        "passed": diff <= TOLERANCE,
        "elapsed_seconds": elapsed
    }

    if result["passed"]:
        logger.info(f"Fisher's exact test validation PASSED: diff={diff:.6f} <= {TOLERANCE}")
    else:
        logger.warning(f"Fisher's exact test validation FAILED: diff={diff:.6f} > {TOLERANCE}")

    return result

def validate_welch_t_test(
    n1: int, n2: int, mean1: float, mean2: float,
    std1: float, std2: float,
    num_replicates: int = NUM_REPLICATES,
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Validate Welch's t-test using Monte-Carlo simulation.

    Args:
        n1, n2: Sample sizes
        mean1, mean2: True means
        std1, std2: True standard deviations
        num_replicates: Number of simulation replicates
        seed: Random seed

    Returns:
        Dictionary with validation results
    """
    set_rng_seed(seed)
    logger.info(f"Running Welch's t-test validation with {num_replicates} replicates...")
    start_time = time.time()

    # Run Monte-Carlo simulation
    empirical_p, t_stats = run_monte_carlo_validation_core(
        simulate_func=lambda: simulate_welch_t_statistic(n1, n2, mean1, mean2, std1, std2),
        num_replicates=num_replicates,
        alpha=ALPHA
    )

    # Theoretical p-value
    from scipy import stats
    # Generate sample data for theoretical test
    np.random.seed(seed)
    sample1 = np.random.normal(mean1, std1, n1)
    sample2 = np.random.normal(mean2, std2, n2)
    
    stat, theoretical_p = stats.ttest_ind(sample1, sample2, equal_var=False)

    elapsed = time.time() - start_time
    diff = abs(empirical_p - theoretical_p)

    result = {
        "test": "welch_t_test",
        "n1": n1,
        "n2": n2,
        "mean1": mean1,
        "mean2": mean2,
        "std1": std1,
        "std2": std2,
        "num_replicates": num_replicates,
        "empirical_p_value": empirical_p,
        "theoretical_p_value": theoretical_p,
        "absolute_difference": diff,
        "passed": diff <= TOLERANCE,
        "elapsed_seconds": elapsed
    }

    if result["passed"]:
        logger.info(f"Welch's t-test validation PASSED: diff={diff:.6f} <= {TOLERANCE}")
    else:
        logger.warning(f"Welch's t-test validation FAILED: diff={diff:.6f} > {TOLERANCE}")

    return result

def validate_binomial_test(
    n: int, p: float, k: int,
    num_replicates: int = NUM_REPLICATES,
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Validate binomial test using Monte-Carlo simulation.

    Args:
        n: Sample size
        p: True probability
        k: Observed successes
        num_replicates: Number of simulation replicates
        seed: Random seed

    Returns:
        Dictionary with validation results
    """
    set_rng_seed(seed)
    logger.info(f"Running binomial test validation with {num_replicates} replicates...")
    start_time = time.time()

    # Run Monte-Carlo simulation
    empirical_p, counts = run_monte_carlo_validation_core(
        simulate_func=lambda: simulate_binomial_statistic(n, p, k),
        num_replicates=num_replicates,
        alpha=ALPHA
    )

    # Theoretical p-value
    from scipy import stats
    # Two-sided binomial test
    theoretical_p = stats.binom_test(k, n, p, alternative='two-sided')

    elapsed = time.time() - start_time
    diff = abs(empirical_p - theoretical_p)

    result = {
        "test": "binomial",
        "n": n,
        "p": p,
        "k": k,
        "num_replicates": num_replicates,
        "empirical_p_value": empirical_p,
        "theoretical_p_value": theoretical_p,
        "absolute_difference": diff,
        "passed": diff <= TOLERANCE,
        "elapsed_seconds": elapsed
    }

    if result["passed"]:
        logger.info(f"Binomial test validation PASSED: diff={diff:.6f} <= {TOLERANCE}")
    else:
        logger.warning(f"Binomial test validation FAILED: diff={diff:.6f} > {TOLERANCE}")

    return result

def run_monte_carlo_validation(
    output_path: Optional[Path] = None,
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Run full Monte-Carlo validation suite for all statistical tests.

    Args:
        output_path: Optional path to write results JSON
        seed: Random seed

    Returns:
        Dictionary with all validation results
    """
    set_rng_seed(seed)
    logger.info("Starting Monte-Carlo validation suite...")
    total_start = time.time()

    results = {
        "summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "overall_passed": True
        },
        "tests": []
    }

    # Test parameters
    test_configs = [
        # Z-test configurations (binary outcomes)
        {"type": "z_test", "n1": 1000, "n2": 1000, "p1": 0.5, "p2": 0.5},
        {"type": "z_test", "n1": 5000, "n2": 5000, "p1": 0.3, "p2": 0.32},
        
        # Fisher's exact test configurations
        {"type": "fisher_exact", "n1": 500, "n2": 500, "p1": 0.4, "p2": 0.4},
        {"type": "fisher_exact", "n1": 1000, "n2": 1000, "p1": 0.2, "p2": 0.25},
        
        # Welch's t-test configurations (continuous outcomes)
        {"type": "welch_t_test", "n1": 2000, "n2": 2000, "mean1": 50.0, "mean2": 50.0, "std1": 10.0, "std2": 10.0},
        {"type": "welch_t_test", "n1": 3000, "n2": 3000, "mean1": 100.0, "mean2": 102.0, "std1": 15.0, "std2": 15.0},
        
        # Binomial test configurations
        {"type": "binomial", "n": 1000, "p": 0.5, "k": 500},
        {"type": "binomial", "n": 2000, "p": 0.4, "k": 820},
    ]

    for config in test_configs:
        test_type = config.pop("type")
        
        if test_type == "z_test":
            result = validate_z_test(
                n1=config["n1"], n2=config["n2"],
                p1=config["p1"], p2=config["p2"],
                num_replicates=NUM_REPLICATES,
                seed=seed
            )
        elif test_type == "fisher_exact":
            result = validate_fisher_exact(
                n1=config["n1"], n2=config["n2"],
                p1=config["p1"], p2=config["p2"],
                num_replicates=NUM_REPLICATES,
                seed=seed
            )
        elif test_type == "welch_t_test":
            result = validate_welch_t_test(
                n1=config["n1"], n2=config["n2"],
                mean1=config["mean1"], mean2=config["mean2"],
                std1=config["std1"], std2=config["std2"],
                num_replicates=NUM_REPLICATES,
                seed=seed
            )
        elif test_type == "binomial":
            result = validate_binomial_test(
                n=config["n"], p=config["p"], k=config["k"],
                num_replicates=NUM_REPLICATES,
                seed=seed
            )
        else:
            logger.error(f"Unknown test type: {test_type}")
            continue

        results["tests"].append(result)
        results["summary"]["total_tests"] += 1
        
        if result["passed"]:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
            results["summary"]["overall_passed"] = False

    total_elapsed = time.time() - total_start
    results["summary"]["total_elapsed_seconds"] = total_elapsed

    # Write results if output path provided
    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Validation results written to {output_path}")

    return results

def main():
    """Main entry point for Monte-Carlo validation."""
    logger.info("Monte-Carlo Validation Module (FR-026)")
    logger.info(f"Running with {NUM_REPLICATES} replicates per test")
    logger.info(f"Acceptance threshold: absolute difference <= {TOLERANCE}")

    output_path = Path("output/monte_carlo_validation_results.json")
    results = run_monte_carlo_validation(output_path=output_path)

    # Exit with appropriate status
    if results["summary"]["overall_passed"]:
        logger.info("All Monte-Carlo validations PASSED")
        sys.exit(0)
    else:
        logger.error("Some Monte-Carlo validations FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()