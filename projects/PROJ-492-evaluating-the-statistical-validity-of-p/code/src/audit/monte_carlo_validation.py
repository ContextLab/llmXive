"""
Monte-Carlo validation module for statistical test correctness.

This module validates the statistical reconstruction logic by running
10,000 replicates for each test type (z-test, Fisher's exact, Welch's t-test,
binomial test) and comparing the empirical p-value distribution against
theoretical expectations. The absolute difference between the empirical
rejection rate and the nominal alpha must be <= 0.005.
"""
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from scipy import stats

# Import project configuration and logging
from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Constants
NUM_REPLICATES = 10000
ALPHA = 0.05
TOLERANCE = 0.005
RANDOM_SEED = 42

logger = get_default_logger(__name__)
audit_logger = AuditLogger()

def validate_z_test(alpha: float = ALPHA, n_replicates: int = NUM_REPLICATES) -> Tuple[bool, float, float]:
    """
    Validates the two-proportion z-test.

    Generates synthetic data where the null hypothesis is true (p1 = p2),
    runs the z-test, and checks if the empirical rejection rate matches alpha.

    Returns:
        (passed, empirical_rate, theoretical_rate)
    """
    set_rng_seed(RANDOM_SEED)
    n1, n2 = 1000, 1000
    p_true = 0.5

    rejections = 0
    for _ in range(n_replicates):
        # Generate data under null hypothesis
        x1 = np.random.binomial(n1, p_true)
        x2 = np.random.binomial(n2, p_true)

        p1_hat = x1 / n1
        p2_hat = x2 / n2

        # Pooled proportion
        p_pool = (x1 + x2) / (n1 + n2)

        # Standard error
        se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))

        if se == 0:
            continue

        z_stat = (p1_hat - p2_hat) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

        if p_value < alpha:
            rejections += 1

    empirical_rate = rejections / n_replicates
    passed = abs(empirical_rate - alpha) <= TOLERANCE
    return passed, empirical_rate, alpha

def validate_fisher_exact(alpha: float = ALPHA, n_replicates: int = NUM_REPLICATES) -> Tuple[bool, float, float]:
    """
    Validates Fisher's exact test.

    Generates 2x2 contingency tables under the null hypothesis of independence,
    runs Fisher's exact test, and checks the empirical rejection rate.
    """
    set_rng_seed(RANDOM_SEED)
    n1, n2 = 100, 100
    p_true = 0.5

    rejections = 0
    for _ in range(n_replicates):
        # Generate data under null hypothesis
        x1 = np.random.binomial(n1, p_true)
        x2 = np.random.binomial(n2, p_true)

        # Construct contingency table
        # [[x1, n1-x1], [x2, n2-x2]]
        table = [[x1, n1 - x1], [x2, n2 - x2]]

        # Fisher's exact test (two-sided)
        _, p_value = stats.fisher_exact(table, alternative='two-sided')

        if p_value < alpha:
            rejections += 1

    empirical_rate = rejections / n_replicates
    passed = abs(empirical_rate - alpha) <= TOLERANCE
    return passed, empirical_rate, alpha

def validate_welch_t_test(alpha: float = ALPHA, n_replicates: int = NUM_REPLICATES) -> Tuple[bool, float, float]:
    """
    Validates Welch's t-test.

    Generates continuous data under the null hypothesis (mu1 = mu2),
    runs Welch's t-test, and checks the empirical rejection rate.
    """
    set_rng_seed(RANDOM_SEED)
    n1, n2 = 50, 50
    mu_true = 0.0
    sigma = 1.0

    rejections = 0
    for _ in range(n_replicates):
        # Generate data under null hypothesis
        data1 = np.random.normal(mu_true, sigma, n1)
        data2 = np.random.normal(mu_true, sigma, n2)

        # Welch's t-test
        _, p_value = stats.ttest_ind(data1, data2, equal_var=False)

        if p_value < alpha:
            rejections += 1

    empirical_rate = rejections / n_replicates
    passed = abs(empirical_rate - alpha) <= TOLERANCE
    return passed, empirical_rate, alpha

def validate_binomial_test(alpha: float = ALPHA, n_replicates: int = NUM_REPLICATES) -> Tuple[bool, float, float]:
    """
    Validates the binomial test.

    Generates binomial data under the null hypothesis (p = p0),
    runs the binomial test, and checks the empirical rejection rate.
    """
    set_rng_seed(RANDOM_SEED)
    n = 100
    p0 = 0.5

    rejections = 0
    for _ in range(n_replicates):
        # Generate data under null hypothesis
        x = np.random.binomial(n, p0)

        # Binomial test (two-sided)
        # Using scipy.stats.binomtest for exact calculation
        result = stats.binomtest(x, n, p0, alternative='two-sided')
        p_value = result.pvalue

        if p_value < alpha:
            rejections += 1

    empirical_rate = rejections / n_replicates
    passed = abs(empirical_rate - alpha) <= TOLERANCE
    return passed, empirical_rate, alpha

