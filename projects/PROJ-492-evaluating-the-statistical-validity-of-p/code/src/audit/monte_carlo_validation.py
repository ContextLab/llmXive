"""
Monte-Carlo Validation Module (FR-026).

Validates statistical test implementations (z-test, Fisher's exact, Welch's t-test,
binomial test) by comparing their p-values against Monte-Carlo simulated ground truth.

Criteria: Absolute difference between library p-value and Monte-Carlo p-value <= 0.005.
Replicates: 10,000 per test.
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
from code.src.config import SEED
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

logger: AuditLogger = get_default_logger(__name__)

# Configuration constants
NUM_REPLICATES = 10000
TOLERANCE_THRESHOLD = 0.005
ALPHA = 0.05


def validate_z_test(rng: np.random.Generator) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate two-proportion z-test against Monte-Carlo simulation.

    Returns:
        Tuple of (is_valid, details_dict)
    """
    logger.info("Running Monte-Carlo validation for Z-Test (Two Proportion)")

    # Parameters for simulation
    n1, n2 = 1000, 1000
    p1, p2 = 0.5, 0.55  # Small effect size

    # Generate data
    x1 = rng.binomial(n1, p1)
    x2 = rng.binomial(n2, p2)

    # 1. Compute Library P-value (Two-sided)
    try:
        # scipy.stats.proportions_ztest
        stat_lib, p_lib = stats.proportions_ztest([x1, x2], [n1, n2], alternative='two-sided')
    except Exception as e:
        logger.error(f"Library Z-Test failed: {e}")
        return False, {"error": str(e), "test": "z_test"}

    # 2. Compute Monte-Carlo P-value
    # Simulate under null hypothesis (p1 = p2)
    # We pool the proportion for the null
    pooled_p = (x1 + x2) / (n1 + n2)

    mc_p_values = []
    for _ in range(NUM_REPLICATES):
        # Generate data under null
        y1 = rng.binomial(n1, pooled_p)
        y2 = rng.binomial(n2, pooled_p)

        # Simulate statistic
        try:
            stat_sim = simulate_z_test_statistic(y1, y2, n1, n2, pooled_p)
            mc_p_values.append(stat_sim)
        except Exception:
            continue

    if not mc_p_values:
        logger.error("Monte-Carlo simulation produced no valid statistics for Z-Test.")
        return False, {"error": "No MC samples", "test": "z_test"}

    # Compute empirical p-value (two-sided: count stats >= |observed|)
    # Note: simulate_z_test_statistic returns the z-statistic
    observed_abs_stat = abs(stat_lib)
    # Count how many simulated stats are as extreme or more extreme
    extreme_count = sum(1 for s in mc_p_values if abs(s) >= observed_abs_stat)
    p_mc = extreme_count / NUM_REPLICATES

    diff = abs(p_lib - p_mc)
    is_valid = diff <= TOLERANCE_THRESHOLD

    details = {
        "test": "z_test",
        "p_library": p_lib,
        "p_monte_carlo": p_mc,
        "difference": diff,
        "threshold": TOLERANCE_THRESHOLD,
        "valid": is_valid,
        "replicates": NUM_REPLICATES
    }

    if is_valid:
        logger.info(f"Z-Test validation PASSED (diff={diff:.5f})")
    else:
        logger.error(f"Z-Test validation FAILED (diff={diff:.5f} > {TOLERANCE_THRESHOLD})")

    return is_valid, details


