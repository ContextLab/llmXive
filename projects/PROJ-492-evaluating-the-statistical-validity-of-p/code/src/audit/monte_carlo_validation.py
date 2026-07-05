"""
Monte-Carlo Validation Module (FR-026).

Validates statistical reconstruction logic by comparing empirical p-values
from Monte-Carlo simulations against theoretical library calculations (scipy).
Runs 100,000 replicates for each test type (z-test, Fisher's, Welch's, binomial).
Exits with status 0 if all absolute differences are <= 0.005.
"""
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from scipy import stats

from code.src.audit.monte_carlo_core import (
    set_seeds,
    generate_null_binary_data,
    generate_null_continuous_data,
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
)
from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger

# Configuration
NUM_REPLICATES = 100000
DIFFERENCE_THRESHOLD = 0.005
logger = get_default_logger(__name__)

def validate_z_test() -> Tuple[bool, Dict[str, Any]]:
    """
    Validate two-proportion z-test consistency.
    Simulates data under the null hypothesis (p1 = p2) and compares
    empirical p-value distribution to the theoretical z-test.
    """
    set_seeds(SEED)
    n1, n2 = 1000, 1000
    p_true = 0.5

    # Generate null data (binary outcomes)
    # Under null, p1 = p2 = p_true
    group_a = generate_null_binary_data(n1, p_true)
    group_b = generate_null_binary_data(n2, p_true)

    # Calculate theoretical p-value (two-sided)
    # Using pooled proportion for z-test
    p_pool = (np.sum(group_a) + np.sum(group_b)) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    z_obs = (np.mean(group_a) - np.mean(group_b)) / se
    p_theoretical = 2 * (1 - stats.norm.cdf(np.abs(z_obs)))

    # Monte Carlo simulation
    # We need to simulate the distribution of the test statistic under the null
    # to verify the p-value calculation logic.
    # However, for a single instance, we compare the empirical p-value of the observed
    # statistic against the theoretical one.
    # Better approach: Generate many pairs, compute theoretical and empirical p-values,
    # and check if the proportion of rejections matches alpha (type I error control).
    # But the task asks for "absolute difference <= 0.005". This usually implies
    # comparing the empirical p-value of a specific observed statistic to the theoretical one.
    # Since p-values are random variables, we run the simulation for a fixed observed statistic
    # or check the calibration.
    # Let's interpret as: Compute the empirical p-value by simulating the null distribution
    # of the Z statistic and comparing the position of the observed Z.

    # Generate null distribution of Z statistics
    z_stats = []
    for _ in range(NUM_REPLICATES):
        g_a = generate_null_binary_data(n1, p_true)
        g_b = generate_null_binary_data(n2, p_true)
        p_a, p_b = np.mean(g_a), np.mean(g_b)
        p_pool_sim = (n1*p_a + n2*p_b) / (n1 + n2)
        se_sim = np.sqrt(p_pool_sim * (1 - p_pool_sim) * (1/n1 + 1/n2))
        if se_sim == 0:
            z_stats.append(0.0)
        else:
            z_stats.append((p_a - p_b) / se_sim)

    z_stats = np.array(z_stats)
    empirical_p = (np.sum(np.abs(z_stats) >= np.abs(z_obs)) + 1) / (NUM_REPLICATES + 1)

    diff = abs(empirical_p - p_theoretical)
    passed = diff <= DIFFERENCE_THRESHOLD

    return passed, {
        "test": "z_test",
        "observed_z": float(z_obs),
        "theoretical_p": float(p_theoretical),
        "empirical_p": float(empirical_p),
        "difference": float(diff),
        "passed": passed
    }

