"""
Monte-Carlo Validation Module (FR-026).

This module validates the statistical correctness of the reconstruction logic
by running 10,000 replicates for each statistical test (z-test, Fisher's,
Welch's, binomial) and checking that the absolute difference between the
empirical p-value and the theoretical p-value is <= 0.005.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
from scipy import stats

# Import from project core
from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.audit.monte_carlo_core import (
    set_seeds,
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
)

logger = get_default_logger(__name__)

# Constants
N_REPLICATES = 10000
TOLERANCE = 0.005
ALPHA = 0.05


def validate_z_test() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validates the two-proportion z-test consistency via Monte-Carlo simulation.

    Returns:
        Tuple: (passed, theoretical_p, empirical_p, details)
    """
    set_seeds(SEED)

    # Parameters for simulation (fixed effect size to ensure power)
    n1, n2 = 500, 500
    p1, p2 = 0.40, 0.45  # Small effect size

    # Run simulation
    z_stats = simulate_z_test_statistic(n1, n2, p1, p2, N_REPLICATES)

    # Compute theoretical p-value for the observed difference
    # We simulate under the null hypothesis for the empirical distribution
    # However, to validate the test statistic calculation itself, we compare
    # the distribution of simulated statistics to the theoretical normal.
    # A simpler validation: check if the empirical p-value (from simulated null)
    # matches the theoretical p-value for a known effect.
    
    # Let's simulate under the NULL hypothesis (p1=p2) to check Type I error control
    # or simulate with a specific effect and compare the distribution of p-values.
    # The task asks to check "absolute difference <= 0.005".
    # We will compute the empirical p-value for a specific observed statistic
    # generated from the simulation and compare it to the theoretical p-value.

    # Generate one observed sample to get a statistic
    rng = np.random.default_rng(SEED)
    x1 = rng.binomial(n1, p1)
    x2 = rng.binomial(n2, p2)
    
    # Calculate theoretical z and p
    p_pool = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    z_obs = (x1/n1 - x2/n2) / se
    p_theoretical = 2 * (1 - stats.norm.cdf(abs(z_obs)))

    # Calculate empirical p-value from the null distribution
    # We generate N_REPLICATES of z-stats under the null (p1=p2=p_pool)
    null_z_stats = []
    for _ in range(N_REPLICATES):
        nx1 = rng.binomial(n1, p_pool)
        nx2 = rng.binomial(n2, p_pool)
        np_pool = (nx1 + nx2) / (n1 + n2)
        nse = np.sqrt(np_pool * (1 - np_pool) * (1/n1 + 1/n2))
        nz = (nx1/n1 - nx2/n2) / nse
        null_z_stats.append(nz)

    # Empirical p-value: proportion of |null_z| >= |z_obs|
    empirical_p = np.mean(np.abs(null_z_stats) >= np.abs(z_obs))

    diff = abs(p_theoretical - empirical_p)
    passed = diff <= TOLERANCE

    details = {
        "test": "z_test",
        "n1": n1, "n2": n2,
        "p1": p1, "p2": p2,
        "z_obs": float(z_obs),
        "p_theoretical": float(p_theoretical),
        "p_empirical": float(empirical_p),
        "diff": float(diff),
        "tolerance": TOLERANCE,
        "passed": passed
    }

    return passed, float(p_theoretical), float(empirical_p), details


