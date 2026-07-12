"""
Monte-Carlo validation module for statistical tests (FR-026).

This module validates the statistical reconstruction logic by running
Monte-Carlo simulations (10,000 replicates per test) and comparing
the empirical p-values against the theoretical p-values from scipy.

The absolute difference between empirical and theoretical p-values
must be <= 0.005 to pass validation.
"""
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.audit.monte_carlo_core import (
    run_monte_carlo_validation_core,
    set_seeds,
    generate_null_binary_data,
    generate_null_continuous_data,
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
)

# Constants
NUM_REPLICATES = 10000
TOLERANCE = 0.005
ALPHA = 0.05

logger = get_default_logger(__name__)


def validate_z_test(n1: int, n2: int, p1: float, p2: float, seed: int = SEED) -> Dict[str, Any]:
    """
    Validate the two-proportion z-test using Monte-Carlo simulation.
    
    Args:
        n1: Sample size of group 1
        n2: Sample size of group 2
        p1: True proportion of group 1 (under null hypothesis, p1 should equal p2)
        p2: True proportion of group 2
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing validation results
    """
    set_seeds(seed)
    
    # Theoretical p-value (assuming null hypothesis is true, we use pooled proportion)
    # For validation, we simulate under the null hypothesis where p1 = p2 = p_pooled
    p_pooled = (p1 * n1 + p2 * n2) / (n1 + n2)
    
    # Generate null data and run simulation
    results = run_monte_carlo_validation_core(
        n1=n1,
        n2=n2,
        p_true=p_pooled,
        num_replicates=NUM_REPLICATES,
        test_type="z_test",
        seed=seed
    )
    
    theoretical_p = results.get("theoretical_p", 0.0)
    empirical_p = results.get("empirical_p", 0.0)
    abs_diff = abs(theoretical_p - empirical_p)
    passed = abs_diff <= TOLERANCE
    
    return {
        "test_type": "z_test",
        "n1": n1,
        "n2": n2,
        "p_pooled": p_pooled,
        "theoretical_p": theoretical_p,
        "empirical_p": empirical_p,
        "absolute_difference": abs_diff,
        "passed": passed,
        "tolerance": TOLERANCE
    }


def validate_fisher_exact(n1: int, n2: int, p1: float, p2: float, seed: int = SEED) -> Dict[str, Any]:
    """
    Validate Fisher's exact test using Monte-Carlo simulation.
    
    Args:
        n1: Sample size of group 1
        n2: Sample size of group 2
        p1: True proportion of group 1
        p2: True proportion of group 2
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing validation results
    """
    set_seeds(seed)
    
    # Under null hypothesis, use pooled proportion
    p_pooled = (p1 * n1 + p2 * n2) / (n1 + n2)
    
    results = run_monte_carlo_validation_core(
        n1=n1,
        n2=n2,
        p_true=p_pooled,
        num_replicates=NUM_REPLICATES,
        test_type="fisher_exact",
        seed=seed
    )
    
    theoretical_p = results.get("theoretical_p", 0.0)
    empirical_p = results.get("empirical_p", 0.0)
    abs_diff = abs(theoretical_p - empirical_p)
    passed = abs_diff <= TOLERANCE
    
    return {
        "test_type": "fisher_exact",
        "n1": n1,
        "n2": n2,
        "p_pooled": p_pooled,
        "theoretical_p": theoretical_p,
        "empirical_p": empirical_p,
        "absolute_difference": abs_diff,
        "passed": passed,
        "tolerance": TOLERANCE
    }


