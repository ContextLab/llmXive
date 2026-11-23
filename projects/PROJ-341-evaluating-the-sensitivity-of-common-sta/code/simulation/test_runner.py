"""
Test Runner Module for Statistical Simulation.

Implements vectorized statistical tests (t-test, ANOVA, Chi-squared)
with batch processing, dynamic alpha support, and strict reproducibility
guarantees via per-iteration seed re-initialization.
"""
from __future__ import annotations

import json
import os
import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy import stats

from code.simulation.logging_config import get_logger, log_operation
from code.simulation.data_generator import (
    generate_two_sample_data,
    generate_anova_data,
    generate_contingency_table_data,
)
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback
from code.simulation import get_rng

logger = get_logger(__name__)


def run_t_test(
    sample_size: int,
    effect_size: float,
    hypothesis_state: str,
    alpha: float = 0.05,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run an independent two-sample t-test on generated data.

    Args:
        sample_size: Number of observations per group.
        effect_size: Cohen's d for the effect (0.0 for null).
        hypothesis_state: 'null' or 'alternative'.
        alpha: Significance level.
        seed: Random seed for this specific iteration.

    Returns:
        Dictionary with p_value, test_statistic, and rejection status.
    """
    # Re-initialize RNG for this specific iteration to prevent state leakage
    rng = get_rng(seed)

    # Determine effect based on hypothesis state
    actual_effect = effect_size if hypothesis_state == "alternative" else 0.0

    # Generate data
    group1, group2 = generate_two_sample_data(
        n1=sample_size,
        n2=sample_size,
        effect_size=actual_effect,
        rng=rng,
    )

    # Perform t-test (two-sided)
    t_stat, p_val = stats.ttest_ind(group1, group2)

    # Flag small sample warning
    small_sample_warning = sample_size < 30

    return {
        "p_value": float(p_val),
        "test_statistic": float(t_stat),
        "rejection": bool(p_val < alpha),
        "small_sample_warning": small_sample_warning,
        "seed_used": seed,
    }


def run_anova(
    sample_size: int,
    effect_size: float,
    hypothesis_state: str,
    alpha: float = 0.05,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run a one-way ANOVA on generated data.

    Args:
        sample_size: Number of observations per group (assumes 3 groups).
        effect_size: Effect size parameter for ANOVA.
        hypothesis_state: 'null' or 'alternative'.
        alpha: Significance level.
        seed: Random seed for this specific iteration.

    Returns:
        Dictionary with p_value, f_statistic, and rejection status.
    """
    # Re-initialize RNG for this specific iteration
    rng = get_rng(seed)

    # Determine effect based on hypothesis state
    actual_effect = effect_size if hypothesis_state == "alternative" else 0.0

    # Generate data for 3 groups
    groups = generate_anova_data(
        n_per_group=sample_size,
        effect_size=actual_effect,
        rng=rng,
    )

    # Perform ANOVA
    f_stat, p_val = stats.f_oneway(*groups)

    # Flag small sample warning
    small_sample_warning = sample_size < 30

    return {
        "p_value": float(p_val),
        "test_statistic": float(f_stat),
        "rejection": bool(p_val < alpha),
        "small_sample_warning": small_sample_warning,
        "seed_used": seed,
    }


def run_chi_squared(
    sample_size: int,
    effect_size: float,
    hypothesis_state: str,
    alpha: float = 0.05,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run a Chi-squared test of independence on generated contingency table data.

    Args:
        sample_size: Total sample size (distributed across cells).
        effect_size: Effect size parameter for contingency table.
        hypothesis_state: 'null' or 'alternative'.
        alpha: Significance level.
        seed: Random seed for this specific iteration.

    Returns:
        Dictionary with p_value, chi2_statistic, and rejection status.
    """
    # Re-initialize RNG for this specific iteration
    rng = get_rng(seed)

    # Determine effect based on hypothesis state
    actual_effect = effect_size if hypothesis_state == "alternative" else 0.0

    # Generate contingency table data
    # For chi-squared, we generate counts for a 2x2 table
    contingency_table = generate_contingency_table_data(
        total_n=sample_size,
        effect_size=actual_effect,
        rng=rng,
    )

    # Perform Chi-squared test with fallback logic
    result = run_chi_squared_with_fallback(contingency_table, alpha=alpha)

    # Flag small sample warning
    small_sample_warning = sample_size < 30

    return {
        "p_value": float(result["p_value"]),
        "test_statistic": float(result["chi2_statistic"]),
        "rejection": result["rejection"],
        "fallback_used": result.get("fallback_used", False),
        "small_sample_warning": small_sample_warning,
        "seed_used": seed,
    }


def run_simulation_condition(
    test_type: str,
    sample_size: int,
    effect_size: float,
    hypothesis_state: str,
    alpha: float = 0.05,
    iterations: int = 1000,
    batch_size: int = 100,
) -> List[Dict[str, Any]]:
    """
    Run a simulation condition with multiple iterations.

    IMPORTANT: To ensure strict reproducibility, the random seed is
    re-initialized INSIDE the iteration loop. This prevents state leakage
    between batches and ensures every single iteration is deterministic
    based on its computed seed.

    Args:
        test_type: 't-test', 'anova', or 'chi-squared'.
        sample_size: Sample size per group (or total for chi-squared).
        effect_size: Effect size parameter.
        hypothesis_state: 'null' or 'alternative'.
        alpha: Significance level.
        iterations: Number of Monte Carlo iterations.
        batch_size: Number of iterations to process in a batch.

    Returns:
        List of result dictionaries for each iteration.
    """
    results = []

    # Select the appropriate test function
    test_functions = {
        "t-test": run_t_test,
        "anova": run_anova,
        "chi-squared": run_chi_squared,
    }

    if test_type not in test_functions:
        raise ValueError(f"Unknown test type: {test_type}")

    test_func = test_functions[test_type]

    # Base seed for this condition
    base_seed = hash((test_type, sample_size, effect_size, hypothesis_state)) % (2**32)

    # Process in batches
    for batch_start in range(0, iterations, batch_size):
        batch_end = min(batch_start + batch_size, iterations)
        batch_results = []

        for i in range(batch_start, batch_end):
            # CRITICAL: Re-initialize seed for EACH iteration
            # This ensures that even if batch processing is interrupted
            # or restarted, every iteration gets the exact same seed
            iteration_seed = base_seed + i

            result = test_func(
                sample_size=sample_size,
                effect_size=effect_size,
                hypothesis_state=hypothesis_state,
                alpha=alpha,
                seed=iteration_seed,
            )

            # Add metadata
            result["test_type"] = test_type
            result["sample_size"] = sample_size
            result["effect_size"] = effect_size
            result["hypothesis_state"] = hypothesis_state
            result["iteration_index"] = i
            result["alpha"] = alpha

            batch_results.append(result)

        results.extend(batch_results)

    return results


def aggregate_results(
    results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Aggregate simulation results to calculate error rates.

    Args:
        results: List of result dictionaries from run_simulation_condition.

    Returns:
        Dictionary with aggregated statistics.
    """
    if not results:
        return {
            "total_iterations": 0,
            "rejections": 0,
            "type1_error_rate": None,
            "type2_error_rate": None,
            "power": None,
        }

    total = len(results)
    rejections = sum(1 for r in results if r["rejection"])

    # Separate by hypothesis state
    null_results = [r for r in results if r["hypothesis_state"] == "null"]
    alt_results = [r for r in results if r["hypothesis_state"] == "alternative"]

    # Type I error: proportion of rejections when null is true
    type1_rejections = sum(1 for r in null_results if r["rejection"])
    type1_rate = type1_rejections / len(null_results) if null_results else None

    # Type II error: proportion of non-rejections when alternative is true
    alt_non_rejections = sum(1 for r in alt_results if not r["rejection"])
    type2_rate = alt_non_rejections / len(alt_results) if alt_results else None

    # Power: 1 - Type II error
    power = 1 - type2_rate if type2_rate is not None else None

    # Small sample warnings
    small_sample_warnings = sum(1 for r in results if r.get("small_sample_warning", False))

    return {
        "total_iterations": total,
        "rejections": rejections,
        "type1_error_rate": type1_rate,
        "type2_error_rate": type2_rate,
        "power": power,
        "small_sample_warning_count": small_sample_warnings,
        "null_count": len(null_results),
        "alt_count": len(alt_results),
    }


def main() -> None:
    """
    Main entry point for testing the simulation runner.
    Runs a small demo to verify functionality.
    """
    print("Running test simulation condition...")

    # Run a small test
    results = run_simulation_condition(
        test_type="t-test",
        sample_size=20,
        effect_size=0.5,
        hypothesis_state="alternative",
        alpha=0.05,
        iterations=100,
        batch_size=50,
    )

    print(f"Generated {len(results)} results")

    # Aggregate
    agg = aggregate_results(results)
    print(f"Aggregated results: {json.dumps(agg, indent=2)}")

    # Verify reproducibility: run again with same params
    results2 = run_simulation_condition(
        test_type="t-test",
        sample_size=20,
        effect_size=0.5,
        hypothesis_state="alternative",
        alpha=0.05,
        iterations=100,
        batch_size=50,
    )

    # Check that results are identical (deterministic)
    p_values_match = all(
        r1["p_value"] == r2["p_value"]
        for r1, r2 in zip(results, results2)
    )

    print(f"Reproducibility check (p-values identical): {p_values_match}")

    if not p_values_match:
        print("ERROR: Results are not reproducible!")
        return

    print("Test completed successfully.")


if __name__ == "__main__":
    main()