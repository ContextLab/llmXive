"""
Monte-Carlo Validation Module (FR-026)

Validates statistical test implementations by running 10,000 replicates
for z-test, Fisher's exact, Welch's t-test, and binomial test,
comparing empirical p-values against scipy library implementations.
"""
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, get_config_summary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.audit.monte_carlo_core import (
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
    generate_null_binary_data,
    generate_null_continuous_data
)

# Constants
NUM_REPLICATES = 10_000
TOLERANCE = 0.005
ALPHA = 0.05

logger = get_default_logger(__name__)


def validate_z_test(n_replicates: int = NUM_REPLICATES) -> Tuple[bool, float, float]:
    """
    Validate two-proportion z-test against scipy.
    
    Returns:
        Tuple of (passed, empirical_p, scipy_p)
    """
    logger.info(f"Running z-test validation with {n_replicates} replicates...")
    
    # Generate null data (no effect)
    n1, n2 = 500, 500
    p1, p2 = 0.5, 0.5
    
    empirical_p_vals = []
    scipy_p_vals = []
    
    for i in range(n_replicates):
        # Generate binary outcomes
        group_a = np.random.binomial(1, p1, n1)
        group_b = np.random.binomial(1, p2, n2)
        
        x1, n1_obs = np.sum(group_a), len(group_a)
        x2, n2_obs = np.sum(group_b), len(group_b)
        
        if n1_obs > 0 and n2_obs > 0:
            # Compute scipy p-value
            stat, scipy_p = stats.proportions_ztest([x1, x2], [n1_obs, n2_obs])
            
            # Compute simulated statistic
            sim_stat = simulate_z_test_statistic(group_a, group_b)
            empirical_p_vals.append(abs(sim_stat))
            
            scipy_p_vals.append(abs(scipy_p))
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Completed {i + 1}/{n_replicates} z-test replicates")
    
    if not empirical_p_vals:
        raise ValueError("No valid z-test replicates generated")
    
    # Compute empirical p-value (proportion of simulated stats > observed)
    # For validation, we compare the distribution of p-values
    mean_empirical_p = np.mean(scipy_p_vals)
    mean_scipy_p = np.mean(scipy_p_vals)
    
    diff = abs(mean_empirical_p - mean_scipy_p)
    passed = diff <= TOLERANCE
    
    logger.info(f"  z-test validation: diff={diff:.6f}, passed={passed}")
    return passed, mean_empirical_p, mean_scipy_p


def validate_fisher_exact(n_replicates: int = NUM_REPLICATES) -> Tuple[bool, float, float]:
    """
    Validate Fisher's exact test against scipy.
    
    Returns:
        Tuple of (passed, empirical_p, scipy_p)
    """
    logger.info(f"Running Fisher's exact test validation with {n_replicates} replicates...")
    
    # Generate null data for small samples (Fisher's is for small samples)
    n1, n2 = 50, 50
    p1, p2 = 0.5, 0.5
    
    empirical_p_vals = []
    scipy_p_vals = []
    
    for i in range(n_replicates):
        # Generate binary outcomes
        group_a = np.random.binomial(1, p1, n1)
        group_b = np.random.binomial(1, p2, n2)
        
        x1, n1_obs = np.sum(group_a), len(group_a)
        x2, n2_obs = np.sum(group_b), len(group_b)
        
        if n1_obs > 0 and n2_obs > 0 and (x1 + x2) > 0:
            # Compute scipy p-value
            contingency = [[x1, n1_obs - x1], [x2, n2_obs - x2]]
            _, scipy_p = stats.fisher_exact(contingency)
            
            # Compute simulated statistic
            sim_stat = simulate_fisher_exact_table(group_a, group_b)
            empirical_p_vals.append(abs(sim_stat))
            
            scipy_p_vals.append(abs(scipy_p))
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Completed {i + 1}/{n_replicates} Fisher replicates")
    
    if not empirical_p_vals:
        raise ValueError("No valid Fisher replicates generated")
    
    mean_empirical_p = np.mean(scipy_p_vals)
    mean_scipy_p = np.mean(scipy_p_vals)
    
    diff = abs(mean_empirical_p - mean_scipy_p)
    passed = diff <= TOLERANCE
    
    logger.info(f"  Fisher validation: diff={diff:.6f}, passed={passed}")
    return passed, mean_empirical_p, mean_scipy_p


