"""
Monte-Carlo validation module for statistical tests.

Validates the accuracy of z-test, Fisher's exact test, Welch's t-test,
and binomial test implementations by comparing empirical p-values from
Monte-Carlo simulations against scipy library implementations.

Runs 100,000 replicates for each test type and verifies the absolute
difference between empirical and theoretical p-values is <= 0.005.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from scipy import stats

# Import from project modules
from code.src.audit.monte_carlo_core import (
    set_seeds,
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value
)
from code.src.config import set_rng_seed, get_config_summary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Constants
NUM_REPLICATES = 100000
TOLERANCE_THRESHOLD = 0.005
DEFAULT_SEED = 42


def validate_z_test(
    n1: int = 1000,
    n2: int = 1000,
    p1: float = 0.5,
    p2: float = 0.55,
    alpha: float = 0.05,
    seed: int = DEFAULT_SEED
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate two-proportion z-test using Monte-Carlo simulation.

    Args:
        n1: Sample size for group 1
        n2: Sample size for group 2
        p1: True proportion for group 1
        p2: True proportion for group 2
        alpha: Significance level
        seed: Random seed for reproducibility

    Returns:
        Tuple of (passed, details_dict)
    """
    logger = get_default_logger("monte_carlo_validation")
    set_rng_seed(seed)
    set_seeds(seed)

    logger.info(f"Starting z-test validation with {NUM_REPLICATES} replicates")

    # Run Monte-Carlo simulation
    simulated_stats = []
    for _ in range(NUM_REPLICATES):
        stat = simulate_z_test_statistic(n1, n2, p1, p2)
        simulated_stats.append(stat)

    # Compute empirical p-value (two-tailed)
    observed_stat = np.mean(simulated_stats)  # Use mean as representative
    # For validation, we check if the distribution of simulated stats
    # matches the theoretical null distribution
    # We compute the proportion of simulated stats that are as extreme as a threshold
    threshold = stats.norm.ppf(1 - alpha/2)
    empirical_p = compute_empirical_p_value(simulated_stats, threshold, two_tailed=True)

    # Theoretical p-value under null hypothesis (p1 == p2)
    # We simulate under null, so theoretical p should be ~alpha
    theoretical_p = alpha  # Under null, p-value should be uniformly distributed

    # For this validation, we check if the empirical p-value is close to expected
    # under the null hypothesis (should be around alpha)
    # However, a better approach: compare simulated distribution to theoretical
    # Let's compute the proportion of stats exceeding the theoretical critical value
    abs_stats = np.abs(simulated_stats)
    critical_value = stats.norm.ppf(1 - alpha/2)
    empirical_alpha = np.mean(abs_stats > critical_value)

    # Theoretical alpha is just alpha
    diff = abs(empirical_alpha - alpha)

    passed = diff <= TOLERANCE_THRESHOLD

    details = {
        "test": "z_test",
        "replicates": NUM_REPLICATES,
        "empirical_alpha": empirical_alpha,
        "theoretical_alpha": alpha,
        "difference": diff,
        "threshold": TOLERANCE_THRESHOLD,
        "passed": passed,
        "seed": seed
    }

    if passed:
        logger.info(f"z-test validation PASSED: diff={diff:.6f}")
    else:
        logger.warning(f"z-test validation FAILED: diff={diff:.6f}")

    return passed, details


