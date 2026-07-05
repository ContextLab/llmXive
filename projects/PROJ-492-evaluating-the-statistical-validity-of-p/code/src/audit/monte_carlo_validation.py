"""
Monte-Carlo validation module for statistical tests.

Implements FR-026: Runs 10,000 replicates for z-test, Fisher's exact, Welch's t-test,
and binomial test to verify that empirical p-values match library calculations
within a tolerance of 0.005.
"""
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from scipy import stats

# Import from local project structure
from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.audit.monte_carlo_core import (
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
    set_seeds
)

# Constants
NUM_REPLICATES = 10000
TOLERANCE = 0.005
ALPHA = 0.05

def _setup_logging():
    """Configure logging for the validation module."""
    logger = get_default_logger()
    logger.setLevel(logging.INFO)
    return logger

def validate_z_test(logger: AuditLogger) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate two-proportion z-test using Monte-Carlo simulation.
    
    Returns:
        Tuple of (passed, empirical_p, library_p, details)
    """
    logger.info("Starting Monte-Carlo validation for z-test...")
    
    # Set seeds for reproducibility
    set_seeds(SEED)
    
    # Parameters for the simulation (standard effect size)
    n1, n2 = 1000, 1000
    p1, p2 = 0.50, 0.55  # 5% effect size
    
    # Run simulation
    z_stats = []
    for _ in range(NUM_REPLICATES):
        z_stat = simulate_z_test_statistic(n1, n2, p1, p2)
        z_stats.append(z_stat)
    
    # Compute empirical p-value (two-tailed)
    empirical_p = compute_empirical_p_value(z_stats, z_stats[0]) # Using first as observed for simplicity in null check, 
    # Actually, we need to compare the distribution of null stats to a specific observed.
    # Standard approach: Generate null distribution, then see where a specific observed stat falls.
    # Or: Generate data under H0, compute stat, check distribution matches theoretical.
    
    # Correct approach for validation:
    # 1. Generate data under H0 (p1 = p2).
    # 2. Compute z-stat for each replicate.
    # 3. The distribution of these stats should be N(0,1).
    # 4. Compare the empirical p-value of a specific observed stat against the theoretical.
    
    # Let's fix the logic:
    # We simulate the null distribution. Then we pick a "true" p1, p2 (maybe slightly different) 
    # or just check the null distribution properties.
    # The requirement is "checks the absolute difference <= 0.005".
    # We will simulate under H0 (p1=p2=0.5), compute z-stats.
    # Then we calculate the proportion of stats > |z_obs| for a fixed z_obs derived from a specific sample.
    
    # Simpler validation strategy:
    # Generate 10,000 samples under H0. Compute z-stat for each.
    # Calculate the empirical p-value for a fixed observed z-stat (e.g., 1.96).
    # Compare with scipy.stats.norm.sf(1.96)*2.
    
    z_obs = 1.96  # Fixed observed statistic
    
    # Regenerate under H0 to get null distribution
    set_seeds(SEED)
    null_z_stats = []
    for _ in range(NUM_REPLICATES):
        # Generate under H0: p1 = p2
        stat = simulate_z_test_statistic(n1, n2, 0.5, 0.5)
        null_z_stats.append(stat)
    
    # Empirical p-value: proportion of null stats with |stat| >= |z_obs|
    empirical_p = (sum(1 for s in null_z_stats if abs(s) >= abs(z_obs))) / NUM_REPLICATES
    
    # Theoretical p-value
    library_p = 2 * stats.norm.sf(abs(z_obs))
    
    diff = abs(empirical_p - library_p)
    passed = diff <= TOLERANCE
    
    details = {
        "test": "z-test",
        "z_observed": z_obs,
        "empirical_p": empirical_p,
        "library_p": library_p,
        "difference": diff,
        "tolerance": TOLERANCE,
        "replicates": NUM_REPLICATES
    }
    
    logger.info(f"z-test: empirical={empirical_p:.4f}, library={library_p:.4f}, diff={diff:.4f}, passed={passed}")
    return passed, empirical_p, library_p, details

def validate_fisher_exact(logger: AuditLogger) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate Fisher's exact test using Monte-Carlo simulation.
    
    Returns:
        Tuple of (passed, empirical_p, library_p, details)
    """
    logger.info("Starting Monte-Carlo validation for Fisher's exact test...")
    
    set_seeds(SEED)
    
    # Contingency table: [[a, b], [c, d]]
    # Under H0, odds ratio = 1.
    # We simulate tables with fixed margins and compute p-values.
    # Or simpler: Simulate data under H0, compute Fisher p-value, check distribution.
    
    # Strategy:
    # 1. Generate data under H0 (independence).
    # 2. Compute Fisher's p-value for that table.
    # 3. The p-value should be uniformly distributed under H0.
    # 4. Check if the mean p-value is ~0.5 and variance ~1/12?
    # 5. Better: Compare empirical p-value of a specific table against scipy.
    
    # Let's use a specific table and simulate the permutation distribution.
    # Table: [[10, 20], [15, 25]] (margins: 30, 40, 25, 35)
    a, b, c, d = 10, 20, 15, 25
    table = [[a, b], [c, d]]
    
    # Compute library p-value
    library_result = stats.fisher_exact(table, alternative='two-sided')
    library_p = library_result.pvalue
    
    # Simulate permutation distribution
    # Total successes = a+c, Total failures = b+d, Total n = a+b+c+d
    # We fix row and column margins? No, Fisher's conditions on margins.
    # We simulate hypergeometric distribution for cell 'a'.
    
    set_seeds(SEED)
    null_p_values = []
    
    # We simulate the distribution of the test statistic (odds ratio or cell count)
    # under the null hypothesis of independence, conditional on margins.
    # The test statistic is the count in cell (0,0).
    # Margins: row0 = a+b, row1 = c+d, col0 = a+c, col1 = b+d
    row0_sum = a + b
    row1_sum = c + d
    col0_sum = a + c
    n = a + b + c + d
    
    observed_stat = a
    
    # Simulate hypergeometric draws
    # X ~ Hypergeometric(N=n, K=col0_sum, n=row0_sum)
    # This is the exact distribution of cell (0,0) under H0.
    # We can just sample from scipy.stats.hypergeom
    
    # To get empirical p-value:
    # P(|X - E[X]| >= |observed - E[X]|)
    # Or simply: proportion of simulated X's with p-value <= library_p?
    # No, we want to verify the p-value calculation.
    # If we simulate the exact null distribution, the empirical p-value
    # calculated from the simulation should match the library p-value.
    
    # Simulate many tables with fixed margins
    simulated_a_values = []
    for _ in range(NUM_REPLICATES):
        # Sample from Hypergeometric
        val = stats.hypergeom.rvs(n, col0_sum, row0_sum)
        simulated_a_values.append(val)
    
    # Calculate p-value for each simulated table relative to the observed?
    # No, the p-value is a property of the observed table.
    # The "Monte Carlo validation" usually means:
    # "Does the library's p-value match the proportion of tables as extreme as observed?"
    # So we count how many simulated tables have a probability <= probability of observed table?
    # Or simply count how many have a statistic as extreme.
    
    # Let's count how many simulated 'a' values are as extreme or more extreme than observed 'a'.
    # Two-sided: |a - mean| >= |observed - mean|
    mean_a = (row0_sum * col0_sum) / n
    extreme_count = sum(1 for val in simulated_a_values if abs(val - mean_a) >= abs(observed_stat - mean_a))
    empirical_p = extreme_count / NUM_REPLICATES
    
    diff = abs(empirical_p - library_p)
    passed = diff <= TOLERANCE
    
    details = {
        "test": "fisher_exact",
        "table": table,
        "empirical_p": empirical_p,
        "library_p": library_p,
        "difference": diff,
        "tolerance": TOLERANCE,
        "replicates": NUM_REPLICATES
    }
    
    logger.info(f"Fisher's: empirical={empirical_p:.4f}, library={library_p:.4f}, diff={diff:.4f}, passed={passed}")
    return passed, empirical_p, library_p, details

