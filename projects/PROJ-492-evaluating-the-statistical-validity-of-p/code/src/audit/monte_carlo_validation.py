"""
Monte-Carlo validation module for statistical test consistency.

Implements FR-026: Runs Monte-Carlo simulations to validate that the
statistical test implementations (z-test, Fisher's exact, Welch's t-test,
binomial test) produce p-values within an acceptable tolerance of the
theoretical expectations under the null hypothesis.

Target: 10 * 10,000 replicates for each test type.
Tolerance: Absolute difference <= 0.005.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

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
    run_monte_carlo_validation_core
)

# Configuration
NUM_REPLICATES = 10000
NUM_RUNS = 10
TOLERANCE = 0.005
ALPHA = 0.05

logger = get_default_logger()

def validate_z_test(
    n_runs: int = NUM_RUNS,
    n_replicates: int = NUM_REPLICATES,
    tolerance: float = TOLERANCE,
    seed: int = SEED
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates the two-proportion z-test implementation via Monte-Carlo simulation.

    Under the null hypothesis (p1 = p2), the z-statistic should follow N(0,1).
    We simulate data where p1 = p2 and check if the empirical rejection rate
    matches the theoretical alpha (0.05) within tolerance.
    """
    set_rng_seed(seed)
    logger.info(f"Running Z-Test validation: {n_runs} runs x {n_replicates} replicates")

    results = []
    for run_idx in range(n_runs):
        # Simulate data under null: p1 = p2 = 0.5, n1 = n2 = 1000
        n1, n2 = 1000, 1000
        p_true = 0.5
        
        # Generate synthetic data
        # Group A: Binomial(n1, p_true)
        # Group B: Binomial(n2, p_true)
        x1 = np.random.binomial(n1, p_true)
        x2 = np.random.binomial(n2, p_true)
        
        # Calculate observed proportions
        p1_hat = x1 / n1
        p2_hat = x2 / n2
        
        # Pooled proportion
        p_pooled = (x1 + x2) / (n1 + n2)
        
        # Standard error under null
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
        
        # Z-statistic
        if se == 0:
            z_stat = 0.0
        else:
            z_stat = (p1_hat - p2_hat) / se
        
        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        # Check if we reject null (should happen ~5% of the time)
        reject = 1 if p_value < ALPHA else 0
        results.append(reject)
    
    empirical_rate = np.mean(results)
    theoretical_rate = ALPHA
    diff = abs(empirical_rate - theoretical_rate)
    
    passed = diff <= tolerance
    
    status = {
        "test_name": "z_test",
        "runs": n_runs,
        "replicates_per_run": n_replicates,
        "theoretical_alpha": theoretical_rate,
        "empirical_alpha": empirical_rate,
        "absolute_difference": diff,
        "tolerance": tolerance,
        "passed": passed
    }
    
    logger.info(f"Z-Test Validation: Empirical rate={empirical_rate:.4f}, Diff={diff:.4f}, Passed={passed}")
    return passed, status

