"""
Monte-Carlo validation module for statistical test consistency.

This module validates the correctness of statistical tests (z-test, Fisher's exact,
Welch's t-test, binomial test) by running Monte-Carlo simulations and comparing
empirical p-values against theoretical expectations.

Per FR-026, this module runs 10,000 replicates for each test type and verifies
that the absolute difference between empirical and theoretical p-values is <= 0.005.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import numpy as np
from scipy import stats

from code.src.audit.monte_carlo_core import (
    set_seeds,
    generate_null_binary_data,
    generate_null_continuous_data,
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
)
from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants for Monte-Carlo validation
NUM_REPLICATES = 10000
TOLERANCE = 0.005  # Maximum allowed absolute difference


def validate_z_test(
    n_replicates: int = NUM_REPLICATES,
    seed: int = SEED,
) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate the two-proportion z-test using Monte-Carlo simulation.

    Under the null hypothesis (equal proportions), the z-test p-values should
    be uniformly distributed. We verify that the empirical Type I error rate
    at alpha=0.05 is within tolerance of the theoretical rate.

    Args:
        n_replicates: Number of Monte-Carlo replicates.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (passed, empirical_p, theoretical_p, details_dict)
    """
    set_seeds(seed)
    logger = get_default_logger()
    logger.info(f"Starting z-test validation with {n_replicates} replicates")

    # Parameters for the null simulation (equal proportions)
    n1, n2 = 100, 100
    p1, p2 = 0.5, 0.5

    # Generate null data and compute empirical p-values
    empirical_p_values = []
    for _ in range(n_replicates):
        # Generate binary outcomes under null
        group_a = generate_null_binary_data(n1, p1)
        group_b = generate_null_binary_data(n2, p2)

        # Compute z-test statistic and p-value
        stat, p_val = simulate_z_test_statistic(group_a, group_b)
        empirical_p_values.append(p_val)

    # Calculate empirical Type I error rate at alpha=0.05
    alpha = 0.05
    empirical_error_rate = np.mean(np.array(empirical_p_values) < alpha)
    theoretical_error_rate = alpha

    # Check if within tolerance
    diff = abs(empirical_error_rate - theoretical_error_rate)
    passed = diff <= TOLERANCE

    details = {
        "test_type": "z_test",
        "n_replicates": n_replicates,
        "sample_sizes": (n1, n2),
        "true_proportions": (p1, p2),
        "alpha": alpha,
        "empirical_error_rate": float(empirical_error_rate),
        "theoretical_error_rate": float(theoretical_error_rate),
        "absolute_difference": float(diff),
        "passed": passed,
    }

    logger.info(
        f"Z-test validation: empirical={empirical_error_rate:.4f}, "
        f"theoretical={theoretical_error_rate:.4f}, diff={diff:.4f}, "
        f"passed={passed}"
    )

    return passed, float(empirical_error_rate), float(theoretical_error_rate), details


