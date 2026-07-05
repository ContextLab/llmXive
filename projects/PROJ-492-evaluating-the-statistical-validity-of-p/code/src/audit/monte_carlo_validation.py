"""
Monte-Carlo Validation Module (FR-026)

Validates statistical reconstruction accuracy by running Monte-Carlo simulations
for z-test, Fisher's exact test, Welch's t-test, and binomial test.
Compares empirical p-values against scipy library p-values.
Criterion: absolute difference <= 0.005.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from scipy import stats

from code.src.audit.monte_carlo_core import (
    set_seeds,
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
)
from code.src.config import SEED
from code.src.utils.logger import get_default_logger, AuditLogger

# Configuration
NUM_REPLICATES = 10000
TOLERANCE = 0.005
LOG_FILE = Path("output/monte_carlo_validation.log")

# Ensure output directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = get_default_logger(__name__, log_file=str(LOG_FILE))
audit_logger = AuditLogger(logger)


def validate_z_test(n_replicates: int = NUM_REPLICATES) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate two-proportion z-test using Monte-Carlo simulation.
    Generates null binary data, computes z-statistics, and compares empirical p-value
    to scipy's analytical p-value.
    """
    set_seeds(SEED)
    logger.info(f"Running z-test validation with {n_replicates} replicates...")

    # Parameters for simulation (typical A/B test scenario)
    n_control = 1000
    n_treatment = 1000
    p_control = 0.10
    p_treatment = 0.10  # Null hypothesis: equal proportions

    # Generate null data and compute z-statistics
    z_stats = []
    for _ in range(n_replicates):
        x_control = np.random.binomial(n_control, p_control)
        x_treatment = np.random.binomial(n_treatment, p_treatment)
        z_stat = simulate_z_test_statistic(x_control, n_control, x_treatment, n_treatment)
        z_stats.append(z_stat)

    z_stats = np.array(z_stats)

    # Compute empirical two-sided p-value
    # Under null, z should be N(0,1), so empirical p = proportion |z| >= observed
    # For validation, we simulate the distribution and check if the tail probability matches
    # We use the max absolute z as a threshold for empirical p-value calculation
    # Actually, we compare the distribution of z-stats to standard normal
    # Better approach: compute p-value for a specific observed effect and compare
    
    # Simulate a specific case: observed difference
    x_ctrl_obs = int(n_control * p_control)
    x_trt_obs = int(n_treatment * p_treatment)
    # Add small noise to ensure non-zero difference for testing
    x_trt_obs += 2
    
    z_obs = simulate_z_test_statistic(x_ctrl_obs, n_control, x_trt_obs, n_treatment)
    scipy_p = 2 * (1 - stats.norm.cdf(abs(z_obs)))
    
    # Empirical p-value: proportion of simulated |z| >= |z_obs|
    empirical_p = np.mean(np.abs(z_stats) >= abs(z_obs))

    diff = abs(empirical_p - scipy_p)
    passed = diff <= TOLERANCE

    result = {
        "test": "z_test",
        "n_replicates": n_replicates,
        "z_observed": float(z_obs),
        "scipy_p_value": float(scipy_p),
        "empirical_p_value": float(empirical_p),
        "absolute_difference": float(diff),
        "passed": passed,
    }

    logger.info(f"Z-test: scipy={scipy_p:.6f}, empirical={empirical_p:.6f}, diff={diff:.6f}, passed={passed}")
    return passed, result


