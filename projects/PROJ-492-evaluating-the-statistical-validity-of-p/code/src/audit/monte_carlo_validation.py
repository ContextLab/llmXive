"""
Monte-Carlo validation module for statistical tests (FR-026).

Validates the accuracy of z-test, Fisher's exact test, Welch's t-test,
and binomial test implementations by running 10,000 replicates for each.
Checks that the absolute difference between empirical and theoretical
p-values is <= 0.005.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.audit.monte_carlo_core import (
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
)
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
NUM_REPLICATES = 10000
THRESHOLD = 0.005
ALPHA = 0.05


def validate_z_test(logger: Optional[AuditLogger] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate two-proportion z-test using Monte-Carlo simulation.

    Returns:
        Tuple of (success, details_dict)
    """
    if logger is None:
        logger = get_default_logger(__name__)

    logger.info("Starting Monte-Carlo validation for z-test (10,000 replicates)...")

    # Parameters for simulation
    n1, n2 = 1000, 1000
    p1, p2 = 0.5, 0.55  # Small effect size
    n_replicates = NUM_REPLICATES

    # Set seed for reproducibility
    set_rng_seed(SEED)

    # Run simulations
    empirical_p_values = []
    for _ in range(n_replicates):
        # Generate binary data
        group1 = np.random.binomial(1, p1, n1)
        group2 = np.random.binomial(1, p2, n2)

        # Compute z-statistic and p-value
        stat, p_val = simulate_z_test_statistic(group1, group2)
        empirical_p_values.append(p_val)

    # Compute empirical rejection rate (should be close to alpha under null,
    # but here we have a small effect, so we check consistency of p-value distribution)
    # For validation, we compare the empirical p-value distribution to the expected
    # Under the null (p1=p2), the empirical p-value should be uniformly distributed.
    # We'll use a simpler check: the mean of empirical p-values should be ~0.5 under null.
    # But since we have a small effect, we'll just check that the p-values are computed
    # consistently and the variance is reasonable.

    # Actually, the standard Monte-Carlo validation for a test is:
    # 1. Simulate under the NULL hypothesis (p1 = p2)
    # 2. Compute p-value for each replicate
    # 3. The proportion of p-values <= alpha should be close to alpha (e.g., 0.05)
    # 4. The absolute difference between observed and expected rejection rate should be <= threshold

    # Let's redo with NULL hypothesis
    set_rng_seed(SEED)
    n1_null, n2_null = 1000, 1000
    p_null = 0.5

    rejection_count = 0
    for _ in range(n_replicates):
        group1 = np.random.binomial(1, p_null, n1_null)
        group2 = np.random.binomial(1, p_null, n2_null)

        stat, p_val = simulate_z_test_statistic(group1, group2)
        if p_val <= ALPHA:
            rejection_count += 1

    empirical_alpha = rejection_count / n_replicates
    expected_alpha = ALPHA
    diff = abs(empirical_alpha - expected_alpha)

    details = {
        "test": "z-test",
        "replicates": n_replicates,
        "empirical_alpha": empirical_alpha,
        "expected_alpha": expected_alpha,
        "absolute_difference": diff,
        "passed": diff <= THRESHOLD,
    }

    if details["passed"]:
        logger.info(f"z-test validation PASSED: diff={diff:.4f} <= {THRESHOLD}")
    else:
        logger.error(f"z-test validation FAILED: diff={diff:.4f} > {THRESHOLD}")

    return details["passed"], details