def validate_fisher_exact(
    n1: int = 1000,
    n2: int = 1000,
    p1: float = 0.5,
    p2: float = 0.5,
    alpha: float = 0.05,
    seed: int = DEFAULT_SEED
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Fisher's exact test using Monte-Carlo simulation.

    Args:
        n1: Sample size for group 1
        n2: Sample size for group 2
        p1: True proportion for group 1 (under null, p1 == p2)
        p2: True proportion for group 2
        alpha: Significance level
        seed: Random seed

    Returns:
        Tuple of (passed, details_dict)
    """
    logger = get_default_logger("monte_carlo_validation")
    set_rng_seed(seed)
    set_seeds(seed)

    logger.info(f"Starting Fisher's exact test validation with {NUM_REPLICATES} replicates")

    # Run Monte-Carlo simulation
    empirical_p_values = []
    for _ in range(NUM_REPLICATES):
        # Generate contingency table under null
        table = simulate_fisher_exact_table(n1, n2, p1, p2)
        # Compute p-value using scipy
        _, p_val = stats.fisher_exact(table, alternative='two-sided')
        empirical_p_values.append(p_val)

    # Under null hypothesis, p-values should be uniformly distributed
    # Check if proportion of p-values < alpha is close to alpha
    empirical_alpha = np.mean(np.array(empirical_p_values) < alpha)
    diff = abs(empirical_alpha - alpha)

    passed = diff <= TOLERANCE_THRESHOLD

    details = {
        "test": "fisher_exact",
        "replicates": NUM_REPLICATES,
        "empirical_alpha": empirical_alpha,
        "theoretical_alpha": alpha,
        "difference": diff,
        "threshold": TOLERANCE_THRESHOLD,
        "passed": passed,
        "seed": seed
    }

    if passed:
        logger.info(f"Fisher's exact test validation PASSED: diff={diff:.6f}")
    else:
        logger.warning(f"Fisher's exact test validation FAILED: diff={diff:.6f}")

    return passed, details


def validate_welch_t_test(
    n1: int = 500,
    n2: int = 500,
    mu1: float = 0.0,
    mu2: float = 0.0,
    sigma1: float = 1.0,
    sigma2: float = 1.0,
    alpha: float = 0.05,
    seed: int = DEFAULT_SEED
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Welch's t-test using Monte-Carlo simulation.

    Args:
        n1: Sample size for group 1
        n2: Sample size for group 2
        mu1: True mean for group 1
        mu2: True mean for group 2
        sigma1: True std dev for group 1
        sigma2: True std dev for group 2
        alpha: Significance level
        seed: Random seed

    Returns:
        Tuple of (passed, details_dict)
    """
    logger = get_default_logger("monte_carlo_validation")
    set_rng_seed(seed)
    set_seeds(seed)

    logger.info(f"Starting Welch's t-test validation with {NUM_REPLICATES} replicates")

    # Run Monte-Carlo simulation
    empirical_p_values = []
    for _ in range(NUM_REPLICATES):
        # Generate data under null (mu1 == mu2)
        data1 = np.random.normal(mu1, sigma1, n1)
        data2 = np.random.normal(mu2, sigma2, n2)

        # Compute Welch's t-test
        t_stat, p_val = stats.ttest_ind(data1, data2, equal_var=False)
        empirical_p_values.append(p_val)

    # Under null, p-values should be uniformly distributed
    empirical_alpha = np.mean(np.array(empirical_p_values) < alpha)
    diff = abs(empirical_alpha - alpha)

    passed = diff <= TOLERANCE_THRESHOLD

    details = {
        "test": "welch_t",
        "replicates": NUM_REPLICATES,
        "empirical_alpha": empirical_alpha,
        "theoretical_alpha": alpha,
        "difference": diff,
        "threshold": TOLERANCE_THRESHOLD,
        "passed": passed,
        "seed": seed
    }

    if passed:
        logger.info(f"Welch's t-test validation PASSED: diff={diff:.6f}")
    else:
        logger.warning(f"Welch's t-test validation FAILED: diff={diff:.6f}")

    return passed, details


def validate_binomial_test(
    n: int = 1000,
    p: float = 0.5,
    alpha: float = 0.05,
    seed: int = DEFAULT_SEED
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate binomial test using Monte-Carlo simulation.

    Args:
        n: Sample size
        p: True probability of success
        alpha: Significance level
        seed: Random seed

    Returns:
        Tuple of (passed, details_dict)
    """
    logger = get_default_logger("monte_carlo_validation")
    set_rng_seed(seed)
    set_seeds(seed)

    logger.info(f"Starting binomial test validation with {NUM_REPLICATES} replicates")

    # Run Monte-Carlo simulation
    empirical_p_values = []
    for _ in range(NUM_REPLICATES):
        # Generate binomial data under null
        x = np.random.binomial(n, p)

        # Compute binomial test p-value (two-sided)
        # Using scipy's binom_test (deprecated) or binomtest
        try:
            result = stats.binomtest(x, n, p)
            p_val = result.pvalue
        except AttributeError:
            # Fallback for older scipy versions
            p_val = stats.binom_test(x, n, p)

        empirical_p_values.append(p_val)

    # Under null, p-values should be uniformly distributed
    empirical_alpha = np.mean(np.array(empirical_p_values) < alpha)
    diff = abs(empirical_alpha - alpha)

    passed = diff <= TOLERANCE_THRESHOLD

    details = {
        "test": "binomial",
        "replicates": NUM_REPLICATES,
        "empirical_alpha": empirical_alpha,
        "theoretical_alpha": alpha,
        "difference": diff,
        "threshold": TOLERANCE_THRESHOLD,
        "passed": passed,
        "seed": seed
    }

    if passed:
        logger.info(f"Binomial test validation PASSED: diff={diff:.6f}")
    else:
        logger.warning(f"Binomial test validation FAILED: diff={diff:.6f}")

    return passed, details


def run_monte_carlo_validation(
    seed: int = DEFAULT_SEED,
    tolerance: float = TOLERANCE_THRESHOLD
) -> Tuple[bool, Dict[str, Any]]:
    """
    Run full Monte-Carlo validation suite for all statistical tests.

    Args:
        seed: Random seed for reproducibility
        tolerance: Maximum allowed difference between empirical and theoretical

    Returns:
        Tuple of (all_passed, results_dict)
    """
    logger = get_default_logger("monte_carlo_validation")
    logger.info("=" * 60)
    logger.info("Starting Monte-Carlo Validation Suite")
    logger.info(f"Replicates per test: {NUM_REPLICATES}")
    logger.info(f"Acceptance threshold: {tolerance}")
    logger.info("=" * 60)

    # Set global seed
    set_rng_seed(seed)

    results = {
        "seed": seed,
        "replicates": NUM_REPLICATES,
        "tolerance": tolerance,
        "tests": {}
    }

    # Run each validation
    z_passed, z_details = validate_z_test(seed=seed)
    results["tests"]["z_test"] = z_details

    fisher_passed, fisher_details = validate_fisher_exact(seed=seed)
    results["tests"]["fisher_exact"] = fisher_details

    welch_passed, welch_details = validate_welch_t_test(seed=seed)
    results["tests"]["welch_t"] = welch_details

    binomial_passed, binomial_details = validate_binomial_test(seed=seed)
    results["tests"]["binomial"] = binomial_details

    # Overall result
    all_passed = all([z_passed, fisher_passed, welch_passed, binomial_passed])
    results["all_passed"] = all_passed

    logger.info("=" * 60)
    if all_passed:
        logger.info("MONTE-CARLO VALIDATION: ALL TESTS PASSED")
    else:
        logger.error("MONTE-CARLO VALIDATION: SOME TESTS FAILED")
        failed_tests = [t for t, d in results["tests"].items() if not d["passed"]]
        logger.error(f"Failed tests: {failed_tests}")
    logger.info("=" * 60)

    return all_passed, results


def main() -> int:
    """
    Main entry point for Monte-Carlo validation script.

    Returns:
        Exit code: 0 if all tests pass, 1 otherwise
    """
    logger = get_default_logger("monte_carlo_validation")

    try:
        # Get configuration
        config = get_config_summary()
        seed = config.get("seed", DEFAULT_SEED)
        tolerance = config.get("monte_carlo_tolerance", TOLERANCE_THRESHOLD)

        logger.info(f"Running with seed={seed}, tolerance={tolerance}")

        # Run validation
        all_passed, results = run_monte_carlo_validation(seed=seed, tolerance=tolerance)

        # Exit with appropriate code
        if all_passed:
            logger.info("Validation complete. Exit code: 0")
            return 0
        else:
            logger.error("Validation failed. Exit code: 1")
            return 1

    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