def validate_welch_t_test(logger: AuditLogger) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate Welch's t-test using Monte-Carlo simulation.
    
    Returns:
        Tuple of (passed, empirical_p, library_p, details)
    """
    logger.info("Starting Monte-Carlo validation for Welch's t-test...")
    
    set_seeds(SEED)
    
    # Parameters
    n1, n2 = 50, 60
    mu1, mu2 = 10.0, 10.0  # H0: mu1 = mu2
    sigma1, sigma2 = 2.0, 2.5  # Unequal variances (Welch's handles this)
    
    # We want to check if the p-value distribution is uniform under H0.
    # Or compare empirical p-value of a specific observed t-stat.
    
    # Strategy: Simulate under H0, compute t-stats.
    # Pick a fixed t_obs (e.g., 1.96).
    # Compute empirical p-value: proportion of |t| >= |t_obs|.
    # Compare with theoretical t-distribution p-value.
    
    t_obs = 1.96
    
    null_t_stats = []
    for _ in range(NUM_REPLICATES):
        t_stat = simulate_welch_t_statistic(n1, n2, mu1, mu2, sigma1, sigma2)
        null_t_stats.append(t_stat)
    
    # Empirical p-value
    empirical_p = (sum(1 for s in null_t_stats if abs(s) >= abs(t_obs))) / NUM_REPLICATES
    
    # Theoretical: Welch's degrees of freedom
    # For H0, we can approximate with standard t-distribution or calculate df for the specific sample sizes
    # Since mu1=mu2, the distribution of t is t-distribution with df approximated by Welch-Satterthwaite.
    # But for H0, the expected t is 0.
    # We use the theoretical distribution of Welch's t under H0.
    # Approximate df:
    s1_sq = sigma1**2
    s2_sq = sigma2**2
    df = (s1_sq/n1 + s2_sq/n2)**2 / ( (s1_sq/n1)**2/(n1-1) + (s2_sq/n2)**2/(n2-1) )
    
    library_p = 2 * stats.t.sf(abs(t_obs), df)
    
    diff = abs(empirical_p - library_p)
    passed = diff <= TOLERANCE
    
    details = {
        "test": "welch_t",
        "t_observed": t_obs,
        "df": df,
        "empirical_p": empirical_p,
        "library_p": library_p,
        "difference": diff,
        "tolerance": TOLERANCE,
        "replicates": NUM_REPLICATES
    }
    
    logger.info(f"Welch's t: empirical={empirical_p:.4f}, library={library_p:.4f}, diff={diff:.4f}, passed={passed}")
    return passed, empirical_p, library_p, details

def validate_binomial_test(logger: AuditLogger) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate binomial test using Monte-Carlo simulation.
    
    Returns:
        Tuple of (passed, empirical_p, library_p, details)
    """
    logger.info("Starting Monte-Carlo validation for binomial test...")
    
    set_seeds(SEED)
    
    # Parameters
    n = 100
    p_null = 0.5
    k_obs = 60  # Observed successes
    
    # Library p-value (two-sided)
    # scipy.stats.binom_test is deprecated, use binomtest
    library_result = stats.binomtest(k_obs, n, p_null, alternative='two-sided')
    library_p = library_result.pvalue
    
    # Simulate under H0
    null_k_values = []
    for _ in range(NUM_REPLICATES):
        k = simulate_binomial_statistic(n, p_null)
        null_k_values.append(k)
    
    # Empirical p-value: proportion of |k - n*p| >= |k_obs - n*p|
    expected_k = n * p_null
    extreme_count = sum(1 for k in null_k_values if abs(k - expected_k) >= abs(k_obs - expected_k))
    empirical_p = extreme_count / NUM_REPLICATES
    
    diff = abs(empirical_p - library_p)
    passed = diff <= TOLERANCE
    
    details = {
        "test": "binomial",
        "n": n,
        "p_null": p_null,
        "k_observed": k_obs,
        "empirical_p": empirical_p,
        "library_p": library_p,
        "difference": diff,
        "tolerance": TOLERANCE,
        "replicates": NUM_REPLICATES
    }
    
    logger.info(f"Binomial: empirical={empirical_p:.4f}, library={library_p:.4f}, diff={diff:.4f}, passed={passed}")
    return passed, empirical_p, library_p, details

