"""
Monte-Carlo validation module for statistical tests (FR-026).

Runs 10,000 replicates for each statistical test (z-test, Fisher's exact,
Welch's t-test, binomial test) and validates that the absolute difference
between Monte-Carlo estimates and scipy library results is <= 0.005.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
from scipy import stats
from scipy.stats import proportion

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
N_REPLICATES = 10000
TOLERANCE = 0.005

# Global RNG for reproducibility
rng = np.random.default_rng(42)


def validate_z_test(n_replicates: int = N_REPLICATES) -> Tuple[bool, float, float, float]:
    """
    Validate two-proportion z-test using Monte-Carlo simulation.

    Generates binary outcome data with known parameters, runs z-tests,
    and compares the empirical p-value distribution against scipy's
    analytical result.

    Args:
        n_replicates: Number of Monte-Carlo replicates (default: 10000)

    Returns:
        Tuple of (passed, abs_diff, mc_p, scipy_p)
    """
    logger = get_default_logger()
    logger.info("Validating z-test (two-proportion) with Monte-Carlo...")

    # Generate data with known effect (null hypothesis is true)
    p1, p2 = 0.5, 0.5  # Same proportions under null
    n1, n2 = 200, 200  # Sample sizes

    p_values = []
    for _ in range(n_replicates):
        # Generate binary outcomes
        treatment_successes = rng.binomial(n1, p1)
        control_successes = rng.binomial(n2, p2)

        # Calculate z-statistic using pooled proportion
        p_pooled = (treatment_successes + control_successes) / (n1 + n2)
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))

        p_hat1 = treatment_successes / n1
        p_hat2 = control_successes / n2

        z_stat = (p_hat1 - p_hat2) / se if se > 0 else 0

        # Two-sided p-value from normal distribution
        p = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        p_values.append(p)

    # Compare with scipy's z-test on observed data
    treatment_successes = rng.binomial(n1, p1)
    control_successes = rng.binomial(n2, p2)

    stat, scipy_p = proportion.ztest(
        [treatment_successes, control_successes],
        [n1, n2],
        alternative='two-sided'
    )

    # Calculate Monte Carlo p-value (proportion of p-values <= scipy_p)
    mc_p = sum(1 for p in p_values if p <= scipy_p) / n_replicates

    abs_diff = abs(mc_p - scipy_p)

    logger.info(f"Z-test: MC p={mc_p:.6f}, scipy p={scipy_p:.6f}, diff={abs_diff:.6f}")

    return abs_diff <= TOLERANCE, abs_diff, mc_p, scipy_p


def validate_fisher_exact(n_replicates: int = N_REPLICATES) -> Tuple[bool, float, float, float]:
    """
    Validate Fisher's exact test using Monte-Carlo simulation.

    Generates contingency tables with known parameters and compares
    the empirical p-value distribution against scipy's exact result.

    Args:
        n_replicates: Number of Monte-Carlo replicates (default: 10000)

    Returns:
        Tuple of (passed, abs_diff, mc_p, scipy_p)
    """
    logger = get_default_logger()
    logger.info("Validating Fisher's exact test with Monte-Carlo...")

    # Parameters under null hypothesis
    p1, p2 = 0.5, 0.5
    n1, n2 = 100, 100

    p_values = []
    for _ in range(n_replicates):
        # Generate contingency table
        t_success = rng.binomial(n1, p1)
        t_failure = n1 - t_success
        c_success = rng.binomial(n2, p2)
        c_failure = n2 - c_success

        table = [[t_success, t_failure], [c_success, c_failure]]
        _, p = stats.fisher_exact(table, alternative='two-sided')
        p_values.append(p)

    # Compare with scipy's Fisher's exact test on observed data
    t_success = rng.binomial(n1, p1)
    t_failure = n1 - t_success
    c_success = rng.binomial(n2, p2)
    c_failure = n2 - c_success

    observed_table = [[t_success, t_failure], [c_success, c_failure]]
    _, scipy_p = stats.fisher_exact(observed_table, alternative='two-sided')

    # Calculate Monte Carlo p-value
    mc_p = sum(1 for p in p_values if p <= scipy_p) / n_replicates

    abs_diff = abs(mc_p - scipy_p)

    logger.info(f"Fisher's exact: MC p={mc_p:.6f}, scipy p={scipy_p:.6f}, diff={abs_diff:.6f}")

    return abs_diff <= TOLERANCE, abs_diff, mc_p, scipy_p


def validate_welch_t_test(n_replicates: int = N_REPLICATES) -> Tuple[bool, float, float, float]:
    """
    Validate Welch's t-test using Monte-Carlo simulation.

    Generates continuous outcome data with known parameters and compares
    the empirical p-value distribution against scipy's result.

    Args:
        n_replicates: Number of Monte-Carlo replicates (default: 10000)

    Returns:
        Tuple of (passed, abs_diff, mc_p, scipy_p)
    """
    logger = get_default_logger()
    logger.info("Validating Welch's t-test with Monte-Carlo...")

    # Parameters under null hypothesis (same means)
    mu1, mu2 = 0.0, 0.0
    sigma1, sigma2 = 1.0, 1.0
    n1, n2 = 100, 100

    p_values = []
    for _ in range(n_replicates):
        # Generate continuous data
        treatment = rng.normal(mu1, sigma1, n1)
        control = rng.normal(mu2, sigma2, n2)

        # Calculate Welch's t-statistic
        mean1, mean2 = treatment.mean(), control.mean()
        var1, var2 = treatment.var(ddof=1), control.var(ddof=1)

        se = np.sqrt(var1/n1 + var2/n2)
        t_stat = (mean1 - mean2) / se if se > 0 else 0

        # Welch-Satterthwaite degrees of freedom
        df = (var1/n1 + var2/n2)**2 / ((var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1))

        # Two-sided p-value
        p = 2 * (1 - stats.t.cdf(abs(t_stat), df))
        p_values.append(p)

    # Compare with scipy's Welch's t-test on observed data
    treatment = rng.normal(mu1, sigma1, n1)
    control = rng.normal(mu2, sigma2, n2)

    _, scipy_p = stats.ttest_ind(treatment, control, equal_var=False)

    # Calculate Monte Carlo p-value
    mc_p = sum(1 for p in p_values if p <= scipy_p) / n_replicates

    abs_diff = abs(mc_p - scipy_p)

    logger.info(f"Welch's t-test: MC p={mc_p:.6f}, scipy p={scipy_p:.6f}, diff={abs_diff:.6f}")

    return abs_diff <= TOLERANCE, abs_diff, mc_p, scipy_p


def validate_binomial_test(n_replicates: int = N_REPLICATES) -> Tuple[bool, float, float, float]:
    """
    Validate binomial test using Monte-Carlo simulation.

    Generates binomial data with known parameters and compares
    the empirical p-value distribution against scipy's exact result.

    Args:
        n_replicates: Number of Monte-Carlo replicates (default: 10000)

    Returns:
        Tuple of (passed, abs_diff, mc_p, scipy_p)
    """
    logger = get_default_logger()
    logger.info("Validating binomial test with Monte-Carlo...")

    # Parameters under null hypothesis
    p_null = 0.5
    n = 100

    p_values = []
    for _ in range(n_replicates):
        # Generate binomial outcome
        successes = rng.binomial(n, p_null)

        # Calculate two-sided binomial p-value
        # P(X <= successes) + P(X >= successes) for two-sided
        if successes <= n * p_null:
            p_lower = stats.binom.cdf(successes, n, p_null)
            p_upper = 1 - stats.binom.cdf(successes - 1, n, p_null)
        else:
            p_lower = stats.binom.cdf(successes - 1, n, p_null)
            p_upper = 1 - stats.binom.cdf(successes, n, p_null)

        p = min(p_lower + p_upper, 1.0)
        p_values.append(p)

    # Compare with scipy's binomial test on observed data
    successes = rng.binomial(n, p_null)

    # scipy.stats.binomtest is the modern interface
    result = stats.binomtest(successes, n, p_null, alternative='two-sided')
    scipy_p = result.pvalue

    # Calculate Monte Carlo p-value
    mc_p = sum(1 for p in p_values if p <= scipy_p) / n_replicates

    abs_diff = abs(mc_p - scipy_p)

    logger.info(f"Binomial test: MC p={mc_p:.6f}, scipy p={scipy_p:.6f}, diff={abs_diff:.6f}")

    return abs_diff <= TOLERANCE, abs_diff, mc_p, scipy_p


def run_monte_carlo_validation() -> Dict[str, Any]:
    """
    Run Monte-Carlo validation for all statistical tests.

    Returns:
        Dictionary with validation results for each test type
    """
    results = {
        'z_test': {},
        'fisher_exact': {},
        'welch_t_test': {},
        'binomial_test': {}
    }

    logger = get_default_logger()
    logger.info(f"Starting Monte-Carlo validation with {N_REPLICATES} replicates per test")

    # Validate z-test
    passed, diff, mc_p, scipy_p = validate_z_test()
    results['z_test'] = {
        'passed': passed,
        'abs_diff': diff,
        'tolerance': TOLERANCE,
        'mc_p_value': mc_p,
        'scipy_p_value': scipy_p
    }

    # Validate Fisher's exact test
    passed, diff, mc_p, scipy_p = validate_fisher_exact()
    results['fisher_exact'] = {
        'passed': passed,
        'abs_diff': diff,
        'tolerance': TOLERANCE,
        'mc_p_value': mc_p,
        'scipy_p_value': scipy_p
    }

    # Validate Welch's t-test
    passed, diff, mc_p, scipy_p = validate_welch_t_test()
    results['welch_t_test'] = {
        'passed': passed,
        'abs_diff': diff,
        'tolerance': TOLERANCE,
        'mc_p_value': mc_p,
        'scipy_p_value': scipy_p
    }

    # Validate binomial test
    passed, diff, mc_p, scipy_p = validate_binomial_test()
    results['binomial_test'] = {
        'passed': passed,
        'abs_diff': diff,
        'tolerance': TOLERANCE,
        'mc_p_value': mc_p,
        'scipy_p_value': scipy_p
    }

    # Overall result
    all_passed = all(r['passed'] for r in results.values())

    logger.info(f"Monte-Carlo validation complete: {'PASSED' if all_passed else 'FAILED'}")

    return {
        'all_passed': all_passed,
        'n_replicates': N_REPLICATES,
        'tolerance': TOLERANCE,
        'test_results': results
    }


def main():
    """
    Main entry point for Monte-Carlo validation.

    Sets random seed, runs validation, and exits with appropriate status code.
    Exits with 0 if all tests pass, 1 if any test fails.
    """
    # Set RNG seed for reproducibility (Constitution Principle I)
    set_rng_seed(42)

    logger = get_default_logger()
    logger.info("=" * 60)
    logger.info("Monte-Carlo Statistical Test Validation (FR-026)")
    logger.info("=" * 60)

    # Run validation
    results = run_monte_carlo_validation()

    # Print summary
    print("\n" + "=" * 60)
    print("MONTE-CARLO VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Replicates per test: {results['n_replicates']}")
    print(f"Tolerance threshold: {results['tolerance']}")
    print()

    for test_name, test_result in results['test_results'].items():
        status = "PASS" if test_result['passed'] else "FAIL"
        print(f"{test_name}: {status}")
        print(f"  - Absolute difference: {test_result['abs_diff']:.6f}")
        print(f"  - MC p-value: {test_result['mc_p_value']:.6f}")
        print(f"  - Scipy p-value: {test_result['scipy_p_value']:.6f}")
        print()

    overall_status = "ALL TESTS PASSED" if results['all_passed'] else "SOME TESTS FAILED"
    print(f"Overall: {overall_status}")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if results['all_passed'] else 1)


if __name__ == '__main__':
    main()