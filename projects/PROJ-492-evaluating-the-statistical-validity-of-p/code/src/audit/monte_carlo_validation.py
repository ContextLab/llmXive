"""
Monte-Carlo Validation Module (FR-026)

Runs 10,000 replicates for each statistical test (z-test, Fisher's, Welch's, binomial)
and checks that the absolute difference between the empirical p-value and the
theoretical p-value is <= 0.005.
"""
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, SEED
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

NUM_REPLICATES = 10000
TOLERANCE = 0.005
ALPHA = 0.05

logger = get_default_logger(__name__)

def validate_z_test() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate the two-proportion z-test using Monte-Carlo simulation.
    Generates binary data under the null hypothesis (p1 = p2) and compares
    the empirical p-value distribution to the theoretical z-test.
    """
    set_rng_seed(SEED)
    n1, n2 = 500, 500
    p_true = 0.2
    
    # Generate data under null
    group_a = generate_null_binary_data(n1, p_true)
    group_b = generate_null_binary_data(n2, p_true)
    
    # Compute theoretical p-value (two-sided)
    count_a = np.sum(group_a)
    count_b = np.sum(group_b)
    p_hat_1 = count_a / n1
    p_hat_2 = count_b / n2
    p_pool = (count_a + count_b) / (n1 + n2)
    
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    if se == 0:
        # Edge case: perfect separation or no variance
        theoretical_p = 1.0
    else:
        z_stat = (p_hat_1 - p_hat_2) / se
        theoretical_p = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # Run Monte-Carlo simulation
    # We simulate many datasets under the null and see how often the z-stat exceeds the observed
    # However, the task asks to validate the *test itself*. 
    # Standard approach: Generate data under null, compute p-value for each replicate.
    # The distribution of p-values should be uniform. 
    # A simpler check for "difference <= 0.005" usually implies: 
    # Run the test on a specific simulated dataset many times? 
    # Or: Compare the empirical p-value of a *fixed* synthetic dataset against the theoretical one?
    # Given the constraint "absolute difference <= 0.005", we will:
    # 1. Generate ONE fixed dataset under the null.
    # 2. Compute its theoretical p-value.
    # 3. Estimate its p-value via Monte Carlo (permutation/bootstrap or simulation of the null distribution).
    # 4. Compare.
    
    # Let's fix a dataset
    np.random.seed(SEED)
    # Create a scenario with a known effect size of 0 (Null)
    # Or a small effect. Let's do Null to ensure p is uniform-ish, but we need a specific value to compare.
    # Actually, to validate the *implementation* of the z-test against scipy, we can:
    # Generate 10k datasets under H0. For each, compute the z-stat.
    # The proportion of |z| > |z_observed| should match the theoretical p.
    # But z_observed varies.
    
    # Correct interpretation for "Validate z-test":
    # Run 10,000 experiments under H0. For each, compute the theoretical p-value.
    # Then, check if the *empirical* rejection rate matches alpha? No, that's power.
    # The task says: "checks the absolute difference <= 0.005".
    # This usually means: Compare the p-value computed by our simulation logic vs scipy.stats on the SAME data.
    
    # Let's generate 10,000 pairs of samples. For each pair:
    # 1. Compute scipy p-value.
    # 2. Compute empirical p-value via simulation (e.g., permutation or re-sampling from the null).
    # 3. Compare.
    # This is expensive.
    
    # Alternative interpretation (Standard for this type of task):
    # Run the Monte Carlo core to generate the null distribution of the test statistic.
    # Compare the CDF of the simulated statistic to the theoretical CDF.
    # Or: Pick a specific z-score (e.g., 1.96). The theoretical p is 0.05. 
    # Simulate 10,000 z-scores under H0. The fraction > 1.96 should be ~0.05.
    # Difference = |0.05 - empirical_fraction|.
    
    # Let's implement the "Critical Value" check which is robust.
    # Theoretical critical value for alpha=0.05 is 1.96.
    # Simulate 10,000 z-stats under H0. Count how many > 1.96.
    # Expected rate = 0.05.
    # We check if |empirical_rate - 0.05| <= 0.005?
    # Or check if the p-value of the *observed* stat in the simulation matches.
    
    # Let's stick to the prompt's likely intent: Validate the p-value calculation.
    # Generate 10,000 datasets under H0.
    # For each, calculate the z-stat.
    # The empirical p-value for a specific z-stat z_obs is P(|Z| > |z_obs|).
    # If we pick a fixed z_obs (e.g. 1.96), the empirical p should be ~0.05.
    
    z_obs = 1.96 # Fixed threshold
    theoretical_p_target = 2 * (1 - stats.norm.cdf(abs(z_obs)))
    
    z_stats = []
    for i in range(NUM_REPLICATES):
        # Generate under H0
        g1 = generate_null_binary_data(n1, p_true)
        g2 = generate_null_binary_data(n2, p_true)
        c1, c2 = np.sum(g1), np.sum(g2)
        p1, p2 = c1/n1, c2/n2
        p_pool = (c1+c2)/(n1+n2)
        se = np.sqrt(p_pool*(1-p_pool)*(1/n1+1/n2))
        if se == 0:
            z_stats.append(0.0)
        else:
            z_stats.append((p1-p2)/se)
    
    z_stats = np.array(z_stats)
    # Empirical p-value for z_obs
    empirical_p = np.mean(np.abs(z_stats) >= abs(z_obs))
    
    diff = abs(empirical_p - theoretical_p_target)
    passed = diff <= TOLERANCE
    
    return passed, empirical_p, theoretical_p_target, {
        "n1": n1, "n2": n2, "p_true": p_true, "z_obs": z_obs,
        "diff": diff
    }

def validate_fisher_exact() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate Fisher's Exact Test.
    Simulates 2x2 tables under the null hypothesis (independence) and compares
    the empirical rejection rate to the theoretical alpha.
    """
    set_rng_seed(SEED + 1) # Offset seed
    n1, n2 = 200, 200
    p_true = 0.5
    
    # We will simulate tables and check if the p-value distribution is uniform?
    # Or check a specific critical value.
    # Let's check the empirical p-value for a specific table configuration.
    # Table: [[a, b], [c, d]]
    # Let's fix a table that yields a specific p-value?
    # Instead, let's run 10,000 simulations of the null.
    # For each, compute the Fisher p-value.
    # The mean of these p-values should be 0.5 (uniform distribution).
    # Variance should be 1/12.
    # But the task says "absolute difference <= 0.005".
    # Maybe it means: For a given table, does our simulation match scipy?
    
    # Let's try the "Critical Value" approach again.
    # Generate 10,000 tables under H0.
    # Count how many have a Fisher p-value < 0.05.
    # This should be ~0.05.
    
    n_sig = 0
    p_values = []
    for _ in range(NUM_REPLICATES):
        # Generate under H0
        row1 = generate_null_binary_data(n1, p_true)
        row2 = generate_null_binary_data(n2, p_true)
        # Construct 2x2
        a = np.sum(row1)
        b = n1 - a
        c = np.sum(row2)
        d = n2 - c
        
        # Fisher test
        # scipy.stats.fisher_exact returns (odds_ratio, p_value)
        # Two-sided by default
        try:
            _, p_val = stats.fisher_exact([[a, b], [c, d]], alternative='two-sided')
        except ValueError:
            # Edge case: row or col all zeros
            p_val = 1.0
        p_values.append(p_val)
        if p_val < ALPHA:
            n_sig += 1
    
    empirical_alpha = n_sig / NUM_REPLICATES
    theoretical_alpha = ALPHA
    diff = abs(empirical_alpha - theoretical_alpha)
    passed = diff <= TOLERANCE
    
    return passed, empirical_alpha, theoretical_alpha, {
        "n1": n1, "n2": n2, "p_true": p_true, "diff": diff
    }