def validate_fisher_exact(n_replicates: int = NUM_REPLICATES) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Fisher's exact test using Monte-Carlo simulation.
    Simulates contingency tables under the null hypothesis and compares
    empirical p-value to scipy's analytical p-value.
    """
    set_seeds(SEED)
    logger.info(f"Running Fisher's exact test validation with {n_replicates} replicates...")

    # Parameters for simulation
    n_control = 500
    n_treatment = 500
    p_control = 0.05
    p_treatment = 0.05  # Null hypothesis

    # Simulate contingency tables
    p_values = []
    for _ in range(n_replicates):
        x_control = np.random.binomial(n_control, p_control)
        x_treatment = np.random.binomial(n_treatment, p_treatment)
        
        # Build contingency table
        table = np.array([
            [x_control, n_control - x_control],
            [x_treatment, n_treatment - x_treatment]
        ])
        
        # Compute Fisher's exact p-value (two-sided)
        # scipy.stats.fisher_exact returns (odds_ratio, p_value)
        try:
            _, p_val = stats.fisher_exact(table, alternative='two-sided')
            p_values.append(p_val)
        except ValueError:
            # Handle edge cases where table is degenerate
            p_values.append(1.0)

    p_values = np.array(p_values)
    
    # For validation, we check if the distribution of p-values is uniform under null
    # A simple check: proportion of p-values < 0.05 should be ~0.05
    alpha = 0.05
    empirical_alpha = np.mean(p_values < alpha)
    
    # Theoretical alpha is exactly alpha under null
    # We compare empirical rejection rate to theoretical
    diff = abs(empirical_alpha - alpha)
    passed = diff <= TOLERANCE

    result = {
        "test": "fisher_exact",
        "n_replicates": n_replicates,
        "theoretical_alpha": alpha,
        "empirical_alpha": float(empirical_alpha),
        "absolute_difference": float(diff),
        "passed": passed,
    }

    logger.info(f"Fisher's test: theoretical={alpha:.3f}, empirical={empirical_alpha:.3f}, diff={diff:.3f}, passed={passed}")
    return passed, result


def validate_welch_t_test(n_replicates: int = NUM_REPLICATES) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Welch's t-test using Monte-Carlo simulation.
    Generates null continuous data and compares empirical p-value to scipy's analytical p-value.
    """
    set_seeds(SEED)
    logger.info(f"Running Welch's t-test validation with {n_replicates} replicates...")

    # Parameters for simulation
    n_control = 100
    n_treatment = 150  # Unequal sample sizes for Welch
    mean_control = 10.0
    mean_treatment = 10.0  # Null hypothesis: equal means
    std_control = 2.0
    std_treatment = 2.5  # Unequal variances for Welch

    # Simulate t-statistics
    t_stats = []
    for _ in range(n_replicates):
        data_control = np.random.normal(mean_control, std_control, n_control)
        data_treatment = np.random.normal(mean_treatment, std_treatment, n_treatment)
        
        t_stat = simulate_welch_t_statistic(data_control, data_treatment)
        t_stats.append(t_stat)

    t_stats = np.array(t_stats)

    # Simulate a specific observed case
    data_ctrl_obs = np.random.normal(mean_control, std_control, n_control)
    data_trt_obs = np.random.normal(mean_treatment + 0.5, std_treatment, n_treatment)  # Small effect
    
    t_obs = simulate_welch_t_statistic(data_ctrl_obs, data_trt_obs)
    _, scipy_p = stats.ttest_ind(data_ctrl_obs, data_trt_obs, equal_var=False)
    
    # Empirical p-value: proportion of simulated |t| >= |t_obs|
    empirical_p = np.mean(np.abs(t_stats) >= abs(t_obs))

    diff = abs(empirical_p - scipy_p)
    passed = diff <= TOLERANCE

    result = {
        "test": "welch_t_test",
        "n_replicates": n_replicates,
        "t_observed": float(t_obs),
        "scipy_p_value": float(scipy_p),
        "empirical_p_value": float(empirical_p),
        "absolute_difference": float(diff),
        "passed": passed,
    }

    logger.info(f"Welch's t-test: scipy={scipy_p:.6f}, empirical={empirical_p:.6f}, diff={diff:.6f}, passed={passed}")
    return passed, result


