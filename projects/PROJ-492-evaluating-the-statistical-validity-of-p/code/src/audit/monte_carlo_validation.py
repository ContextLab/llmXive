"""
Monte-Carlo Validation Module (FR-026)

Validates the statistical correctness of z-test, Fisher's exact test,
Welch's t-test, and binomial test implementations by running Monte-Carlo
simulations and comparing empirical p-values against theoretical expectations.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.audit.monte_carlo_core import (
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
)

# Configuration
N_REPLICATES = 100000  # 100,000 replicates per test
TOLERANCE = 0.005      # Maximum allowed absolute difference
ALPHA = 0.05           # Significance level for theoretical p-value

# Initialize logger
logger = get_default_logger(__name__)
audit_logger = AuditLogger(logger)


def validate_z_test(n_replicates: int = N_REPLICATES) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate two-proportion z-test consistency via Monte-Carlo simulation.

    Generates data under the null hypothesis (p1 = p2) and checks if the
    empirical p-value distribution matches the theoretical uniform distribution.
    Specifically checks if the rejection rate at alpha=0.05 is close to 0.05.
    """
    set_rng_seed(SEED)

    # Parameters for simulation under null
    n1, n2 = 100, 100
    p1, p2 = 0.5, 0.5  # Null hypothesis: equal proportions

    rejections = 0
    p_values = []

    for _ in range(n_replicates):
        # Generate binary data under null
        x1 = np.random.binomial(1, p1, n1)
        x2 = np.random.binomial(1, p2, n2)
        
        # Calculate proportions
        prop1 = x1.sum() / n1
        prop2 = x2.sum() / n2
        
        # Pooled proportion
        p_pooled = (x1.sum() + x2.sum()) / (n1 + n2)
        
        # Standard error
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
        
        # Z-statistic
        if se > 0:
            z_stat = (prop1 - prop2) / se
            # Two-tailed p-value
            p_val = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        else:
            p_val = 1.0
        
        p_values.append(p_val)
        if p_val < ALPHA:
            rejections += 1

    empirical_alpha = rejections / n_replicates
    theoretical_alpha = ALPHA
    diff = abs(empirical_alpha - theoretical_alpha)
    passed = diff <= TOLERANCE

    result = {
        "test": "z-test",
        "n_replicates": n_replicates,
        "theoretical_alpha": theoretical_alpha,
        "empirical_alpha": empirical_alpha,
        "absolute_difference": diff,
        "passed": passed,
        "tolerance": TOLERANCE
    }

    return passed, result


def validate_fisher_exact(n_replicates: int = N_REPLICATES) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Fisher's exact test consistency via Monte-Carlo simulation.

    Generates 2x2 contingency tables under the null hypothesis and checks
    if the empirical rejection rate matches the theoretical alpha.
    """
    set_rng_seed(SEED + 1)  # Offset seed

    # Parameters: balanced design under null
    n1, n2 = 50, 50
    p1, p2 = 0.4, 0.4  # Null hypothesis

    rejections = 0

    for _ in range(n_replicates):
        # Generate counts
        a = np.random.binomial(n1, p1)
        b = n1 - a
        c = np.random.binomial(n2, p2)
        d = n2 - c

        # Fisher's exact test
        # scipy.stats.fisher_exact returns (odds_ratio, p_value)
        _, p_val = stats.fisher_exact([[a, b], [c, d]], alternative='two-sided')
        
        if p_val < ALPHA:
            rejections += 1

    empirical_alpha = rejections / n_replicates
    theoretical_alpha = ALPHA
    diff = abs(empirical_alpha - theoretical_alpha)
    passed = diff <= TOLERANCE

    result = {
        "test": "fisher-exact",
        "n_replicates": n_replicates,
        "theoretical_alpha": theoretical_alpha,
        "empirical_alpha": empirical_alpha,
        "absolute_difference": diff,
        "passed": passed,
        "tolerance": TOLERANCE
    }

    return passed, result


def validate_welch_t_test(n_replicates: int = N_REPLICATES) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Welch's t-test consistency via Monte-Carlo simulation.

    Generates continuous data under the null hypothesis (equal means)
    and checks if the empirical rejection rate matches theoretical alpha.
    """
    set_rng_seed(SEED + 2)

    # Parameters under null
    n1, n2 = 30, 30
    mu1, mu2 = 10.0, 10.0
    sigma1, sigma2 = 2.0, 2.5  # Unequal variances (Welch's handles this)

    rejections = 0

    for _ in range(n_replicates):
        x1 = np.random.normal(mu1, sigma1, n1)
        x2 = np.random.normal(mu2, sigma2, n2)

        # Welch's t-test
        _, p_val = stats.ttest_ind(x1, x2, equal_var=False)

        if p_val < ALPHA:
            rejections += 1

    empirical_alpha = rejections / n_replicates
    theoretical_alpha = ALPHA
    diff = abs(empirical_alpha - theoretical_alpha)
    passed = diff <= TOLERANCE

    result = {
        "test": "welch-t",
        "n_replicates": n_replicates,
        "theoretical_alpha": theoretical_alpha,
        "empirical_alpha": empirical_alpha,
        "absolute_difference": diff,
        "passed": passed,
        "tolerance": TOLERANCE
    }

    return passed, result