def run_monte_carlo_validation() -> Dict[str, Any]:
    """
    Run the full Monte-Carlo validation suite.
    
    Returns:
        Dictionary with results for all tests.
    """
    logger = _setup_logging()
    logger.info("=== Starting Monte-Carlo Validation Suite ===")
    
    results = {}
    all_passed = True
    
    # Z-test
    passed, emp, lib, details = validate_z_test(logger)
    results["z_test"] = details
    if not passed:
        all_passed = False
    
    # Fisher's Exact
    passed, emp, lib, details = validate_fisher_exact(logger)
    results["fisher_exact"] = details
    if not passed:
        all_passed = False
    
    # Welch's t-test
    passed, emp, lib, details = validate_welch_t_test(logger)
    results["welch_t"] = details
    if not passed:
        all_passed = False
    
    # Binomial
    passed, emp, lib, details = validate_binomial_test(logger)
    results["binomial"] = details
    if not passed:
        all_passed = False
    
    logger.info("=== Monte-Carlo Validation Complete ===")
    logger.info(f"Overall Status: {'PASSED' if all_passed else 'FAILED'}")
    
    return {
        "overall_passed": all_passed,
        "tolerance": TOLERANCE,
        "replicates": NUM_REPLICATES,
        "tests": results
    }

def main():
    """Entry point for the Monte-Carlo validation script."""
    results = run_monte_carlo_validation()
    
    # Exit with status 0 if all tests passed, 1 otherwise
    if results["overall_passed"]:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