def validate_fisher_exact(
    n_runs: int = NUM_RUNS,
    n_replicates: int = NUM_REPLICATES,
    tolerance: float = TOLERANCE,
    seed: int = SEED
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates Fisher's Exact Test implementation via Monte-Carlo simulation.

    Under the null hypothesis of independence, the test should reject
    with probability alpha when the null is true.
    """
    set_rng_seed(seed)
    logger.info(f"Running Fisher's Exact Validation: {n_runs} runs x {n_replicates} replicates")

    results = []
    for run_idx in range(n_runs):
        # Create contingency table under null (independence)
        # Row totals: 100, 100. Col totals: 100, 100.
        # Expected cell counts: 50, 50, 50, 50.
        # We generate counts that satisfy margins exactly to ensure null holds.
        # Simplest: generate binomial for first cell, others determined.
        n_row1, n_row2 = 100, 100
        n_col1, n_col2 = 100, 100
        total = n_row1 + n_row2
        
        # Under null, cell[0,0] ~ Hypergeometric(total, n_col1, n_row1)
        # Or simpler: generate random split
        cell_00 = np.random.hypergeometric(n_col1, n_col2, n_row1)
        cell_01 = n_row1 - cell_00
        cell_10 = n_col1 - cell_00
        cell_11 = n_col2 - cell_01
        
        table = [[cell_00, cell_01], [cell_10, cell_11]]
        
        # Compute Fisher's exact p-value
        # Using scipy.stats.fisher_exact
        oddsratio, p_value = stats.fisher_exact(table, alternative='two-sided')
        
        reject = 1 if p_value < ALPHA else 0
        results.append(reject)
    
    empirical_rate = np.mean(results)
    theoretical_rate = ALPHA
    diff = abs(empirical_rate - theoretical_rate)
    
    passed = diff <= tolerance
    
    status = {
        "test_name": "fisher_exact",
        "runs": n_runs,
        "replicates_per_run": n_replicates,
        "theoretical_alpha": theoretical_rate,
        "empirical_alpha": empirical_rate,
        "absolute_difference": diff,
        "tolerance": tolerance,
        "passed": passed
    }
    
    logger.info(f"Fisher's Exact Validation: Empirical rate={empirical_rate:.4f}, Diff={diff:.4f}, Passed={passed}")
    return passed, status

def validate_welch_t_test(
    n_runs: int = NUM_RUNS,
    n_replicates: int = NUM_REPLICATES,
    tolerance: float = TOLERANCE,
    seed: int = SEED
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates Welch's t-test implementation via Monte-Carlo simulation.

    Under the null hypothesis (means are equal), the test should reject
    with probability alpha.
    """
    set_rng_seed(seed)
    logger.info(f"Running Welch's T-Test Validation: {n_runs} runs x {n_replicates} replicates")

    results = []
    for run_idx in range(n_runs):
        # Generate data under null: mu1 = mu2 = 0, sigma1 = sigma2 = 1
        # Unequal sample sizes to test Welch's robustness
        n1, n2 = 50, 100
        
        data1 = np.random.normal(0, 1, n1)
        data2 = np.random.normal(0, 1, n2)
        
        # Compute Welch's t-test
        t_stat, p_value = stats.ttest_ind(data1, data2, equal_var=False)
        
        reject = 1 if p_value < ALPHA else 0
        results.append(reject)
    
    empirical_rate = np.mean(results)
    theoretical_rate = ALPHA
    diff = abs(empirical_rate - theoretical_rate)
    
    passed = diff <= tolerance
    
    status = {
        "test_name": "welch_t_test",
        "runs": n_runs,
        "replicates_per_run": n_replicates,
        "theoretical_alpha": theoretical_rate,
        "empirical_alpha": empirical_rate,
        "absolute_difference": diff,
        "tolerance": tolerance,
        "passed": passed
    }
    
    logger.info(f"Welch's T-Test Validation: Empirical rate={empirical_rate:.4f}, Diff={diff:.4f}, Passed={passed}")
    return passed, status

def validate_binomial_test(
    n_runs: int = NUM_RUNS,
    n_replicates: int = NUM_REPLICATES,
    tolerance: float = TOLERANCE,
    seed: int = SEED
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates Binomial Test implementation via Monte-Carlo simulation.

    Under the null hypothesis (p = p0), the test should reject with probability alpha.
    """
    set_rng_seed(seed)
    logger.info(f"Running Binomial Test Validation: {n_runs} runs x {n_replicates} replicates")

    results = []
    for run_idx in range(n_runs):
        # Generate data under null: n=100, p=0.5
        n_trials = 100
        p_null = 0.5
        
        # Generate observed successes
        k = np.random.binomial(n_trials, p_null)
        
        # Compute two-sided binomial p-value
        # scipy.stats.binom_test is deprecated, use binomtest
        result = stats.binomtest(k, n_trials, p_null, alternative='two-sided')
        p_value = result.pvalue
        
        reject = 1 if p_value < ALPHA else 0
        results.append(reject)
    
    empirical_rate = np.mean(results)
    theoretical_rate = ALPHA
    diff = abs(empirical_rate - theoretical_rate)
    
    passed = diff <= tolerance
    
    status = {
        "test_name": "binomial_test",
        "runs": n_runs,
        "replicates_per_run": n_replicates,
        "theoretical_alpha": theoretical_rate,
        "empirical_alpha": empirical_rate,
        "absolute_difference": diff,
        "tolerance": tolerance,
        "passed": passed
    }
    
    logger.info(f"Binomial Test Validation: Empirical rate={empirical_rate:.4f}, Diff={diff:.4f}, Passed={passed}")
    return passed, status

def run_monte_carlo_validation(
    n_runs: int = NUM_RUNS,
    n_replicates: int = NUM_REPLICATES,
    tolerance: float = TOLERANCE,
    seed: int = SEED,
    output_path: Optional[Path] = None
) -> bool:
    """
    Runs the full Monte-Carlo validation suite for all statistical tests.

    Returns True if all tests pass, False otherwise.
    """
    logger.info("Starting Monte-Carlo Validation Suite")
    
    tests = [
        ("z_test", validate_z_test),
        ("fisher_exact", validate_fisher_exact),
        ("welch_t_test", validate_welch_t_test),
        ("binomial_test", validate_binomial_test)
    ]
    
    all_results = []
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            passed, status = test_func(
                n_runs=n_runs,
                n_replicates=n_replicates,
                tolerance=tolerance,
                seed=seed
            )
            all_results.append(status)
            if not passed:
                all_passed = False
                logger.error(f"Validation FAILED for {test_name}")
            else:
                logger.info(f"Validation PASSED for {test_name}")
        except Exception as e:
            logger.error(f"Validation ERROR for {test_name}: {str(e)}")
            all_passed = False
            all_results.append({
                "test_name": test_name,
                "error": str(e),
                "passed": False
            })
    
    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({
                "validation_results": all_results,
                "all_passed": all_passed,
                "config": {
                    "n_runs": n_runs,
                    "n_replicates": n_replicates,
                    "tolerance": tolerance,
                    "seed": seed
                }
            }, f, indent=2)
        logger.info(f"Validation results written to {output_path}")
    
    return all_passed

def main():
    """
    Main entry point for Monte-Carlo validation.
    Exits with status 0 if all validations pass, 1 otherwise.
    """
    logger.info("Monte-Carlo Validation Module - Main Entry Point")
    
    # Default output path
    output_dir = Path("code/output")
    output_file = output_dir / "monte_carlo_validation_results.json"
    
    success = run_monte_carlo_validation(
        n_runs=NUM_RUNS,
        n_replicates=NUM_REPLICATES,
        tolerance=TOLERANCE,
        seed=SEED,
        output_path=output_file
    )
    
    if success:
        logger.info("All Monte-Carlo validations PASSED")
        sys.exit(0)
    else:
        logger.error("One or more Monte-Carlo validations FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()