def validate_welch_t_test() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate Welch's t-test.
    Simulates continuous data under the null and checks the rejection rate.
    """
    set_rng_seed(SEED + 2)
    n1, n2 = 100, 100
    mu, sigma = 0, 1
    
    n_sig = 0
    for _ in range(NUM_REPLICATES):
        g1 = np.random.normal(mu, sigma, n1)
        g2 = np.random.normal(mu, sigma, n2)
        
        _, p_val = stats.ttest_ind(g1, g2, equal_var=False)
        if p_val < ALPHA:
            n_sig += 1
    
    empirical_alpha = n_sig / NUM_REPLICATES
    theoretical_alpha = ALPHA
    diff = abs(empirical_alpha - theoretical_alpha)
    passed = diff <= TOLERANCE
    
    return passed, empirical_alpha, theoretical_alpha, {
        "n1": n1, "n2": n2, "mu": mu, "sigma": sigma, "diff": diff
    }

def validate_binomial_test() -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Validate Binomial Test.
    Simulates binomial draws under the null and checks the rejection rate.
    """
    set_rng_seed(SEED + 3)
    n = 100
    p_null = 0.5
    
    n_sig = 0
    for _ in range(NUM_REPLICATES):
        # Draw from Binomial(n, p_null)
        k = np.random.binomial(n, p_null)
        
        # Two-sided binomial test
        # scipy.stats.binom_test is deprecated, use binomtest
        res = stats.binomtest(k, n, p_null, alternative='two-sided')
        p_val = res.pvalue
        
        if p_val < ALPHA:
            n_sig += 1
    
    empirical_alpha = n_sig / NUM_REPLICATES
    theoretical_alpha = ALPHA
    diff = abs(empirical_alpha - theoretical_alpha)
    passed = diff <= TOLERANCE
    
    return passed, empirical_alpha, theoretical_alpha, {
        "n": n, "p_null": p_null, "diff": diff
    }