def validate_fisher_exact(rng: np.random.Generator) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Fisher's Exact Test against Monte-Carlo simulation.

    Returns:
        Tuple of (is_valid, details_dict)
    """
    logger.info("Running Monte-Carlo validation for Fisher's Exact Test")

    # Parameters
    n1, n2 = 100, 100
    p1, p2 = 0.4, 0.5

    # Generate data
    x1 = rng.binomial(n1, p1)
    x2 = rng.binomial(n2, p2)

    # 1. Library P-value
    try:
        table = [[x1, n1 - x1], [x2, n2 - x2]]
        res = stats.fisher_exact(table, alternative='two-sided')
        p_lib = res.pvalue
    except Exception as e:
        logger.error(f"Library Fisher Exact failed: {e}")
        return False, {"error": str(e), "test": "fisher_exact"}

    # 2. Monte-Carlo P-value
    # Simulate contingency tables with fixed margins (hypergeometric distribution)
    # The null hypothesis is that the odds ratio is 1.
    # We simulate by shuffling the outcomes while keeping row/col totals fixed.
    # Or simpler: generate counts from hypergeometric distribution directly.
    # Total successes = x1 + x2, Total failures = (n1+n2) - (x1+x2)
    # We draw x1' from Hypergeometric(N=n1+n2, K=x1+x2, n=n1)
    
    total_successes = x1 + x2
    total_n = n1 + n2
    
    mc_p_values = []
    for _ in range(NUM_REPLICATES):
        # Simulate x1 under null
        x1_sim = rng.hypergeometric(
            ngood=total_successes,
            nbad=total_n - total_successes,
            nsample=n1
        )
        x2_sim = total_successes - x1_sim
        
        # Ensure non-negative (hypergeometric handles this, but just in case)
        if x2_sim < 0 or x2_sim > n2:
            continue

        table_sim = [[x1_sim, n1 - x1_sim], [x2_sim, n2 - x2_sim]]
        
        # Compute statistic (odds ratio) or p-value?
        # To compare p-values directly, we need the p-value of the simulated table.
        # However, computing Fisher's exact for every simulation is slow.
        # Alternative: Compare the Odds Ratio statistic distribution.
        # But the task asks to check p-value difference <= 0.005.
        # Let's approximate the p-value via the hypergeometric probability mass.
        # P-value = sum of probabilities of tables as extreme or more extreme.
        # This is computationally heavy for MC if we sum PMF.
        # Instead, we can simulate the p-value by counting how many tables are more extreme.
        
        # Let's use the Odds Ratio as the statistic for ordering.
        # OR = (x1 * x2_fail) / (x1_fail * x2)
        # If x1_fail or x2 is 0, OR is 0 or inf.
        try:
            or_sim = (x1_sim * (n2 - x2_sim)) / ((n1 - x1_sim) * x2_sim) if (n1-x1_sim)*x2_sim != 0 else float('inf')
        except:
            continue
        
        # We need the observed OR
        try:
            or_obs = (x1 * (n2 - x2)) / ((n1 - x1) * x2) if (n1-x1)*x2 != 0 else float('inf')
        except:
            continue

        # We need to define "extreme". Two-sided: |log(OR)| >= |log(OR_obs)|
        # Or simpler: count how many simulated ORs are as extreme or more extreme.
        # But this is tricky with 0/Inf.
        
        # Let's fallback to a simpler MC approach for Fisher:
        # Simulate the p-value directly by generating tables and computing exact p for each? Too slow.
        # Let's use the hypergeometric probability of the observed table and sum tails.
        # Actually, the standard MC Fisher approximates the p-value by counting tables with p <= p_obs.
        # That's circular.
        
        # Let's use the statistic: the count x1.
        # P-value = P(X1 <= x1_obs | H0) + P(X1 >= x1_obs | H0) depending on direction.
        # Since we generated under H0, the p-value is simply the proportion of simulated x1
        # that are as or more extreme than the observed x1.
        
        # Determine direction
        if x1 > (n1 * total_successes / total_n):
            # Right tail
            extreme = sum(1 for _ in range(NUM_REPLICATES) if rng.hypergeometric(total_successes, total_n-total_successes, n1) >= x1)
            # Wait, we need to do this in one pass.
            pass
        
        # Correct approach for MC p-value of Fisher's:
        # 1. Calculate observed statistic (e.g., x1 or OR).
        # 2. Simulate many tables under H0.
        # 3. Calculate statistic for each.
        # 4. Count how many simulated stats are as or more extreme than observed.
        
        # Let's use x1 as the statistic.
        # Observed x1.
        # Simulate x1_sim.
        # More extreme: if x1 > expected, then x1_sim >= x1. If x1 < expected, x1_sim <= x1.
        
        expected_x1 = n1 * total_successes / total_n
        if x1 >= expected_x1:
            # Right tail
            pass # We'll count in the loop below
        else:
            # Left tail
            pass

        # Let's just collect all simulated x1s first
        pass

    # Re-implementing Fisher MC logic cleanly
    mc_extreme_count = 0
    expected_x1 = n1 * total_successes / total_n
    is_right_tailed = x1 >= expected_x1
    
    # We need to generate the simulated tables and compare
    # But to compare "p-values", we are essentially checking if the library p-value
    # matches the MC estimated p-value.
    # MC Estimated P = (count of simulated tables with p_sim <= p_obs + 1) / (N + 1)
    # But computing p_sim for every table is expensive.
    # Instead, we use the statistic ordering.
    # P-value = P(T >= T_obs) or P(T <= T_obs).
    # We will count how many simulated T are as extreme as T_obs.
    
    # Let's collect simulated x1s
    sim_x1s = []
    for _ in range(NUM_REPLICATES):
        val = rng.hypergeometric(total_successes, total_n - total_successes, n1)
        sim_x1s.append(val)
    
    if is_right_tailed:
        mc_extreme_count = sum(1 for val in sim_x1s if val >= x1)
    else:
        mc_extreme_count = sum(1 for val in sim_x1s if val <= x1)
    
    p_mc = mc_extreme_count / NUM_REPLICATES

    diff = abs(p_lib - p_mc)
    is_valid = diff <= TOLERANCE_THRESHOLD

    details = {
        "test": "fisher_exact",
        "p_library": p_lib,
        "p_monte_carlo": p_mc,
        "difference": diff,
        "threshold": TOLERANCE_THRESHOLD,
        "valid": is_valid,
        "replicates": NUM_REPLICATES
    }

    if is_valid:
        logger.info(f"Fisher Exact validation PASSED (diff={diff:.5f})")
    else:
        logger.error(f"Fisher Exact validation FAILED (diff={diff:.5f} > {TOLERANCE_THRESHOLD})")

    return is_valid, details


def validate_welch_t_test(rng: np.random.Generator) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Welch's t-test against Monte-Carlo simulation.

    Returns:
        Tuple of (is_valid, details_dict)
    """
    logger.info("Running Monte-Carlo validation for Welch's T-Test")

    # Parameters
    n1, n2 = 100, 150
    mu1, mu2 = 0, 0.2
    sigma1, sigma2 = 1.0, 1.2

    # Generate data
    data1 = rng.normal(mu1, sigma1, n1)
    data2 = rng.normal(mu2, sigma2, n2)

    # 1. Library P-value
    try:
        stat_lib, p_lib = stats.ttest_ind(data1, data2, equal_var=False)
    except Exception as e:
        logger.error(f"Library Welch T-Test failed: {e}")
        return False, {"error": str(e), "test": "welch_t_test"}

    # 2. Monte-Carlo P-value
    # Simulate under null (mu1 = mu2). Center both samples at 0.
    # We shift data1 and data2 to have mean 0, then resample?
    # Or just generate new data from N(0, sigma) with estimated sigmas.
    # Better: Permutation test style or parametric bootstrap under H0.
    # Parametric: Generate data from N(0, sigma1) and N(0, sigma2).
    
    # Estimate sigmas from data (or use known if we control generation, but let's be robust)
    s1 = np.std(data1, ddof=1)
    s2 = np.std(data2, ddof=1)
    
    mc_p_values = []
    for _ in range(NUM_REPLICATES):
        y1 = rng.normal(0, s1, n1)
        y2 = rng.normal(0, s2, n2)
        
        try:
            stat_sim, _ = stats.ttest_ind(y1, y2, equal_var=False)
            mc_p_values.append(stat_sim)
        except:
            continue
    
    if not mc_p_values:
        logger.error("Monte-Carlo simulation produced no valid statistics for Welch T-Test.")
        return False, {"error": "No MC samples", "test": "welch_t_test"}
    
    # Two-sided p-value estimation
    observed_abs_stat = abs(stat_lib)
    extreme_count = sum(1 for s in mc_p_values if abs(s) >= observed_abs_stat)
    p_mc = extreme_count / NUM_REPLICATES

    diff = abs(p_lib - p_mc)
    is_valid = diff <= TOLERANCE_THRESHOLD

    details = {
        "test": "welch_t_test",
        "p_library": p_lib,
        "p_monte_carlo": p_mc,
        "difference": diff,
        "threshold": TOLERANCE_THRESHOLD,
        "valid": is_valid,
        "replicates": NUM_REPLICATES
    }

    if is_valid:
        logger.info(f"Welch T-Test validation PASSED (diff={diff:.5f})")
    else:
        logger.error(f"Welch T-Test validation FAILED (diff={diff:.5f} > {TOLERANCE_THRESHOLD})")

    return is_valid, details