def validate_welch_t_test(n1: int, n2: int, mean1: float, mean2: float, 
                          std1: float, std2: float, seed: int = SEED) -> Dict[str, Any]:
    """
    Validate Welch's t-test using Monte-Carlo simulation.
    
    Args:
        n1: Sample size of group 1
        n2: Sample size of group 2
        mean1: True mean of group 1
        mean2: True mean of group 2
        std1: True standard deviation of group 1
        std2: True standard deviation of group 2
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing validation results
    """
    set_seeds(seed)
    
    # Under null hypothesis, means should be equal
    # Use pooled mean for simulation
    pooled_mean = (mean1 * n1 + mean2 * n2) / (n1 + n2)
    
    results = run_monte_carlo_validation_core(
        n1=n1,
        n2=n2,
        mean_true=pooled_mean,
        std1=std1,
        std2=std2,
        num_replicates=NUM_REPLICATES,
        test_type="welch_t",
        seed=seed
    )
    
    theoretical_p = results.get("theoretical_p", 0.0)
    empirical_p = results.get("empirical_p", 0.0)
    abs_diff = abs(theoretical_p - empirical_p)
    passed = abs_diff <= TOLERANCE
    
    return {
        "test_type": "welch_t",
        "n1": n1,
        "n2": n2,
        "pooled_mean": pooled_mean,
        "std1": std1,
        "std2": std2,
        "theoretical_p": theoretical_p,
        "empirical_p": empirical_p,
        "absolute_difference": abs_diff,
        "passed": passed,
        "tolerance": TOLERANCE
    }


def validate_binomial_test(n: int, p_null: float, k: int, seed: int = SEED) -> Dict[str, Any]:
    """
    Validate binomial test using Monte-Carlo simulation.
    
    Args:
        n: Total number of trials
        p_null: Null hypothesis probability of success
        k: Observed number of successes
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing validation results
    """
    set_seeds(seed)
    
    results = run_monte_carlo_validation_core(
        n=n,
        p_true=p_null,
        k_observed=k,
        num_replicates=NUM_REPLICATES,
        test_type="binomial",
        seed=seed
    )
    
    theoretical_p = results.get("theoretical_p", 0.0)
    empirical_p = results.get("empirical_p", 0.0)
    abs_diff = abs(theoretical_p - empirical_p)
    passed = abs_diff <= TOLERANCE
    
    return {
        "test_type": "binomial",
        "n": n,
        "p_null": p_null,
        "k_observed": k,
        "theoretical_p": theoretical_p,
        "empirical_p": empirical_p,
        "absolute_difference": abs_diff,
        "passed": passed,
        "tolerance": TOLERANCE
    }


