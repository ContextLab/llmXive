"""
Monte-Carlo validation module for statistical tests (FR-026).

Runs 10,000 replicates for z-test, Fisher's exact, Welch's t-test, and binomial test.
Validates that the absolute difference between Monte-Carlo estimates and scipy library
results is <= 0.005.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
from scipy import stats

from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, get_error_message

# Configuration
NUM_REPLICATES = 10000
TOLERANCE = 0.005
SEED = 42

logger = get_default_logger(__name__)

def validate_z_test() -> Tuple[bool, float, float, str]:
    """
    Validate two-proportion z-test.
    Compares Monte-Carlo p-value distribution mean against scipy.stats.proportions_ztest.
    """
    set_rng_seed(SEED)
    logger.info("Starting Monte-Carlo validation for z-test (two-proportion).")

    # Fixed parameters for reproducibility
    count1, n1 = 150, 1000
    count2, n2 = 120, 1000

    # Calculate true p-value using scipy
    # Using 'two-sided' alternative
    stat_true, p_true = stats.proportions_ztest([count1, count2], [n1, n2], alternative='two-sided')

    # Monte-Carlo simulation: generate data under null hypothesis
    # Null hypothesis: p1 = p2 = pooled_p
    pooled_p = (count1 + count2) / (n1 + n2)
    
    mc_p_values = []
    
    for _ in range(NUM_REPLICATES):
        # Simulate data under null
        sim_count1 = np.random.binomial(n1, pooled_p)
        sim_count2 = np.random.binomial(n2, pooled_p)
        
        # Avoid division by zero or edge cases where n is effectively 0 (unlikely here but safe)
        if n1 == 0 or n2 == 0:
            continue
        
        try:
            sim_stat, sim_p = stats.proportions_ztest(
                [sim_count1, sim_count2], 
                [n1, n2], 
                alternative='two-sided'
            )
            mc_p_values.append(sim_p)
        except ValueError:
            # Handle cases where scipy might fail (e.g., all successes or all failures in sim)
            continue

    if not mc_p_values:
        return False, 0.0, 0.0, "No valid Monte-Carlo replicates generated."

    mc_mean_p = float(np.mean(mc_p_values))
    abs_diff = abs(mc_mean_p - p_true)
    
    passed = abs_diff <= TOLERANCE
    status_msg = f"Z-Test: True p={p_true:.4f}, MC Mean p={mc_mean_p:.4f}, Diff={abs_diff:.4f} -> {'PASS' if passed else 'FAIL'}"
    
    logger.info(status_msg)
    return passed, abs_diff, p_true, status_msg


def validate_fisher_exact() -> Tuple[bool, float, float, str]:
    """
    Validate Fisher's Exact Test.
    Compares Monte-Carlo estimated p-value against scipy.stats.fisher_exact.
    """
    set_rng_seed(SEED)
    logger.info("Starting Monte-Carlo validation for Fisher's Exact Test.")

    # Fixed contingency table
    table = [[150, 850], [120, 880]] # [[a, b], [c, d]]
    
    # True p-value from scipy (two-sided)
    _, p_true = stats.fisher_exact(table, alternative='two-sided')

    # Monte-Carlo simulation: permute labels while keeping marginals fixed
    # We simulate the distribution of the odds ratio or the cell count 'a'
    # Under null, the probability of 'a' follows a hypergeometric distribution.
    # However, to simulate the p-value directly, we can sample contingency tables
    # with the same marginals.
    
    n1 = table[0][0] + table[0][1]
    n2 = table[1][0] + table[1][1]
    c1 = table[0][0] + table[1][0]
    c2 = table[0][1] + table[1][1]
    n_total = n1 + n2

    mc_p_values = []

    for _ in range(NUM_REPLICATES):
        # Sample 'a' from Hypergeometric(N=n_total, K=c1, n=n1)
        # This is equivalent to sampling a table with fixed marginals
        sim_a = np.random.hypergeometric(c1, c2, n1)
        
        sim_table = [
            [sim_a, n1 - sim_a],
            [c1 - sim_a, c2 - (n1 - sim_a)]
        ]
        
        # Ensure non-negative
        if sim_table[1][1] < 0:
            continue

        try:
            _, sim_p = stats.fisher_exact(sim_table, alternative='two-sided')
            mc_p_values.append(sim_p)
        except ValueError:
            continue

    if not mc_p_values:
        return False, 0.0, 0.0, "No valid Monte-Carlo replicates generated."

    mc_mean_p = float(np.mean(mc_p_values))
    abs_diff = abs(mc_mean_p - p_true)

    passed = abs_diff <= TOLERANCE
    status_msg = f"Fisher: True p={p_true:.4f}, MC Mean p={mc_mean_p:.4f}, Diff={abs_diff:.4f} -> {'PASS' if passed else 'FAIL'}"

    logger.info(status_msg)
    return passed, abs_diff, p_true, status_msg


def validate_welch_t_test() -> Tuple[bool, float, float, str]:
    """
    Validate Welch's t-test.
    Compares Monte-Carlo p-value distribution against scipy.stats.ttest_ind.
    """
    set_rng_seed(SEED)
    logger.info("Starting Monte-Carlo validation for Welch's t-test.")

    # Fixed parameters
    mean1, std1, n1 = 5.0, 1.0, 50
    mean2, std2, n2 = 5.5, 1.2, 50

    # Generate true data to get the "observed" statistic
    # We simulate the null hypothesis: means are equal
    # So we generate both groups from the same distribution (e.g., mean1)
    # But to compare against a specific scipy result, we usually compare the 
    # empirical distribution of p-values under the null to a uniform distribution,
    # OR we compare the p-value of a specific observed statistic.
    
    # The task asks to check the difference <= 0.005. 
    # This implies comparing the Monte-Carlo estimated p-value of a specific 
    # observed statistic against the analytical p-value of that statistic.
    
    # Let's generate a fixed "observed" dataset
    np.random.seed(SEED)
    obs1 = np.random.normal(mean1, std1, n1)
    obs2 = np.random.normal(mean2, std2, n2)
    
    # Analytical p-value for the observed data
    stat_true, p_true = stats.ttest_ind(obs1, obs2, equal_var=False)

    # Monte-Carlo: Simulate data under Null (means equal) to see where obs_stat falls?
    # No, the standard validation is: 
    # 1. Calculate p_true for obs1, obs2.
    # 2. Re-run the test on many resamples? No, that tests power.
    # 3. Correct approach for "validity": 
    #    Generate data under Null (mean1=mean2). Calculate p-values. 
    #    The distribution of p-values should be Uniform(0,1).
    #    But the requirement says "absolute difference <= 0.005".
    #    This suggests comparing the p-value of a specific instance.
    
    # Alternative interpretation: 
    # "Validate that the Monte-Carlo implementation (if we were writing one) matches scipy."
    # Since we are using scipy for the "true" value, we must simulate the test statistic
    # distribution to estimate the p-value and compare it to scipy's analytical p-value.
    
    # Let's fix the observed statistic from a random seed, then estimate its p-value via MC.
    # Observed data generation (fixed seed)
    np.random.seed(SEED + 100) 
    data1 = np.random.normal(0, 1, n1)
    data2 = np.random.normal(0.5, 1.2, n2) # Slight difference
    
    stat_obs, p_analytical = stats.ttest_ind(data1, data2, equal_var=False)
    
    # Monte-Carlo estimation of p-value for this observed statistic
    # We simulate the null distribution of the t-statistic
    mc_stats = []
    for _ in range(NUM_REPLICATES):
        # Simulate under Null: same mean (0), same variance? Welch assumes unequal variances possible.
        # To be safe, we pool variances or use the observed variances as the null?
        # Standard MC for t-test: permute labels or resample from pooled distribution.
        # Let's use permutation test (exact under exchangeability)
        combined = np.concatenate([data1, data2])
        np.random.shuffle(combined)
        sim1 = combined[:n1]
        sim2 = combined[n1:]
        sim_stat, _ = stats.ttest_ind(sim1, sim2, equal_var=False)
        mc_stats.append(sim_stat)
    
    # Calculate empirical p-value (two-sided)
    # p = (count(|t| >= |t_obs|) + 1) / (N + 1)
    abs_t_obs = abs(stat_obs)
    abs_t_mc = np.abs(mc_stats)
    count_extreme = np.sum(abs_t_mc >= abs_t_obs)
    p_mc = (count_extreme + 1) / (NUM_REPLICATES + 1)
    
    abs_diff = abs(p_mc - p_analytical)
    passed = abs_diff <= TOLERANCE
    
    status_msg = f"Welch T: Analytical p={p_analytical:.4f}, MC p={p_mc:.4f}, Diff={abs_diff:.4f} -> {'PASS' if passed else 'FAIL'}"
    logger.info(status_msg)
    
    return passed, abs_diff, p_analytical, status_msg


def validate_binomial_test() -> Tuple[bool, float, float, str]:
    """
    Validate Binomial Test.
    Compares Monte-Carlo p-value against scipy.stats.binom_test.
    """
    set_rng_seed(SEED)
    logger.info("Starting Monte-Carlo validation for Binomial Test.")

    # Fixed parameters
    k = 60 # successes
    n = 100 # trials
    p_null = 0.5 # null probability

    # Analytical p-value (two-sided)
    # Note: scipy.stats.binom_test is deprecated in favor of binomtest in newer versions,
    # but we use binomtest for accuracy.
    res = stats.binomtest(k, n, p=p_null, alternative='two-sided')
    p_true = res.pvalue

    # Monte-Carlo simulation
    # Simulate n trials with probability p_null, count successes, see how extreme k is.
    mc_p_values = []
    
    for _ in range(NUM_REPLICATES):
        sim_k = np.random.binomial(n, p_null)
        # Calculate two-sided p-value for this sim_k relative to null?
        # Actually, we want to estimate the probability of observing a result 
        # as extreme or more extreme than k=60.
        # So we just count how many sim_k are as extreme as k.
        
        # Extreme means P(X <= k) or P(X >= k) depending on side?
        # For two-sided binomial, it's sum of probabilities <= P(k).
        # But in MC, we just count frequency of |sim_k - n*p| >= |k - n*p|
        
        diff_obs = abs(k - n * p_null)
        diff_sim = abs(sim_k - n * p_null)
        
        if diff_sim >= diff_obs:
            mc_p_values.append(1)
        else:
            mc_p_values.append(0)

    p_mc = float(np.mean(mc_p_values))
    abs_diff = abs(p_mc - p_true)
    
    passed = abs_diff <= TOLERANCE
    status_msg = f"Binomial: True p={p_true:.4f}, MC p={p_mc:.4f}, Diff={abs_diff:.4f} -> {'PASS' if passed else 'FAIL'}"
    
    logger.info(status_msg)
    return passed, abs_diff, p_true, status_msg


def run_monte_carlo_validation() -> bool:
    """
    Run all Monte-Carlo validations and return True if all pass.
    """
    logger.info("Running full Monte-Carlo validation suite (10,000 replicates per test).")
    
    results = []
    
    # Z-Test
    passed_z, diff_z, true_z, msg_z = validate_z_test()
    results.append(("z-test", passed_z, diff_z, true_z))
    
    # Fisher
    passed_f, diff_f, true_f, msg_f = validate_fisher_exact()
    results.append(("Fisher's Exact", passed_f, diff_f, true_f))
    
    # Welch T
    passed_w, diff_w, true_w, msg_w = validate_welch_t_test()
    results.append(("Welch's T", passed_w, diff_w, true_w))
    
    # Binomial
    passed_b, diff_b, true_b, msg_b = validate_binomial_test()
    results.append(("Binomial", passed_b, diff_b, true_b))
    
    all_passed = all(r[1] for r in results)
    
    logger.info("=" * 50)
    logger.info("Monte-Carlo Validation Summary")
    for name, passed, diff, true_val in results:
        status = "PASS" if passed else "FAIL"
        logger.info(f"{name}: {status} (Diff: {diff:.5f}, Threshold: {TOLERANCE})")
    logger.info("=" * 50)
    
    if not all_passed:
        logger.error("Monte-Carlo validation FAILED. One or more tests exceeded tolerance.")
        return False
    
    logger.info("Monte-Carlo validation PASSED. All tests within tolerance.")
    return True


def main():
    """
    Entry point for the module.
    Exits with status 0 if validation passes, 1 otherwise.
    """
    try:
        success = run_monte_carlo_validation()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Validation suite failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()