def validate_binomial_test(rng: np.random.Generator) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Binomial Test against Monte-Carlo simulation.

    Returns:
        Tuple of (is_valid, details_dict)
    """
    logger.info("Running Monte-Carlo validation for Binomial Test")

    # Parameters
    n = 50
    p_true = 0.5
    p_null = 0.5

    # Generate data
    k = rng.binomial(n, p_true)

    # 1. Library P-value (Two-sided)
    try:
        # scipy.stats.binom_test is deprecated, use binomtest
        res = stats.binomtest(k, n, p_null, alternative='two-sided')
        p_lib = res.pvalue
    except Exception as e:
        logger.error(f"Library Binomial Test failed: {e}")
        return False, {"error": str(e), "test": "binomial_test"}

    # 2. Monte-Carlo P-value
    # Simulate under null: Binomial(n, p_null)
    mc_p_values = []
    for _ in range(NUM_REPLICATES):
        k_sim = rng.binomial(n, p_null)
        mc_p_values.append(k_sim)
    
    if not mc_p_values:
        logger.error("Monte-Carlo simulation produced no valid statistics for Binomial Test.")
        return False, {"error": "No MC samples", "test": "binomial_test"}
    
    # Two-sided: count how many simulated k are as or more extreme than observed k.
    # "More extreme" means probability of k_sim under H0 is <= probability of k under H0.
    # Or simpler: distance from mean n*p.
    # scipy's two-sided binomial test sums probabilities of all outcomes with p(x) <= p(k).
    # We will approximate this by counting how many k_sim have P(X=k_sim) <= P(X=k).
    
    # Calculate P(X=k)
    from scipy.stats import binom
    p_k = binom.pmf(k, n, p_null)
    
    extreme_count = 0
    for k_sim in mc_p_values:
        p_sim = binom.pmf(k_sim, n, p_null)
        if p_sim <= p_k:
            extreme_count += 1
    
    p_mc = extreme_count / NUM_REPLICATES

    diff = abs(p_lib - p_mc)
    is_valid = diff <= TOLERANCE_THRESHOLD

    details = {
        "test": "binomial_test",
        "p_library": p_lib,
        "p_monte_carlo": p_mc,
        "difference": diff,
        "threshold": TOLERANCE_THRESHOLD,
        "valid": is_valid,
        "replicates": NUM_REPLICATES
    }

    if is_valid:
        logger.info(f"Binomial Test validation PASSED (diff={diff:.5f})")
    else:
        logger.error(f"Binomial Test validation FAILED (diff={diff:.5f} > {TOLERANCE_THRESHOLD})")

    return is_valid, details


def run_monte_carlo_validation() -> bool:
    """
    Execute the full Monte-Carlo validation suite.

    Returns:
        True if all tests pass, False otherwise.
    """
    logger.info("Starting Monte-Carlo Validation Suite (FR-026)")
    
    # Initialize RNG with fixed seed for reproducibility
    rng = np.random.default_rng(SEED)
    
    results = []
    all_passed = True

    # Run validations
    tests = [
        ("Z-Test", validate_z_test),
        ("Fisher's Exact", validate_fisher_exact),
        ("Welch's T-Test", validate_welch_t_test),
        ("Binomial Test", validate_binomial_test),
    ]

    for name, func in tests:
        try:
            passed, details = func(rng)
            results.append(details)
            if not passed:
                all_passed = False
        except Exception as e:
            logger.exception(f"Validation for {name} raised an exception: {e}")
            all_passed = False
            results.append({
                "test": name,
                "error": str(e),
                "valid": False
            })

    # Log summary
    logger.info(f"Validation Suite Complete. All Passed: {all_passed}")
    for res in results:
        status = "PASS" if res.get("valid") else "FAIL"
        logger.info(f"  - {res['test']}: {status}")

    return all_passed


def main() -> int:
    """
    Entry point for the script.

    Returns:
        0 if validation passes, 1 if any test fails.
    """
    try:
        success = run_monte_carlo_validation()
        if success:
            logger.info("All Monte-Carlo validations passed.")
            return 0
        else:
            logger.error("One or more Monte-Carlo validations failed.")
            return 1
    except Exception as e:
        logger.exception(f"Fatal error in Monte-Carlo validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