def validate_fisher_exact() -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Fisher's Exact Test consistency.
    """
    set_seeds(SEED)
    # Create a contingency table
    # Under null, odds ratio = 1
    # We simulate tables with fixed margins to check the p-value calculation
    n1, n2 = 100, 100
    p_true = 0.5

    # Observed table (simulated)
    # We generate one observed table and then simulate the null distribution
    # by permuting or generating new tables with same margins?
    # Standard Fisher: fixed margins.
    # Let's generate data and fix margins.
    a = int(n1 * p_true)
    b = n1 - a
    c = int(n2 * p_true)
    d = n2 - c

    observed_table = [[a, b], [c, d]]
    row_sums = [sum(observed_table[0]), sum(observed_table[1])]
    col_sums = [sum(x[0] for x in observed_table), sum(x[1] for x in observed_table)]
    total = sum(row_sums)

    # Theoretical p-value
    _, p_theoretical = stats.fisher_exact(observed_table, alternative='two-sided')

    # Monte Carlo: Simulate tables with fixed margins
    # We can use the hypergeometric distribution to simulate 'a'
    # a ~ Hypergeometric(N=total, K=col_sums[0], n=row_sums[0])
    # Then construct the table and compute p-value for each?
    # Actually, Fisher's p-value is the sum of probabilities of tables as or more extreme.
    # To validate, we check if the empirical p-value (fraction of simulated tables with
    # odds ratio as extreme or more extreme) matches the theoretical one.
    # But the theoretical p-value IS the sum of hypergeometric probabilities.
    # So we simulate the hypergeometric distribution and check the cumulative probability.

    # Let's simulate 'a' from Hypergeometric
    # N=total, K=col_sums[0], n=row_sums[0]
    # Then calculate the p-value for that specific 'a' using the hypergeometric PMF
    # and compare the empirical proportion of extreme tables.

    # Simplified: The empirical p-value of the observed table under the null
    # should be close to the theoretical p-value.
    # We simulate many tables with the same margins.
    extreme_count = 0
    odds_ratio_obs = (a * d) / (b * c) if (b * c) != 0 else 0

    for _ in range(NUM_REPLICATES):
        # Sample 'a' from Hypergeometric
        # K = col_sums[0] (total successes in pop), n = row_sums[0] (sample size)
        a_sim = np.random.hypergeometric(col_sums[0], col_sums[1], row_sums[0])
        b_sim = row_sums[0] - a_sim
        c_sim = col_sums[0] - a_sim
        d_sim = row_sums[1] - c_sim

        if b_sim <= 0 or c_sim <= 0:
            or_sim = float('inf') if a_sim * d_sim > 0 else 0
        else:
            or_sim = (a_sim * d_sim) / (b_sim * c_sim)

        # Two-sided: check if |log(OR)| >= |log(OR_obs)|
        # Or use the probability mass. Fisher's exact is usually defined by PMF.
        # Let's use the probability of the table itself as the metric for "extremeness"
        # P(T) = (C(row1, a) * C(row2, c)) / C(N, col1)
        # This is the hypergeometric probability.
        # We count tables with P(T_sim) <= P(T_obs)
        # But calculating factorials for large numbers is hard.
        # Instead, we rely on the property that the empirical p-value from simulation
        # of the null distribution (via permutation or hypergeometric) converges to the exact p-value.

        # Let's just count if the simulated table is as extreme or more extreme in terms of odds ratio
        # This is an approximation of the two-sided test.
        if np.abs(np.log(or_sim + 1e-9)) >= np.abs(np.log(odds_ratio_obs + 1e-9)):
            extreme_count += 1

    p_empirical = (extreme_count + 1) / (NUM_REPLICATES + 1)
    diff = abs(p_empirical - p_theoretical)
    passed = diff <= DIFFERENCE_THRESHOLD

    return passed, {
        "test": "fisher_exact",
        "theoretical_p": float(p_theoretical),
        "empirical_p": float(p_empirical),
        "difference": float(diff),
        "passed": passed
    }

def validate_welch_t_test() -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Welch's t-test consistency.
    """
    set_seeds(SEED)
    n1, n2 = 100, 100
    mu, sigma = 0, 1

    # Generate null data (continuous)
    group_a = generate_null_continuous_data(n1, mu, sigma)
    group_b = generate_null_continuous_data(n2, mu, sigma)

    # Theoretical p-value
    t_obs, p_theoretical = stats.ttest_ind(group_a, group_b, equal_var=False)

    # Monte Carlo: Simulate t-statistics under null
    t_stats = []
    for _ in range(NUM_REPLICATES):
        g_a = generate_null_continuous_data(n1, mu, sigma)
        g_b = generate_null_continuous_data(n2, mu, sigma)
        t_sim, _ = stats.ttest_ind(g_a, g_b, equal_var=False)
        t_stats.append(t_sim)

    t_stats = np.array(t_stats)
    empirical_p = (np.sum(np.abs(t_stats) >= np.abs(t_obs)) + 1) / (NUM_REPLICATES + 1)

    diff = abs(empirical_p - p_theoretical)
    passed = diff <= DIFFERENCE_THRESHOLD

    return passed, {
        "test": "welch_t_test",
        "observed_t": float(t_obs),
        "theoretical_p": float(p_theoretical),
        "empirical_p": float(empirical_p),
        "difference": float(diff),
        "passed": passed
    }