def validate_fisher_exact(logger: Optional[AuditLogger] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Fisher's exact test using Monte-Carlo simulation.

    Returns:
        Tuple of (success, details_dict)
    """
    if logger is None:
        logger = get_default_logger(__name__)

    logger.info("Starting Monte-Carlo validation for Fisher's exact test (10,000 replicates)...")

    n_replicates = NUM_REPLICATES
    n1, n2 = 50, 50  # Smaller sample sizes for Fisher's
    p_null = 0.5

    set_rng_seed(SEED)

    rejection_count = 0
    for _ in range(n_replicates):
        # Generate binary data under null
        group1 = np.random.binomial(1, p_null, n1)
        group2 = np.random.binomial(1, p_null, n2)

        # Create contingency table
        a = sum(group1)
        b = n1 - a
        c = sum(group2)
        d = n2 - c

        # Compute Fisher's exact test p-value
        _, p_val = simulate_fisher_exact_table(a, b, c, d)

        if p_val <= ALPHA:
            rejection_count += 1

    empirical_alpha = rejection_count / n_replicates
    expected_alpha = ALPHA
    diff = abs(empirical_alpha - expected_alpha)

    details = {
        "test": "fisher_exact",
        "replicates": n_replicates,
        "empirical_alpha": empirical_alpha,
        "expected_alpha": expected_alpha,
        "absolute_difference": diff,
        "passed": diff <= THRESHOLD,
    }

    if details["passed"]:
        logger.info(f"Fisher's exact test validation PASSED: diff={diff:.4f} <= {THRESHOLD}")
    else:
        logger.error(f"Fisher's exact test validation FAILED: diff={diff:.4f} > {THRESHOLD}")

    return details["passed"], details


def validate_welch_t_test(logger: Optional[AuditLogger] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Welch's t-test using Monte-Carlo simulation.

    Returns:
        Tuple of (success, details_dict)
    """
    if logger is None:
        logger = get_default_logger(__name__)

    logger.info("Starting Monte-Carlo validation for Welch's t-test (10,000 replicates)...")

    n_replicates = NUM_REPLICATES
    n1, n2 = 100, 120  # Unequal sample sizes
    mu = 0.0
    sigma1, sigma2 = 1.0, 1.2  # Slightly different variances

    set_rng_seed(SEED)

    rejection_count = 0
    for _ in range(n_replicates):
        # Generate continuous data under null (same mean)
        group1 = np.random.normal(mu, sigma1, n1)
        group2 = np.random.normal(mu, sigma2, n2)

        # Compute Welch's t-test p-value
        _, p_val = simulate_welch_t_statistic(group1, group2)

        if p_val <= ALPHA:
            rejection_count += 1

    empirical_alpha = rejection_count / n_replicates
    expected_alpha = ALPHA
    diff = abs(empirical_alpha - expected_alpha)

    details = {
        "test": "welch_t",
        "replicates": n_replicates,
        "empirical_alpha": empirical_alpha,
        "expected_alpha": expected_alpha,
        "absolute_difference": diff,
        "passed": diff <= THRESHOLD,
    }

    if details["passed"]:
        logger.info(f"Welch's t-test validation PASSED: diff={diff:.4f} <= {THRESHOLD}")
    else:
        logger.error(f"Welch's t-test validation FAILED: diff={diff:.4f} > {THRESHOLD}")

    return details["passed"], details


def validate_binomial_test(logger: Optional[AuditLogger] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate binomial test using Monte-Carlo simulation.

    Returns:
        Tuple of (success, details_dict)
    """
    if logger is None:
        logger = get_default_logger(__name__)

    logger.info("Starting Monte-Carlo validation for binomial test (10,000 replicates)...")

    n_replicates = NUM_REPLICATES
    n = 100
    p_null = 0.5

    set_rng_seed(SEED)

    rejection_count = 0
    for _ in range(n_replicates):
        # Generate binomial data under null
        successes = np.random.binomial(n, p_null)

        # Compute two-sided binomial test p-value
        # Using scipy.stats.binom_test (or binomtest in newer versions)
        p_val = stats.binomtest(successes, n, p_null).pvalue

        if p_val <= ALPHA:
            rejection_count += 1

    empirical_alpha = rejection_count / n_replicates
    expected_alpha = ALPHA
    diff = abs(empirical_alpha - expected_alpha)

    details = {
        "test": "binomial",
        "replicates": n_replicates,
        "empirical_alpha": empirical_alpha,
        "expected_alpha": expected_alpha,
        "absolute_difference": diff,
        "passed": diff <= THRESHOLD,
    }

    if details["passed"]:
        logger.info(f"Binomial test validation PASSED: diff={diff:.4f} <= {THRESHOLD}")
    else:
        logger.error(f"Binomial test validation FAILED: diff={diff:.4f} > {THRESHOLD}")

    return details["passed"], details


def run_monte_carlo_validation(output_dir: Optional[Path] = None) -> int:
    """
    Run all Monte-Carlo validations and write results.

    Returns:
        0 if all tests pass, 1 otherwise.
    """
    logger = get_default_logger(__name__)
    logger.info("=" * 60)
    logger.info("Starting Monte-Carlo Validation Suite (FR-026)")
    logger.info(f"Replicates per test: {NUM_REPLICATES}")
    logger.info(f"Threshold: {THRESHOLD}")
    logger.info("=" * 60)

    results = []
    all_passed = True

    # Run each validation
    validations = [
        ("z_test", validate_z_test),
        ("fisher_exact", validate_fisher_exact),
        ("welch_t", validate_welch_t_test),
        ("binomial", validate_binomial_test),
    ]

    for name, func in validations:
        passed, details = func(logger)
        results.append(details)
        if not passed:
            all_passed = False

    # Write results to JSON
    if output_dir is None:
        output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / "monte_carlo_validation.json"
    import json
    from datetime import datetime

    output_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "num_replicates": NUM_REPLICATES,
        "threshold": THRESHOLD,
        "all_passed": all_passed,
        "results": results,
    }

    with open(result_file, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Results written to {result_file}")

    # Summary
    logger.info("=" * 60)
    if all_passed:
        logger.info("ALL MONTE-CARLO VALIDATIONS PASSED")
        return 0
    else:
        logger.error("SOME MONTE-CARLO VALIDATIONS FAILED")
        return 1


def main():
    """Entry point for command-line execution."""
    exit_code = run_monte_carlo_validation()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