def validate_fisher_exact(
    n_replicates: int = NUM_REPLICATES,
    seed: int = SEED,
) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate Fisher's exact test using Monte-Carlo simulation.

    Under the null hypothesis (independence), Fisher's exact test p-values
    should be uniformly distributed. We verify the Type I error rate.

    Args:
        n_replicates: Number of Monte-Carlo replicates.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (passed, empirical_p, theoretical_p, details_dict)
    """
    set_seeds(seed)
    logger = get_default_logger()
    logger.info(f"Starting Fisher's exact test validation with {n_replicates} replicates")

    # Parameters for null simulation (independence)
    n1, n2 = 50, 50
    p1, p2 = 0.3, 0.3  # Equal probabilities under null

    empirical_p_values = []
    for _ in range(n_replicates):
        # Generate contingency table under null
        table = simulate_fisher_exact_table(n1, n2, p1, p2)

        # Compute Fisher's exact test p-value
        _, p_val = stats.fisher_exact(table, alternative='two-sided')
        empirical_p_values.append(p_val)

    # Calculate empirical Type I error rate
    alpha = 0.05
    empirical_error_rate = np.mean(np.array(empirical_p_values) < alpha)
    theoretical_error_rate = alpha

    diff = abs(empirical_error_rate - theoretical_error_rate)
    passed = diff <= TOLERANCE

    details = {
        "test_type": "fisher_exact",
        "n_replicates": n_replicates,
        "sample_sizes": (n1, n2),
        "true_proportions": (p1, p2),
        "alpha": alpha,
        "empirical_error_rate": float(empirical_error_rate),
        "theoretical_error_rate": float(theoretical_error_rate),
        "absolute_difference": float(diff),
        "passed": passed,
    }

    logger.info(
        f"Fisher's exact test validation: empirical={empirical_error_rate:.4f}, "
        f"theoretical={theoretical_error_rate:.4f}, diff={diff:.4f}, "
        f"passed={passed}"
    )

    return passed, float(empirical_error_rate), float(theoretical_error_rate), details


def validate_welch_t_test(
    n_replicates: int = NUM_REPLICATES,
    seed: int = SEED,
) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate Welch's t-test using Monte-Carlo simulation.

    Under the null hypothesis (equal means), Welch's t-test p-values should
    be uniformly distributed. We verify the Type I error rate.

    Args:
        n_replicates: Number of Monte-Carlo replicates.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (passed, empirical_p, theoretical_p, details_dict)
    """
    set_seeds(seed)
    logger = get_default_logger()
    logger.info(f"Starting Welch's t-test validation with {n_replicates} replicates")

    # Parameters for null simulation (equal means, different variances)
    n1, n2 = 30, 40
    mu1, mu2 = 0.0, 0.0
    std1, std2 = 1.0, 1.5  # Different variances (Welch handles this)

    empirical_p_values = []
    for _ in range(n_replicates):
        # Generate continuous data under null
        group_a = generate_null_continuous_data(n1, mu1, std1)
        group_b = generate_null_continuous_data(n2, mu2, std2)

        # Compute Welch's t-test
        stat, p_val = simulate_welch_t_statistic(group_a, group_b)
        empirical_p_values.append(p_val)

    # Calculate empirical Type I error rate
    alpha = 0.05
    empirical_error_rate = np.mean(np.array(empirical_p_values) < alpha)
    theoretical_error_rate = alpha

    diff = abs(empirical_error_rate - theoretical_error_rate)
    passed = diff <= TOLERANCE

    details = {
        "test_type": "welch_t_test",
        "n_replicates": n_replicates,
        "sample_sizes": (n1, n2),
        "true_means": (mu1, mu2),
        "true_stds": (std1, std2),
        "alpha": alpha,
        "empirical_error_rate": float(empirical_error_rate),
        "theoretical_error_rate": float(theoretical_error_rate),
        "absolute_difference": float(diff),
        "passed": passed,
    }

    logger.info(
        f"Welch's t-test validation: empirical={empirical_error_rate:.4f}, "
        f"theoretical={theoretical_error_rate:.4f}, diff={diff:.4f}, "
        f"passed={passed}"
    )

    return passed, float(empirical_error_rate), float(theoretical_error_rate), details