def validate_binomial_test(n_replicates: int = N_REPLICATES) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate binomial test consistency via Monte-Carlo simulation.

    Generates binomial data under the null hypothesis and checks
    if the empirical rejection rate matches theoretical alpha.
    """
    set_rng_seed(SEED + 3)

    # Parameters under null
    n = 100
    p_null = 0.5
    p_true = 0.5

    rejections = 0

    for _ in range(n_replicates):
        x = np.random.binomial(n, p_true)
        
        # Two-tailed binomial test
        # scipy.stats.binom_test is deprecated, use binomtest
        result = stats.binomtest(x, n, p_null, alternative='two-sided')
        p_val = result.pvalue

        if p_val < ALPHA:
            rejections += 1

    empirical_alpha = rejections / n_replicates
    theoretical_alpha = ALPHA
    diff = abs(empirical_alpha - theoretical_alpha)
    passed = diff <= TOLERANCE

    result = {
        "test": "binomial",
        "n_replicates": n_replicates,
        "theoretical_alpha": theoretical_alpha,
        "empirical_alpha": empirical_alpha,
        "absolute_difference": diff,
        "passed": passed,
        "tolerance": TOLERANCE
    }

    return passed, result


def run_monte_carlo_validation(output_path: Path = None) -> Dict[str, Any]:
    """
    Run all Monte-Carlo validation tests and aggregate results.

    Args:
        output_path: Optional path to write results JSON. If None, results
                    are only logged.

    Returns:
        Dictionary containing validation results for all tests.
    """
    logger.info("Starting Monte-Carlo validation with %d replicates per test", N_REPLICATES)
    
    results = {
        "n_replicates": N_REPLICATES,
        "tolerance": TOLERANCE,
        "alpha": ALPHA,
        "tests": {},
        "overall_passed": True
    }

    # Run z-test validation
    logger.info("Validating z-test...")
    passed, res = validate_z_test(N_REPLICATES)
    results["tests"]["z-test"] = res
    results["overall_passed"] = results["overall_passed"] and passed
    logger.info("Z-test: %s (diff=%.4f)", "PASSED" if passed else "FAILED", res["absolute_difference"])

    # Run Fisher's exact test validation
    logger.info("Validating Fisher's exact test...")
    passed, res = validate_fisher_exact(N_REPLICATES)
    results["tests"]["fisher-exact"] = res
    results["overall_passed"] = results["overall_passed"] and passed
    logger.info("Fisher's exact: %s (diff=%.4f)", "PASSED" if passed else "FAILED", res["absolute_difference"])

    # Run Welch's t-test validation
    logger.info("Validating Welch's t-test...")
    passed, res = validate_welch_t_test(N_REPLICATES)
    results["tests"]["welch-t"] = res
    results["overall_passed"] = results["overall_passed"] and passed
    logger.info("Welch's t-test: %s (diff=%.4f)", "PASSED" if passed else "FAILED", res["absolute_difference"])

    # Run binomial test validation
    logger.info("Validating binomial test...")
    passed, res = validate_binomial_test(N_REPLICATES)
    results["tests"]["binomial"] = res
    results["overall_passed"] = results["overall_passed"] and passed
    logger.info("Binomial test: %s (diff=%.4f)", "PASSED" if passed else "FAILED", res["absolute_difference"])

    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info("Validation results written to %s", output_path)

    return results


def main():
    """Main entry point for Monte-Carlo validation script."""
    output_path = Path("output/monte_carlo_validation_results.json")
    
    try:
        results = run_monte_carlo_validation(output_path)
        
        if results["overall_passed"]:
            logger.info("All Monte-Carlo validation tests PASSED.")
            sys.exit(0)
        else:
            logger.error("One or more Monte-Carlo validation tests FAILED.")
            sys.exit(1)
            
    except Exception as e:
        audit_logger.log_error("ERR-801", f"Monte-Carlo validation failed with exception: {e}")
        logger.exception("Validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()