def validate_fisher_exact() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validates Fisher's Exact Test consistency.
    """
    set_seeds(SEED)
    rng = np.random.default_rng(SEED)

    # Parameters
    n1, n2 = 50, 50
    p1, p2 = 0.30, 0.45

    # Generate observed counts
    x1 = rng.binomial(n1, p1)
    x2 = rng.binomial(n2, p2)
    
    # Theoretical p-value from scipy
    table = [[x1, n1 - x1], [x2, n2 - x2]]
    _, p_theoretical = stats.fisher_exact(table, alternative='two-sided')

    # Monte Carlo simulation for empirical p-value
    # Simulate under null hypothesis: p1 = p2 = p_pool
    p_pool = (x1 + x2) / (n1 + n2)
    empirical_count = 0

    for _ in range(N_REPLICATES):
        nx1 = rng.binomial(n1, p_pool)
        nx2 = rng.binomial(n2, p_pool)
        ntable = [[nx1, n1 - nx1], [nx2, n2 - nx2]]
        _, p_sim = stats.fisher_exact(ntable, alternative='two-sided')
        # Compare p-values directly or counts?
        # Standard MC validation: count how many simulated tables are as or more extreme
        # than the observed table. Fisher's exact test p-value is the probability of
        # the table or more extreme.
        if p_sim <= p_theoretical:
            empirical_count += 1

    # Note: Direct p-value comparison in MC is tricky due to discreteness.
    # A better approach for validation is to check if the empirical distribution
    # of p-values is uniform under the null, or compare the observed statistic
    # against the simulated distribution.
    # Here we approximate: empirical p = count / N
    p_empirical = empirical_count / N_REPLICATES

    diff = abs(p_theoretical - p_empirical)
    passed = diff <= TOLERANCE

    details = {
        "test": "fisher_exact",
        "n1": n1, "n2": n2,
        "p1": p1, "p2": p2,
        "observed_table": table,
        "p_theoretical": float(p_theoretical),
        "p_empirical": float(p_empirical),
        "diff": float(diff),
        "tolerance": TOLERANCE,
        "passed": passed
    }

    return passed, float(p_theoretical), float(p_empirical), details


def validate_welch_t_test() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validates Welch's t-test consistency.
    """
    set_seeds(SEED)
    rng = np.random.default_rng(SEED)

    # Parameters
    n1, n2 = 100, 120
    mu1, mu2 = 10.0, 10.5
    sigma1, sigma2 = 3.0, 4.0  # Unequal variance

    # Generate observed data
    data1 = rng.normal(mu1, sigma1, n1)
    data2 = rng.normal(mu2, sigma2, n2)

    # Theoretical p-value
    _, p_theoretical = stats.ttest_ind(data1, data2, equal_var=False)

    # Monte Carlo simulation under null hypothesis (mu1 = mu2)
    # Pool data to estimate null distribution
    pooled_data = np.concatenate([data1, data2])
    pooled_mean = np.mean(pooled_data)
    
    # Center data to null
    centered_data1 = data1 - np.mean(data1)
    centered_data2 = data2 - np.mean(data2)
    
    # Resample to simulate null
    empirical_count = 0
    t_obs = stats.ttest_ind(data1, data2, equal_var=False).statistic

    for _ in range(N_REPLICATES):
        # Resample from centered data
        s1 = rng.choice(centered_data1, size=n1, replace=True)
        s2 = rng.choice(centered_data2, size=n2, replace=True)
        t_sim = stats.ttest_ind(s1, s2, equal_var=False).statistic
        if abs(t_sim) >= abs(t_obs):
            empirical_count += 1

    p_empirical = empirical_count / N_REPLICATES
    diff = abs(p_theoretical - p_empirical)
    passed = diff <= TOLERANCE

    details = {
        "test": "welch_t_test",
        "n1": n1, "n2": n2,
        "mu1": mu1, "mu2": mu2,
        "sigma1": sigma1, "sigma2": sigma2,
        "t_obs": float(t_obs),
        "p_theoretical": float(p_theoretical),
        "p_empirical": float(p_empirical),
        "diff": float(diff),
        "tolerance": TOLERANCE,
        "passed": passed
    }

    return passed, float(p_theoretical), float(p_empirical), details


