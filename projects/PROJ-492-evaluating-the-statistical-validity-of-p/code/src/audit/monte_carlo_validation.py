"""
Monte-Carlo Validation Module (FR-026).

Validates the statistical correctness of our reconstruction logic by comparing
empirical p-values from Monte-Carlo simulations against scipy's library functions.

Runs 100,000 replicates for:
- Two-proportion z-test
- Fisher's Exact Test
- Welch's t-test
- Binomial Test

Criteria: Absolute difference between empirical p-value and library p-value <= 0.005.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
from scipy import stats

# Import from project API surface
from code.src.config import set_rng_seed, get_config_summary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.audit.monte_carlo_core import (
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value
)

# Configuration constants
NUM_REPLICATES = 100000
TOLERANCE = 0.005
RANDOM_SEED = 42

def validate_z_test() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate two-proportion z-test consistency.
    Simulates null data and compares empirical p-value to scipy.stats.norm.sf.
    """
    set_rng_seed(RANDOM_SEED)
    logger = get_default_logger(__name__)
    logger.info("Running Monte-Carlo validation for Two-Proportion Z-Test...")

    # Parameters for simulation (fixed baseline and effect)
    n1, n2 = 1000, 1000
    p1, p2 = 0.5, 0.55  # 5% effect size
    
    # Run simulation
    z_stats = simulate_z_test_statistic(n1, n2, p1, p2, NUM_REPLICATES)
    
    # Compute empirical p-value (two-tailed)
    # The null hypothesis is p1 == p2. We simulate under null or close to it.
    # To be rigorous for validation, we simulate under the null (p1=p2)
    # and check if the distribution of Z matches standard normal.
    # However, the task asks to check the *calculation* logic.
    # Let's simulate a specific scenario where we know the expected p-value
    # from scipy for a given set of counts, and compare the Monte Carlo estimate.
    
    # Scenario: n1=1000, x1=500, n2=1000, x2=550
    x1, x2 = 500, 550
    
    # Scipy calculation (Two-proportion z-test)
    # Using statsmodels or manual calculation since scipy doesn't have direct 2-prop z-test in older versions
    # We use the manual formula which is standard:
    p_pool = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    z_obs = (x1/n1 - x2/n2) / se
    p_scipy = 2 * stats.norm.sf(abs(z_obs))
    
    # Monte Carlo: Generate data under the null (p = p_pool)
    # Count how many simulated z-stats are >= |z_obs|
    z_null = simulate_z_test_statistic(n1, n2, p_pool, p_pool, NUM_REPLICATES)
    p_empirical = compute_empirical_p_value(z_null, z_obs, two_tailed=True)
    
    diff = abs(p_scipy - p_empirical)
    passed = diff <= TOLERANCE
    
    result = {
        "test": "z_test",
        "passed": passed,
        "scipy_p": p_scipy,
        "empirical_p": p_empirical,
        "difference": diff,
        "tolerance": TOLERANCE
    }
    
    if passed:
        logger.info(f"Z-Test Validation PASSED. Diff: {diff:.6f}")
    else:
        logger.error(f"Z-Test Validation FAILED. Diff: {diff:.6f} > {TOLERANCE}")
        
    return passed, p_scipy, p_empirical, result