def validate_binomial_test() -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Binomial test consistency.
    """
    set_seeds(SEED)
    n = 100
    p_null = 0.5
    k = int(n * p_null)  # Observed successes under null

    # Theoretical p-value (two-sided)
    # Probability of k or more extreme outcomes
    # For two-sided, it's 2 * min(P(X <= k), P(X >= k)) if symmetric
    # scipy.stats.binom_test handles this
    p_theoretical = stats.binom_test(k, n, p_null, alternative='two-sided')

    # Monte Carlo: Simulate binomial trials
    successes = []
    for _ in range(NUM_REPLICATES):
        s = np.random.binomial(n, p_null)
        successes.append(s)

    # Count how many are as or more extreme than k
    # For two-sided, distance from mean n*p
    mean_val = n * p_null
    dist_obs = abs(k - mean_val)
    extreme_count = 0
    for s in successes:
        dist_s = abs(s - mean_val)
        if dist_s >= dist_obs:
            extreme_count += 1

    p_empirical = (extreme_count + 1) / (NUM_REPLICATES + 1)
    diff = abs(p_empirical - p_theoretical)
    passed = diff <= DIFFERENCE_THRESHOLD

    return passed, {
        "test": "binomial",
        "observed_k": int(k),
        "theoretical_p": float(p_theoretical),
        "empirical_p": float(p_empirical),
        "difference": float(diff),
        "passed": passed
    }

def run_monte_carlo_validation() -> bool:
    """
    Run all validation tests and return True if all pass.
    """
    logger.info("Starting Monte-Carlo validation with %d replicates...", NUM_REPLICATES)

    results = []
    all_passed = True

    # Z-Test
    logger.info("Validating Z-Test...")
    passed, res = validate_z_test()
    results.append(res)
    if not passed:
        all_passed = False
        logger.warning("Z-Test validation FAILED: diff=%.6f", res['difference'])
    else:
        logger.info("Z-Test validation PASSED.")

    # Fisher's Exact
    logger.info("Validating Fisher's Exact Test...")
    passed, res = validate_fisher_exact()
    results.append(res)
    if not passed:
        all_passed = False
        logger.warning("Fisher's Exact validation FAILED: diff=%.6f", res['difference'])
    else:
        logger.info("Fisher's Exact validation PASSED.")

    # Welch's T-Test
    logger.info("Validating Welch's T-Test...")
    passed, res = validate_welch_t_test()
    results.append(res)
    if not passed:
        all_passed = False
        logger.warning("Welch's T-Test validation FAILED: diff=%.6f", res['difference'])
    else:
        logger.info("Welch's T-Test validation PASSED.")

    # Binomial Test
    logger.info("Validating Binomial Test...")
    passed, res = validate_binomial_test()
    results.append(res)
    if not passed:
        all_passed = False
        logger.warning("Binomial Test validation FAILED: diff=%.6f", res['difference'])
    else:
        logger.info("Binomial Test validation PASSED.")

    # Log summary
    logger.info("Monte-Carlo validation complete. All tests passed: %s", all_passed)
    for r in results:
        logger.info("  %s: p_theo=%.4f, p_emp=%.4f, diff=%.4f, pass=%s",
                    r['test'], r['theoretical_p'], r['empirical_p'], r['difference'], r['passed'])

    return all_passed

def main():
    """
    Entry point for the Monte-Carlo validation module.
    Exits with status 0 if all tests pass, 1 otherwise.
    """
    try:
        success = run_monte_carlo_validation()
        if success:
            logger.info("All Monte-Carlo validations passed. Exiting with status 0.")
            sys.exit(0)
        else:
            logger.error("Some Monte-Carlo validations failed. Exiting with status 1.")
            sys.exit(1)
    except Exception as e:
        logger.exception("Monte-Carlo validation failed with exception: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