def validate_binomial_test(
    n_replicates: int = NUM_REPLICATES,
    seed: int = SEED,
) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate the binomial test using Monte-Carlo simulation.

    Under the null hypothesis, the binomial test p-values should be uniformly
    distributed. We verify the Type I error rate.

    Args:
        n_replicates: Number of Monte-Carlo replicates.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (passed, empirical_p, theoretical_p, details_dict)
    """
    set_seeds(seed)
    logger = get_default_logger()
    logger.info(f"Starting binomial test validation with {n_replicates} replicates")

    # Parameters for null simulation
    n = 100
    p_null = 0.5

    empirical_p_values = []
    for _ in range(n_replicates):
        # Generate binomial data under null
        successes = simulate_binomial_statistic(n, p_null)

        # Compute binomial test p-value (two-sided)
        # Using scipy's binom_test (deprecated but still functional) or binomtest
        try:
            result = stats.binomtest(successes, n, p_null, alternative='two-sided')
            p_val = result.pvalue
        except AttributeError:
            # Fallback for older scipy versions
            p_val = stats.binom_test(successes, n, p_null, alternative='two-sided')

        empirical_p_values.append(p_val)

    # Calculate empirical Type I error rate
    alpha = 0.05
    empirical_error_rate = np.mean(np.array(empirical_p_values) < alpha)
    theoretical_error_rate = alpha

    diff = abs(empirical_error_rate - theoretical_error_rate)
    passed = diff <= TOLERANCE

    details = {
        "test_type": "binomial_test",
        "n_replicates": n_replicates,
        "n_trials": n,
        "null_probability": p_null,
        "alpha": alpha,
        "empirical_error_rate": float(empirical_error_rate),
        "theoretical_error_rate": float(theoretical_error_rate),
        "absolute_difference": float(diff),
        "passed": passed,
    }

    logger.info(
        f"Binomial test validation: empirical={empirical_error_rate:.4f}, "
        f"theoretical={theoretical_error_rate:.4f}, diff={diff:.4f}, "
        f"passed={passed}"
    )

    return passed, float(empirical_error_rate), float(theoretical_error_rate), details


def run_monte_carlo_validation(
    n_replicates: int = NUM_REPLICATES,
    seed: int = SEED,
    output_path: Optional[Path] = None,
) -> bool:
    """
    Run full Monte-Carlo validation suite for all statistical tests.

    This function executes validation for:
    - Two-proportion z-test
    - Fisher's exact test
    - Welch's t-test
    - Binomial test

    Each test runs n_replicates simulations and checks if the empirical
    Type I error rate is within TOLERANCE of the theoretical rate (alpha=0.05).

    Args:
        n_replicates: Number of replicates per test.
        seed: Random seed for reproducibility.
        output_path: Optional path to write validation results JSON.

    Returns:
        True if all tests pass, False otherwise.
    """
    set_rng_seed(seed)
    logger = get_default_logger()
    logger.info(f"Running full Monte-Carlo validation suite with {n_replicates} replicates")

    results = []
    all_passed = True

    # Run each validation
    validators = [
        ("z_test", validate_z_test),
        ("fisher_exact", validate_fisher_exact),
        ("welch_t_test", validate_welch_t_test),
        ("binomial_test", validate_binomial_test),
    ]

    for test_name, validator_fn in validators:
        passed, emp_p, theo_p, details = validator_fn(n_replicates, seed)
        results.append(details)
        if not passed:
            all_passed = False
            logger.error(f"Validation FAILED for {test_name}")
        else:
            logger.info(f"Validation PASSED for {test_name}")

    # Write results if output path provided
    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({
                "seed": seed,
                "n_replicates": n_replicates,
                "tolerance": TOLERANCE,
                "all_passed": all_passed,
                "test_results": results,
            }, f, indent=2)
        logger.info(f"Validation results written to {output_path}")

    return all_passed


def main() -> int:
    """
    Main entry point for Monte-Carlo validation script.

    Runs the validation suite and exits with status 0 if all tests pass,
    or status 1 if any test fails.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = get_default_logger()
    logger.info("Starting Monte-Carlo validation module (T062)")

    try:
        # Run validation with default parameters
        all_passed = run_monte_carlo_validation(
            n_replicates=NUM_REPLICATES,
            seed=SEED,
            output_path=Path("output/monte_carlo_validation_results.json"),
        )

        if all_passed:
            logger.info("All Monte-Carlo validations PASSED")
            return 0
        else:
            logger.error("Monte-Carlo validation FAILED - some tests exceeded tolerance")
            return 1

    except Exception as e:
        logger.error(f"Monte-Carlo validation encountered an error: {e}")
        raise


if __name__ == "__main__":
    sys.exit(main())