def validate_fisher_exact() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate Fisher's Exact Test consistency.
    """
    set_rng_seed(RANDOM_SEED + 1)
    logger = get_default_logger(__name__)
    logger.info("Running Monte-Carlo validation for Fisher's Exact Test...")

    # Contingency table
    # Group A: 50 successes, 950 failures
    # Group B: 80 successes, 920 failures
    a, b, c, d = 50, 950, 80, 920
    table = [[a, b], [c, d]]
    
    # Scipy calculation
    _, p_scipy = stats.fisher_exact(table, alternative='two-sided')
    
    # Monte Carlo Simulation:
    # Simulate contingency tables with fixed margins (n1=a+b, n2=c+d, k=a+c, N=a+b+c+d)
    # using hypergeometric distribution logic.
    # We generate 'a' from Hypergeometric(N, k, n1)
    N = a + b + c + d
    k = a + c
    n1 = a + b
    
    # Generate simulated 'a' values
    sim_a = stats.hypergeom.rvs(N, k, n1, size=NUM_REPLICATES)
    
    # Calculate p-value: proportion of tables with probability <= observed table probability
    # Probability of a specific table (a, b, c, d) is: C(k, a) * C(N-k, n1-a) / C(N, n1)
    # This is the Hypergeometric PMF.
    # We count how many simulated 'a' have PMF <= observed PMF.
    
    obs_prob = stats.hypergeom.pmf(a, N, k, n1)
    sim_probs = stats.hypergeom.pmf(sim_a, N, k, n1)
    
    # Two-sided: sum of probabilities <= observed probability
    # Note: Fisher's exact two-sided is often defined as sum(p <= p_obs)
    p_empirical = np.mean(sim_probs <= obs_prob)
    
    diff = abs(p_scipy - p_empirical)
    passed = diff <= TOLERANCE
    
    result = {
        "test": "fisher_exact",
        "passed": passed,
        "scipy_p": p_scipy,
        "empirical_p": p_empirical,
        "difference": diff,
        "tolerance": TOLERANCE
    }
    
    if passed:
        logger.info(f"Fisher's Exact Validation PASSED. Diff: {diff:.6f}")
    else:
        logger.error(f"Fisher's Exact Validation FAILED. Diff: {diff:.6f} > {TOLERANCE}")
        
    return passed, p_scipy, p_empirical, result

def validate_welch_t_test() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate Welch's t-test consistency.
    """
    set_rng_seed(RANDOM_SEED + 2)
    logger = get_default_logger(__name__)
    logger.info("Running Monte-Carlo validation for Welch's t-test...")

    # Parameters
    n1, n2 = 500, 500
    mu1, mu2 = 10.0, 10.5
    sigma1, sigma2 = 2.0, 2.5
    
    # Observed statistics
    # We simulate one large sample to get 'observed' t and p
    # Actually, we want to check if the Monte Carlo distribution of t matches
    # the theoretical t-distribution implied by the null.
    # Or, more simply: simulate under null, get empirical p for a specific observed t.
    
    # Let's define an observed difference that yields a specific p-value.
    # Generate one "observed" sample
    np.random.seed(RANDOM_SEED + 10)
    x1_obs = np.random.normal(mu1, sigma1, n1)
    x2_obs = np.random.normal(mu2, sigma2, n2)
    
    t_obs, p_scipy = stats.ttest_ind(x1_obs, x2_obs, equal_var=False)
    
    # Monte Carlo under Null (mu1 = mu2)
    # We simulate distributions with means equal to pooled mean or just 0 difference
    # To be precise, we simulate data with same variance but zero mean difference.
    # We use the observed variances for realism or standard null variances.
    # Standard approach: permute or generate from N(0, sigma).
    # Let's generate from N(0, sigma) using observed sigmas to match the scale.
    
    s1, s2 = np.std(x1_obs, ddof=1), np.std(x2_obs, ddof=1)
    # Simulate under null: mean1 = mean2 = 0
    t_null = simulate_welch_t_statistic(n1, n2, 0.0, 0.0, s1, s2, NUM_REPLICATES)
    
    p_empirical = compute_empirical_p_value(t_null, t_obs, two_tailed=True)
    
    diff = abs(p_scipy - p_empirical)
    passed = diff <= TOLERANCE
    
    result = {
        "test": "welch_t",
        "passed": passed,
        "scipy_p": p_scipy,
        "empirical_p": p_empirical,
        "difference": diff,
        "tolerance": TOLERANCE
    }
    
    if passed:
        logger.info(f"Welch's t-Test Validation PASSED. Diff: {diff:.6f}")
    else:
        logger.error(f"Welch's t-Test Validation FAILED. Diff: {diff:.6f} > {TOLERANCE}")
        
    return passed, p_scipy, p_empirical, result

def validate_binomial_test() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate Binomial Test consistency.
    """
    set_rng_seed(RANDOM_SEED + 3)
    logger = get_default_logger(__name__)
    logger.info("Running Monte-Carlo validation for Binomial Test...")

    # Parameters
    n = 100
    k = 60
    p_null = 0.5
    
    # Scipy calculation
    # stats.binom_test is deprecated, use binomtest
    res = stats.binomtest(k, n, p_null, alternative='two-sided')
    p_scipy = res.pvalue
    
    # Monte Carlo Simulation
    # Generate 'k' from Binomial(n, p_null)
    sim_k = np.random.binomial(n, p_null, size=NUM_REPLICATES)
    
    # Calculate p-value: proportion of simulated k with P(K=x) <= P(K=k_obs)
    # Or simply count how many are as extreme or more extreme?
    # Fisher's exact logic applies: sum of probabilities <= observed probability.
    # However, standard binomial test often uses tail probabilities.
    # Let's use the probability mass logic for strict consistency with "exact" definition.
    
    obs_prob = stats.binom.pmf(k, n, p_null)
    sim_probs = stats.binom.pmf(sim_k, n, p_null)
    p_empirical = np.mean(sim_probs <= obs_prob)
    
    diff = abs(p_scipy - p_empirical)
    passed = diff <= TOLERANCE
    
    result = {
        "test": "binomial",
        "passed": passed,
        "scipy_p": p_scipy,
        "empirical_p": p_empirical,
        "difference": diff,
        "tolerance": TOLERANCE
    }
    
    if passed:
        logger.info(f"Binomial Test Validation PASSED. Diff: {diff:.6f}")
    else:
        logger.error(f"Binomial Test Validation FAILED. Diff: {diff:.6f} > {TOLERANCE}")
        
    return passed, p_scipy, p_empirical, result

def run_monte_carlo_validation() -> bool:
    """
    Run all validations and return True if all pass.
    """
    logger = get_default_logger(__name__)
    logger.info(f"Starting Monte-Carlo Validation with {NUM_REPLICATES} replicates...")
    
    all_passed = True
    results = []
    
    # Run Z-Test
    p1, s1, e1, r1 = validate_z_test()
    results.append(r1)
    if not p1: all_passed = False
    
    # Run Fisher
    p2, s2, e2, r2 = validate_fisher_exact()
    results.append(r2)
    if not p2: all_passed = False
    
    # Run Welch
    p3, s3, e3, r3 = validate_welch_t_test()
    results.append(r3)
    if not p3: all_passed = False
    
    # Run Binomial
    p4, s4, e4, r4 = validate_binomial_test()
    results.append(r4)
    if not p4: all_passed = False
    
    # Log summary
    if all_passed:
        logger.info("All Monte-Carlo validations PASSED.")
    else:
        logger.error("One or more Monte-Carlo validations FAILED.")
        
    return all_passed

def main():
    """
    Entry point for the validation script.
    Exits with 0 if all pass, 1 otherwise.
    """
    try:
        success = run_monte_carlo_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger = get_default_logger(__name__)
        logger.critical(f"Validation failed with exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
