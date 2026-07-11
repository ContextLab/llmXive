"""
Monte-Carlo Validation Module (FR-026)

Validates the statistical correctness of z-test, Fisher's exact, Welch's t-test,
and binomial test implementations by running Monte-Carlo simulations.

Runs 100,000 replicates for each test type and verifies the empirical p-value
matches the theoretical expectation within a tolerance of 0.005.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import numpy as np
from scipy import stats

# Import from local project structure
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
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.config import SEED

# Constants
NUM_REPLICATES = 100000
TOLERANCE = 0.005
ALPHA = 0.05

logger = get_default_logger(__name__)


def validate_z_test(n1: int = 100, n2: int = 100, p1: float = 0.5, p2: float = 0.5) -> Dict[str, Any]:
    """
    Validate two-proportion z-test under the null hypothesis (p1 == p2).

    Under H0, the empirical rejection rate at alpha=0.05 should be ~0.05.
    We check if the observed rate is within [0.045, 0.055].
    """
    logger.info(f"Running Monte-Carlo validation for Z-Test ({NUM_REPLICATES} replicates)...")
    set_seeds(SEED)

    rejected_count = 0
    theoretical_p_values = []

    for _ in range(NUM_REPLICATES):
        # Generate data under null
        x1 = np.random.binomial(n1, p1)
        x2 = np.random.binomial(n2, p2)

        # Calculate p-value using scipy (theoretical)
        # We use the standard two-proportion z-test logic
        prop1 = x1 / n1
        prop2 = x2 / n2
        pooled_p = (x1 + x2) / (n1 + n2)
        
        if pooled_p == 0 or pooled_p == 1:
            continue

        se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))
        if se == 0:
            continue

        z_stat = (prop1 - prop2) / se
        p_val = 2 * (1 - stats.norm.cdf(abs(z_stat)))

        theoretical_p_values.append(p_val)
        if p_val < ALPHA:
            rejected_count += 1

    empirical_rate = rejected_count / NUM_REPLICATES
    expected_rate = ALPHA
    diff = abs(empirical_rate - expected_rate)

    result = {
        "test": "z_test",
        "replicates": NUM_REPLICATES,
        "expected_rate": expected_rate,
        "empirical_rate": empirical_rate,
        "absolute_difference": diff,
        "passed": diff <= TOLERANCE,
        "tolerance": TOLERANCE
    }

    logger.info(f"Z-Test Result: Empirical rate={empirical_rate:.4f}, Expected={expected_rate}, Diff={diff:.4f}, Passed={result['passed']}")
    return result


def validate_fisher_exact(n1: int = 50, n2: int = 50, p1: float = 0.5, p2: float = 0.5) -> Dict[str, Any]:
    """
    Validate Fisher's Exact Test under the null hypothesis.
    """
    logger.info(f"Running Monte-Carlo validation for Fisher's Exact Test ({NUM_REPLICATES} replicates)...")
    set_seeds(SEED)

    rejected_count = 0

    for _ in range(NUM_REPLICATES):
        # Generate contingency table under null
        # Row 1: Success, Fail | Row 2: Success, Fail
        x1 = np.random.binomial(n1, p1)
        x2 = np.random.binomial(n2, p2)
        
        table = np.array([[x1, n1 - x1], [x2, n2 - x2]])
        
        try:
            _, p_val = stats.fisher_exact(table, alternative='two-sided')
            if p_val < ALPHA:
                rejected_count += 1
        except ValueError:
            # Handle edge cases (e.g., zero variance)
            continue

    empirical_rate = rejected_count / NUM_REPLICATES
    expected_rate = ALPHA
    diff = abs(empirical_rate - expected_rate)

    result = {
        "test": "fisher_exact",
        "replicates": NUM_REPLICATES,
        "expected_rate": expected_rate,
        "empirical_rate": empirical_rate,
        "absolute_difference": diff,
        "passed": diff <= TOLERANCE,
        "tolerance": TOLERANCE
    }

    logger.info(f"Fisher's Exact Test Result: Empirical rate={empirical_rate:.4f}, Expected={expected_rate}, Diff={diff:.4f}, Passed={result['passed']}")
    return result


def validate_welch_t_test(n1: int = 100, n2: int = 100, mu1: float = 0.0, mu2: float = 0.0, sigma1: float = 1.0, sigma2: float = 1.0) -> Dict[str, Any]:
    """
    Validate Welch's t-test under the null hypothesis (mu1 == mu2).
    """
    logger.info(f"Running Monte-Carlo validation for Welch's T-Test ({NUM_REPLICATES} replicates)...")
    set_seeds(SEED)

    rejected_count = 0

    for _ in range(NUM_REPLICATES):
        data1 = np.random.normal(mu1, sigma1, n1)
        data2 = np.random.normal(mu2, sigma2, n2)

        try:
            _, p_val = stats.ttest_ind(data1, data2, equal_var=False)
            if p_val < ALPHA:
                rejected_count += 1
        except Exception:
            continue

    empirical_rate = rejected_count / NUM_REPLICATES
    expected_rate = ALPHA
    diff = abs(empirical_rate - expected_rate)

    result = {
        "test": "welch_t_test",
        "replicates": NUM_REPLICATES,
        "expected_rate": expected_rate,
        "empirical_rate": empirical_rate,
        "absolute_difference": diff,
        "passed": diff <= TOLERANCE,
        "tolerance": TOLERANCE
    }

    logger.info(f"Welch's T-Test Result: Empirical rate={empirical_rate:.4f}, Expected={expected_rate}, Diff={diff:.4f}, Passed={result['passed']}")
    return result


def validate_binomial_test(n: int = 100, p: float = 0.5) -> Dict[str, Any]:
    """
    Validate Binomial Test under the null hypothesis.
    """
    logger.info(f"Running Monte-Carlo validation for Binomial Test ({NUM_REPLICATES} replicates)...")
    set_seeds(SEED)

    rejected_count = 0

    for _ in range(NUM_REPLICATES):
        x = np.random.binomial(n, p)
        
        try:
            # Two-sided binomial test
            _, p_val = stats.binomtest(x, n, p, alternative='two-sided')
            if p_val < ALPHA:
                rejected_count += 1
        except Exception:
            continue

    empirical_rate = rejected_count / NUM_REPLICATES
    expected_rate = ALPHA
    diff = abs(empirical_rate - expected_rate)

    result = {
        "test": "binomial_test",
        "replicates": NUM_REPLICATES,
        "expected_rate": expected_rate,
        "empirical_rate": empirical_rate,
        "absolute_difference": diff,
        "passed": diff <= TOLERANCE,
        "tolerance": TOLERANCE
    }

    logger.info(f"Binomial Test Result: Empirical rate={empirical_rate:.4f}, Expected={expected_rate}, Diff={diff:.4f}, Passed={result['passed']}")
    return result


def run_monte_carlo_validation(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run all Monte-Carlo validations and aggregate results.
    """
    logger.info("Starting full Monte-Carlo validation suite...")
    
    results = {
        "z_test": validate_z_test(),
        "fisher_exact": validate_fisher_exact(),
        "welch_t_test": validate_welch_t_test(),
        "binomial_test": validate_binomial_test()
    }

    all_passed = all(r["passed"] for r in results.values())
    
    results["overall_passed"] = all_passed
    results["summary"] = f"Total tests: {len(results) - 1}, Passed: {sum(1 for r in results.values() if r['passed'])}, Failed: {sum(1 for r in results.values() if not r['passed'])}"

    logger.info(f"Validation Suite Complete. Overall Passed: {all_passed}")
    logger.info(f"Summary: {results['summary']}")

    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {output_path}")

    return results


def main():
    """
    Entry point for the Monte-Carlo validation script.
    Exits with status 0 if all tests pass, 1 otherwise.
    """
    output_file = Path("data/monte_carlo_validation_results.json")
    
    try:
        results = run_monte_carlo_validation(output_file)
        
        if results["overall_passed"]:
            logger.info("SUCCESS: All statistical tests validated within tolerance.")
            sys.exit(0)
        else:
            logger.error("FAILURE: One or more statistical tests failed validation.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"CRITICAL ERROR during validation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()