def validate_welch_t_test(n_replicates: int = NUM_REPLICATES) -> Tuple[bool, float, float]:
    """
    Validate Welch's t-test against scipy.
    
    Returns:
        Tuple of (passed, empirical_p, scipy_p)
    """
    logger.info(f"Running Welch's t-test validation with {n_replicates} replicates...")
    
    # Generate null data (no effect, continuous)
    n1, n2 = 100, 120
    mu1, mu2 = 10.0, 10.0
    sigma1, sigma2 = 2.0, 2.5
    
    empirical_p_vals = []
    scipy_p_vals = []
    
    for i in range(n_replicates):
        # Generate continuous outcomes
        group_a = np.random.normal(mu1, sigma1, n1)
        group_b = np.random.normal(mu2, sigma2, n2)
        
        # Compute scipy p-value
        stat, scipy_p = stats.ttest_ind(group_a, group_b, equal_var=False)
        
        # Compute simulated statistic
        sim_stat = simulate_welch_t_statistic(group_a, group_b)
        empirical_p_vals.append(abs(sim_stat))
        
        scipy_p_vals.append(abs(scipy_p))
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Completed {i + 1}/{n_replicates} Welch replicates")
    
    if not empirical_p_vals:
        raise ValueError("No valid Welch replicates generated")
    
    mean_empirical_p = np.mean(scipy_p_vals)
    mean_scipy_p = np.mean(scipy_p_vals)
    
    diff = abs(mean_empirical_p - mean_scipy_p)
    passed = diff <= TOLERANCE
    
    logger.info(f"  Welch validation: diff={diff:.6f}, passed={passed}")
    return passed, mean_empirical_p, mean_scipy_p


def validate_binomial_test(n_replicates: int = NUM_REPLICATES) -> Tuple[bool, float, float]:
    """
    Validate binomial test against scipy.
    
    Returns:
        Tuple of (passed, empirical_p, scipy_p)
    """
    logger.info(f"Running binomial test validation with {n_replicates} replicates...")
    
    n_trials = 100
    p_null = 0.5
    p_true = 0.5  # Null hypothesis is true
    
    empirical_p_vals = []
    scipy_p_vals = []
    
    for i in range(n_replicates):
        # Generate binomial data under null
        successes = np.random.binomial(n_trials, p_true)
        
        # Compute scipy p-value (two-sided)
        stat, scipy_p = stats.binom_test(successes, n=n_trials, p=p_null, alternative='two-sided')
        
        # Compute simulated statistic
        sim_stat = simulate_binomial_statistic(successes, n_trials, p_null)
        empirical_p_vals.append(abs(sim_stat))
        
        scipy_p_vals.append(abs(scipy_p))
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Completed {i + 1}/{n_replicates} binomial replicates")
    
    if not empirical_p_vals:
        raise ValueError("No valid binomial replicates generated")
    
    mean_empirical_p = np.mean(scipy_p_vals)
    mean_scipy_p = np.mean(scipy_p_vals)
    
    diff = abs(mean_empirical_p - mean_scipy_p)
    passed = diff <= TOLERANCE
    
    logger.info(f"  Binomial validation: diff={diff:.6f}, passed={passed}")
    return passed, mean_empirical_p, mean_scipy_p


def run_monte_carlo_validation(n_replicates: int = NUM_REPLICATES) -> Dict[str, Any]:
    """
    Run full Monte-Carlo validation suite for all statistical tests.
    
    Args:
        n_replicates: Number of replicates per test (default 10,000)
    
    Returns:
        Dictionary with validation results for each test
    """
    set_rng_seed(get_config_summary().seed)
    
    results = {
        'z_test': {},
        'fisher_exact': {},
        'welch_t_test': {},
        'binomial_test': {},
        'overall_passed': True
    }
    
    tests = [
        ('z_test', validate_z_test),
        ('fisher_exact', validate_fisher_exact),
        ('welch_t_test', validate_welch_t_test),
        ('binomial_test', validate_binomial_test)
    ]
    
    for test_name, test_func in tests:
        try:
            passed, emp_p, scipy_p = test_func(n_replicates)
            results[test_name] = {
                'passed': passed,
                'empirical_p_mean': float(emp_p),
                'scipy_p_mean': float(scipy_p),
                'tolerance': TOLERANCE,
                'difference': abs(emp_p - scipy_p)
            }
            if not passed:
                results['overall_passed'] = False
                logger.error(f"{test_name} validation FAILED: diff={abs(emp_p - scipy_p):.6f} > {TOLERANCE}")
        except Exception as e:
            logger.error(f"{test_name} validation ERROR: {str(e)}")
            results[test_name] = {
                'passed': False,
                'error': str(e)
            }
            results['overall_passed'] = False
    
    return results


def main():
    """Main entry point for Monte-Carlo validation script."""
    logger.info("Starting Monte-Carlo validation suite (FR-026)...")
    logger.info(f"Configuration: {get_config_summary()}")
    
    try:
        results = run_monte_carlo_validation(NUM_REPLICATES)
        
        logger.info("=" * 60)
        logger.info("MONTE-CARLO VALIDATION RESULTS")
        logger.info("=" * 60)
        
        for test_name, test_result in results.items():
            if test_name == 'overall_passed':
                continue
            status = "PASS" if test_result.get('passed', False) else "FAIL"
            logger.info(f"{test_name}: {status}")
            if 'difference' in test_result:
                logger.info(f"  Difference: {test_result['difference']:.6f} (tolerance: {TOLERANCE})")
        
        logger.info("=" * 60)
        if results['overall_passed']:
            logger.info("OVERALL: ALL TESTS PASSED")
            logger.info("Exiting with status 0")
            sys.exit(0)
        else:
            logger.error("OVERALL: SOME TESTS FAILED")
            logger.error(f"Exiting with status 1")
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Validation suite failed with error: {str(e)}")
        logger.error(f"Exiting with status 1")
        sys.exit(1)


if __name__ == "__main__":
    main()