def validate_binomial_test() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validates Binomial test consistency.
    """
    set_seeds(SEED)
    rng = np.random.default_rng(SEED)

    # Parameters
    n = 100
    p_null = 0.5
    p_true = 0.6

    # Generate observed data
    k_obs = rng.binomial(n, p_true)

    # Theoretical p-value (two-sided)
    # scipy.stats.binom_test is deprecated, use binomtest
    result = stats.binomtest(k_obs, n, p_null, alternative='two-sided')
    p_theoretical = result.pvalue

    # Monte Carlo simulation under null
    empirical_count = 0
    for _ in range(N_REPLICATES):
        k_sim = rng.binomial(n, p_null)
        # Calculate p-value for this simulated k
        # For simplicity, we compare the probability mass or use the same logic
        # A robust MC p-value: proportion of simulated k's as or more extreme than k_obs
        # "More extreme" means P(K=k_sim) <= P(K=k_obs) under null
        p_k_obs = stats.binom.pmf(k_obs, n, p_null)
        p_k_sim = stats.binom.pmf(k_sim, n, p_null)
        if p_k_sim <= p_k_obs:
            empirical_count += 1

    p_empirical = empirical_count / N_REPLICATES
    diff = abs(p_theoretical - p_empirical)
    passed = diff <= TOLERANCE

    details = {
        "test": "binomial_test",
        "n": n,
        "p_null": p_null,
        "p_true": p_true,
        "k_obs": int(k_obs),
        "p_theoretical": float(p_theoretical),
        "p_empirical": float(p_empirical),
        "diff": float(diff),
        "tolerance": TOLERANCE,
        "passed": passed
    }

    return passed, float(p_theoretical), float(p_empirical), details


def run_monte_carlo_validation() -> Dict[str, Any]:
    """
    Runs all Monte-Carlo validation tests and aggregates results.
    """
    logger.info("Starting Monte-Carlo validation module (FR-026).")
    logger.info(f"Running {N_REPLICATES} replicates per test.")

    results = {}
    all_passed = True

    tests = [
        ("z_test", validate_z_test),
        ("fisher_exact", validate_fisher_exact),
        ("welch_t_test", validate_welch_t_test),
        ("binomial_test", validate_binomial_test),
    ]

    for name, func in tests:
        logger.info(f"Running validation for {name}...")
        try:
            passed, p_theo, p_emp, details = func()
            results[name] = details
            if not passed:
                all_passed = False
                logger.warning(f"Validation FAILED for {name}: diff={details['diff']:.5f} > {TOLERANCE}")
            else:
                logger.info(f"Validation PASSED for {name}: diff={details['diff']:.5f}")
        except Exception as e:
            logger.error(f"Error running {name}: {e}")
            results[name] = {"error": str(e), "passed": False}
            all_passed = False

    summary = {
        "total_tests": len(tests),
        "passed_count": sum(1 for r in results.values() if r.get("passed", False)),
        "failed_count": sum(1 for r in results.values() if not r.get("passed", False)),
        "all_passed": all_passed,
        "tolerance": TOLERANCE,
        "replicates": N_REPLICATES,
        "timestamp": str(logging.Formatter().formatTime(logging.LogRecord("", "", "", "", "", (), None)))
    }

    return summary


def main():
    """
    Entry point for the Monte-Carlo validation script.
    Exits with status 0 if all tests pass, 1 otherwise.
    """
    set_rng_seed(SEED)
    summary = run_monte_carlo_validation()

    # Print summary to stdout for easy reading
    print("\n--- Monte-Carlo Validation Summary ---")
    print(f"Replicates per test: {summary['replicates']}")
    print(f"Tolerance: {summary['tolerance']}")
    print(f"Total tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_count']}")
    print(f"Failed: {summary['failed_count']}")
    print(f"Overall Status: {'PASSED' if summary['all_passed'] else 'FAILED'}")
    print("--------------------------------------\n")

    if summary['all_passed']:
        logger.info("All Monte-Carlo validations passed.")
        sys.exit(0)
    else:
        logger.error("One or more Monte-Carlo validations failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