def run_monte_carlo_validation() -> Dict[str, Any]:
    """
    Runs all Monte-Carlo validation tests.

    Returns:
        Dictionary containing results for each test type.
    """
    logger.info("Starting Monte-Carlo validation with %d replicates per test.", NUM_REPLICATES)

    results = {}

    # Z-test
    logger.info("Validating Z-test...")
    z_passed, z_emp, z_theo = validate_z_test()
    results['z_test'] = {
        'passed': z_passed,
        'empirical_rate': z_emp,
        'theoretical_rate': z_theo,
        'difference': abs(z_emp - z_theo)
    }
    if z_passed:
        logger.info("Z-test validation PASSED (diff: %.4f <= %.4f)", abs(z_emp - z_theo), TOLERANCE)
    else:
        logger.error("Z-test validation FAILED (diff: %.4f > %.4f)", abs(z_emp - z_theo), TOLERANCE)
        audit_logger.log_error('ERR-801', f"Z-test validation failed: difference {abs(z_emp - z_theo):.4f} exceeds tolerance {TOLERANCE}")

    # Fisher's exact test
    logger.info("Validating Fisher's exact test...")
    fisher_passed, fisher_emp, fisher_theo = validate_fisher_exact()
    results['fisher_exact'] = {
        'passed': fisher_passed,
        'empirical_rate': fisher_emp,
        'theoretical_rate': fisher_theo,
        'difference': abs(fisher_emp - fisher_theo)
    }
    if fisher_passed:
        logger.info("Fisher's exact test validation PASSED (diff: %.4f <= %.4f)", abs(fisher_emp - fisher_theo), TOLERANCE)
    else:
        logger.error("Fisher's exact test validation FAILED (diff: %.4f > %.4f)", abs(fisher_emp - fisher_theo), TOLERANCE)
        audit_logger.log_error('ERR-801', f"Fisher's exact test validation failed: difference {abs(fisher_emp - fisher_theo):.4f} exceeds tolerance {TOLERANCE}")

    # Welch's t-test
    logger.info("Validating Welch's t-test...")
    welch_passed, welch_emp, welch_theo = validate_welch_t_test()
    results['welch_t_test'] = {
        'passed': welch_passed,
        'empirical_rate': welch_emp,
        'theoretical_rate': welch_theo,
        'difference': abs(welch_emp - welch_theo)
    }
    if welch_passed:
        logger.info("Welch's t-test validation PASSED (diff: %.4f <= %.4f)", abs(welch_emp - welch_theo), TOLERANCE)
    else:
        logger.error("Welch's t-test validation FAILED (diff: %.4f > %.4f)", abs(welch_emp - welch_theo), TOLERANCE)
        audit_logger.log_error('ERR-801', f"Welch's t-test validation failed: difference {abs(welch_emp - welch_theo):.4f} exceeds tolerance {TOLERANCE}")

    # Binomial test
    logger.info("Validating Binomial test...")
    binom_passed, binom_emp, binom_theo = validate_binomial_test()
    results['binomial_test'] = {
        'passed': binom_passed,
        'empirical_rate': binom_emp,
        'theoretical_rate': binom_theo,
        'difference': abs(binom_emp - binom_theo)
    }
    if binom_passed:
        logger.info("Binomial test validation PASSED (diff: %.4f <= %.4f)", abs(binom_emp - binom_theo), TOLERANCE)
    else:
        logger.error("Binomial test validation FAILED (diff: %.4f > %.4f)", abs(binom_emp - binom_theo), TOLERANCE)
        audit_logger.log_error('ERR-801', f"Binomial test validation failed: difference {abs(binom_emp - binom_theo):.4f} exceeds tolerance {TOLERANCE}")

    # Overall status
    all_passed = all([z_passed, fisher_passed, welch_passed, binom_passed])
    results['overall_passed'] = all_passed

    return results

def main():
    """
    Main entry point for the Monte-Carlo validation module.
    """
    try:
        results = run_monte_carlo_validation()

        if results['overall_passed']:
            logger.info("All Monte-Carlo validations PASSED.")
            sys.exit(0)
        else:
            logger.error("One or more Monte-Carlo validations FAILED.")
            sys.exit(1)

    except Exception as e:
        logger.exception("Unexpected error during Monte-Carlo validation: %s", str(e))
        audit_logger.log_error('ERR-801', f"Monte-Carlo validation failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()