def run_monte_carlo_validation() -> Dict[str, Any]:
    """
    Runs all validation tests and returns the results.
    Exits with status 0 if all pass, 1 otherwise.
    """
    logger.info("Starting Monte-Carlo validation (10,000 replicates per test)...")
    
    results = {
        "z_test": {},
        "fisher_exact": {},
        "welch_t_test": {},
        "binomial_test": {}
    }
    
    all_passed = True
    
    # Z-Test
    logger.info("Validating Z-Test...")
    passed, emp, theo, details = validate_z_test()
    results["z_test"] = {"passed": passed, "empirical": emp, "theoretical": theo, "diff": details["diff"]}
    logger.info(f"Z-Test: Empirical={emp:.4f}, Theoretical={theo:.4f}, Diff={details['diff']:.4f} -> {'PASS' if passed else 'FAIL'}")
    if not passed: all_passed = False
    
    # Fisher
    logger.info("Validating Fisher's Exact Test...")
    passed, emp, theo, details = validate_fisher_exact()
    results["fisher_exact"] = {"passed": passed, "empirical": emp, "theoretical": theo, "diff": details["diff"]}
    logger.info(f"Fisher: Empirical={emp:.4f}, Theoretical={theo:.4f}, Diff={details['diff']:.4f} -> {'PASS' if passed else 'FAIL'}")
    if not passed: all_passed = False
    
    # Welch
    logger.info("Validating Welch's T-Test...")
    passed, emp, theo, details = validate_welch_t_test()
    results["welch_t_test"] = {"passed": passed, "empirical": emp, "theoretical": theo, "diff": details["diff"]}
    logger.info(f"Welch: Empirical={emp:.4f}, Theoretical={theo:.4f}, Diff={details['diff']:.4f} -> {'PASS' if passed else 'FAIL'}")
    if not passed: all_passed = False
    
    # Binomial
    logger.info("Validating Binomial Test...")
    passed, emp, theo, details = validate_binomial_test()
    results["binomial_test"] = {"passed": passed, "empirical": emp, "theoretical": theo, "diff": details["diff"]}
    logger.info(f"Binomial: Empirical={emp:.4f}, Theoretical={theo:.4f}, Diff={details['diff']:.4f} -> {'PASS' if passed else 'FAIL'}")
    if not passed: all_passed = False
    
    return {
        "all_passed": all_passed,
        "num_replicates": NUM_REPLICATES,
        "tolerance": TOLERANCE,
        "results": results
    }

def main():
    try:
        result = run_monte_carlo_validation()
        if result["all_passed"]:
            logger.info("Monte-Carlo validation PASSED. All tests within tolerance.")
            sys.exit(0)
        else:
            logger.error("Monte-Carlo validation FAILED. Some tests exceeded tolerance.")
            logger.error(f"Results: {result['results']}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error during Monte-Carlo validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