def run_monte_carlo_validation(output_path: Optional[Path] = None, seed: int = SEED) -> Dict[str, Any]:
    """
    Run Monte-Carlo validation for all statistical tests.
    
    This function validates:
    1. Two-proportion z-test
    2. Fisher's exact test
    3. Welch's t-test
    4. Binomial test
    
    Each test runs NUM_REPLICATES (10,000) simulations and checks that
    the absolute difference between empirical and theoretical p-values
    is <= TOLERANCE (0.005).
    
    Args:
        output_path: Optional path to write results to JSON
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing all validation results and overall status
    """
    set_seeds(seed)
    start_time = time.time()
    
    logger.info(f"Starting Monte-Carlo validation with {NUM_REPLICATES} replicates per test")
    logger.info(f"Tolerance: {TOLERANCE}")
    
    results = {
        "seed": seed,
        "num_replicates": NUM_REPLICATES,
        "tolerance": TOLERANCE,
        "tests": {},
        "overall_passed": True,
        "execution_time_seconds": 0.0
    }
    
    # Test parameters for validation
    # These are chosen to represent typical A/B test scenarios
    test_configs = {
        "z_test": {
            "n1": 1000,
            "n2": 1000,
            "p1": 0.10,
            "p2": 0.10  # Under null, p1 = p2
        },
        "fisher_exact": {
            "n1": 500,
            "n2": 500,
            "p1": 0.15,
            "p2": 0.15  # Under null, p1 = p2
        },
        "welch_t": {
            "n1": 800,
            "n2": 800,
            "mean1": 50.0,
            "mean2": 50.0,  # Under null, means are equal
            "std1": 10.0,
            "std2": 12.0
        },
        "binomial": {
            "n": 1000,
            "p_null": 0.05,
            "k": 50  # Expected under null
        }
    }
    
    # Run z-test validation
    logger.info("Validating z-test...")
    z_config = test_configs["z_test"]
    z_result = validate_z_test(
        n1=z_config["n1"],
        n2=z_config["n2"],
        p1=z_config["p1"],
        p2=z_config["p2"],
        seed=seed
    )
    results["tests"]["z_test"] = z_result
    if not z_result["passed"]:
        results["overall_passed"] = False
        logger.warning(f"Z-test validation FAILED: diff={z_result['absolute_difference']:.6f}")
    else:
        logger.info(f"Z-test validation PASSED: diff={z_result['absolute_difference']:.6f}")
    
    # Run Fisher's exact test validation
    logger.info("Validating Fisher's exact test...")
    fisher_config = test_configs["fisher_exact"]
    fisher_result = validate_fisher_exact(
        n1=fisher_config["n1"],
        n2=fisher_config["n2"],
        p1=fisher_config["p1"],
        p2=fisher_config["p2"],
        seed=seed
    )
    results["tests"]["fisher_exact"] = fisher_result
    if not fisher_result["passed"]:
        results["overall_passed"] = False
        logger.warning(f"Fisher's exact test validation FAILED: diff={fisher_result['absolute_difference']:.6f}")
    else:
        logger.info(f"Fisher's exact test validation PASSED: diff={fisher_result['absolute_difference']:.6f}")
    
    # Run Welch's t-test validation
    logger.info("Validating Welch's t-test...")
    welch_config = test_configs["welch_t"]
    welch_result = validate_welch_t_test(
        n1=welch_config["n1"],
        n2=welch_config["n2"],
        mean1=welch_config["mean1"],
        mean2=welch_config["mean2"],
        std1=welch_config["std1"],
        std2=welch_config["std2"],
        seed=seed
    )
    results["tests"]["welch_t"] = welch_result
    if not welch_result["passed"]:
        results["overall_passed"] = False
        logger.warning(f"Welch's t-test validation FAILED: diff={welch_result['absolute_difference']:.6f}")
    else:
        logger.info(f"Welch's t-test validation PASSED: diff={welch_result['absolute_difference']:.6f}")
    
    # Run binomial test validation
    logger.info("Validating binomial test...")
    binom_config = test_configs["binomial"]
    binom_result = validate_binomial_test(
        n=binom_config["n"],
        p_null=binom_config["p_null"],
        k=binom_config["k"],
        seed=seed
    )
    results["tests"]["binomial"] = binom_result
    if not binom_result["passed"]:
        results["overall_passed"] = False
        logger.warning(f"Binomial test validation FAILED: diff={binom_result['absolute_difference']:.6f}")
    else:
        logger.info(f"Binomial test validation PASSED: diff={binom_result['absolute_difference']:.6f}")
    
    end_time = time.time()
    results["execution_time_seconds"] = round(end_time - start_time, 2)
    
    logger.info(f"Monte-Carlo validation completed in {results['execution_time_seconds']} seconds")
    logger.info(f"Overall status: {'PASSED' if results['overall_passed'] else 'FAILED'}")
    
    # Write results to file if output_path is provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {output_path}")
    
    return results


def main() -> int:
    """
    Main entry point for Monte-Carlo validation.
    
    Returns:
        0 if all tests pass, 1 otherwise
    """
    logger.info("=" * 60)
    logger.info("Monte-Carlo Validation Module (FR-026)")
    logger.info("=" * 60)
    
    output_path = Path("code/output/monte_carlo_validation_results.json")
    results = run_monte_carlo_validation(output_path=output_path)
    
    if results["overall_passed"]:
        logger.info("All Monte-Carlo validations PASSED.")
        return 0
    else:
        logger.error("One or more Monte-Carlo validations FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())