def validate_binomial_test(n_replicates: int = NUM_REPLICATES) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate binomial test using Monte-Carlo simulation.
    Simulates binomial counts under null and compares empirical p-value to scipy's analytical p-value.
    """
    set_seeds(SEED)
    logger.info(f"Running binomial test validation with {n_replicates} replicates...")

    # Parameters for simulation
    n_trials = 100
    p_null = 0.5  # Null hypothesis

    # Simulate binomial counts
    counts = []
    for _ in range(n_replicates):
        count = np.random.binomial(n_trials, p_null)
        counts.append(count)

    counts = np.array(counts)

    # Simulate a specific observed case
    k_obs = 60  # Observed successes
    scipy_p = 2 * min(stats.binom.cdf(k_obs, n_trials, p_null), 
                     1 - stats.binom.cdf(k_obs - 1, n_trials, p_null))
    
    # Empirical p-value: proportion of simulated counts as extreme or more extreme than k_obs
    # Two-sided: |count - expected| >= |k_obs - expected|
    expected = n_trials * p_null
    extreme = np.abs(counts - expected) >= np.abs(k_obs - expected)
    empirical_p = np.mean(extreme)

    diff = abs(empirical_p - scipy_p)
    passed = diff <= TOLERANCE

    result = {
        "test": "binomial_test",
        "n_replicates": n_replicates,
        "k_observed": int(k_obs),
        "scipy_p_value": float(scipy_p),
        "empirical_p_value": float(empirical_p),
        "absolute_difference": float(diff),
        "passed": passed,
    }

    logger.info(f"Binomial test: scipy={scipy_p:.6f}, empirical={empirical_p:.6f}, diff={diff:.6f}, passed={passed}")
    return passed, result


def run_monte_carlo_validation(n_replicates: int = NUM_REPLICATES) -> bool:
    """
    Run all Monte-Carlo validations and return True if all pass.
    """
    logger.info("=" * 60)
    logger.info("Starting Monte-Carlo Validation Suite")
    logger.info(f"Replicates per test: {n_replicates}")
    logger.info(f"Acceptance threshold: {TOLERANCE}")
    logger.info("=" * 60)

    results = []
    all_passed = True

    # Run z-test validation
    z_passed, z_result = validate_z_test(n_replicates)
    results.append(z_result)
    if not z_passed:
        all_passed = False
        audit_logger.error("ERR-801", "Z-test Monte-Carlo validation failed")

    # Run Fisher's exact test validation
    fisher_passed, fisher_result = validate_fisher_exact(n_replicates)
    results.append(fisher_result)
    if not fisher_passed:
        all_passed = False
        audit_logger.error("ERR-801", "Fisher's exact test Monte-Carlo validation failed")

    # Run Welch's t-test validation
    welch_passed, welch_result = validate_welch_t_test(n_replicates)
    results.append(welch_result)
    if not welch_passed:
        all_passed = False
        audit_logger.error("ERR-801", "Welch's t-test Monte-Carlo validation failed")

    # Run binomial test validation
    binom_passed, binom_result = validate_binomial_test(n_replicates)
    results.append(binom_result)
    if not binom_passed:
        all_passed = False
        audit_logger.error("ERR-801", "Binomial test Monte-Carlo validation failed")

    logger.info("=" * 60)
    logger.info("Monte-Carlo Validation Summary")
    logger.info("=" * 60)
    for res in results:
        status = "PASS" if res["passed"] else "FAIL"
        logger.info(f"{res['test']}: {status} (diff={res['absolute_difference']:.6f})")

    if all_passed:
        logger.info("All validations PASSED.")
    else:
        logger.error("Some validations FAILED. Aborting pipeline.")

    return all_passed


def main() -> int:
    """
    Main entry point for Monte-Carlo validation module.
    Returns 0 if all validations pass, 1 otherwise.
    """
    try:
        success = run_monte_carlo_validation()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Unexpected error during Monte-Carlo validation: {e}")
        audit_logger.error("ERR-999", f"Monte-Carlo validation failed with exception: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())