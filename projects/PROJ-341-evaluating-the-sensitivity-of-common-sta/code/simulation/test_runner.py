"""
Test runner module for executing statistical tests on generated data.
Supports t-test, ANOVA, and chi-squared tests with fallback logic.
"""
import numpy as np
from scipy import stats
from typing import Tuple, List, Dict, Any, Optional, Union
import warnings
import json
import os
import pandas as pd

from code.simulation.data_generator import (
    generate_two_sample_data,
    generate_anova_data,
    generate_contingency_table_data
)
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback
from code.simulation.logging_config import get_logger, log_operation
from code.simulation import get_rng
from code.simulation.output_writer import write_p_values_raw

logger = get_logger(__name__)

def run_t_test(
    sample_size: int,
    effect_size: float,
    alpha: float = 0.05,
    hypothesis: str = "null"
) -> Tuple[float, str]:
    """
    Run an independent two-sample t-test.
    
    Args:
        sample_size: Number of samples per group.
        effect_size: Cohen's d effect size (0 for null hypothesis).
        alpha: Significance level.
        hypothesis: "null" or "alt" indicating ground truth.
        
    Returns:
        Tuple of (p_value, warning_message)
    """
    rng = get_rng()
    
    # Small sample warning
    warning = ""
    if sample_size < 30:
        warning = f"Small sample size (n={sample_size}) detected. Normality assumption may be violated."
        logger.log("small_sample_warning", n=sample_size, test="t-test")

    # Generate data
    group1 = generate_two_sample_data(n=sample_size, effect_size=0.0, rng=rng)
    if hypothesis == "alt":
        group2 = generate_two_sample_data(n=sample_size, effect_size=effect_size, rng=rng)
    else:
        group2 = generate_two_sample_data(n=sample_size, effect_size=0.0, rng=rng)

    # Perform t-test
    stat, p_val = stats.ttest_ind(group1, group2)
    
    return float(p_val), warning

def run_anova(
    sample_size: int,
    effect_size: float,
    alpha: float = 0.05,
    hypothesis: str = "null",
    n_groups: int = 3
) -> Tuple[float, str]:
    """
    Run a one-way ANOVA.
    
    Args:
        sample_size: Number of samples per group.
        effect_size: Effect size for alternative hypothesis.
        alpha: Significance level.
        hypothesis: "null" or "alt".
        n_groups: Number of groups to compare.
        
    Returns:
        Tuple of (p_value, warning_message)
    """
    rng = get_rng()
    
    warning = ""
    if sample_size < 30:
        warning = f"Small sample size (n={sample_size}) detected per group. Normality assumption may be violated."
        logger.log("small_sample_warning", n=sample_size, test="anova")

    # Generate data
    groups = []
    for i in range(n_groups):
        if hypothesis == "alt" and i > 0:
            # Apply effect to some groups to create difference
            groups.append(generate_anova_data(n=sample_size, effect_size=effect_size, rng=rng))
        else:
            groups.append(generate_anova_data(n=sample_size, effect_size=0.0, rng=rng))

    # Perform ANOVA
    stat, p_val = stats.f_oneway(*groups)
    
    return float(p_val), warning

def run_chi_squared(
    sample_size: int,
    effect_size: float,
    alpha: float = 0.05,
    hypothesis: str = "null",
    n_rows: int = 2,
    n_cols: int = 2
) -> Tuple[float, str, str]:
    """
    Run a Chi-squared test of independence with fallback logic.
    
    Args:
        sample_size: Total sample size (distributed across cells).
        effect_size: Effect size for alternative hypothesis.
        alpha: Significance level.
        hypothesis: "null" or "alt".
        n_rows: Number of rows in contingency table.
        n_cols: Number of columns in contingency table.
        
    Returns:
        Tuple of (p_value, warning_message, method_used)
    """
    rng = get_rng()
    
    warning = ""
    if sample_size < 30:
        warning = f"Small sample size (n={sample_size}) detected. Expected cell counts may be low."
        logger.log("small_sample_warning", n=sample_size, test="chi-squared")

    # Generate contingency table
    table = generate_contingency_table_data(
        n_total=sample_size,
        n_rows=n_rows,
        n_cols=n_cols,
        effect_size=effect_size if hypothesis == "alt" else 0.0,
        rng=rng
    )

    # Run chi-squared with fallback
    p_val, method_used, log_level = run_chi_squared_with_fallback(table, alpha)
    
    if log_level == "warning":
        warning = f"Low expected cell counts detected. Used {method_used}."
        logger.log("chi_squared_fallback", method=method_used, sample_size=sample_size)

    return float(p_val), warning, method_used

def run_simulation_condition(
    sample_size: int,
    effect_size: float,
    test_type: str,
    hypothesis: str,
    alpha: float = 0.05,
    n_iterations: int = 100
) -> List[Dict[str, Any]]:
    """
    Run a single simulation condition (one n, one effect, one test, one hypothesis)
    for a specified number of iterations.
    
    Args:
        sample_size: Sample size per iteration.
        effect_size: Effect size.
        test_type: "t-test", "anova", or "chi-squared".
        hypothesis: "null" or "alt".
        alpha: Significance level.
        n_iterations: Number of Monte Carlo iterations.
        
    Returns:
        List of result dictionaries.
    """
    results = []
    
    for i in range(n_iterations):
        # Reset RNG for each iteration to ensure independence
        # Note: get_rng() should be stateful, but we need fresh draws per iteration
        # We rely on the global state managed by get_rng()
        
        p_val = 0.0
        warning = ""
        method = "standard"
        
        if test_type == "t-test":
            p_val, warning = run_t_test(sample_size, effect_size, alpha, hypothesis)
        elif test_type == "anova":
            p_val, warning = run_anova(sample_size, effect_size, alpha, hypothesis)
        elif test_type == "chi-squared":
            p_val, warning, method = run_chi_squared(sample_size, effect_size, alpha, hypothesis)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        results.append({
            "sample_size": sample_size,
            "effect_size": effect_size,
            "test_type": test_type,
            "p_value": p_val,
            "hypothesis_state": hypothesis,
            "warning": warning,
            "method_used": method,
            "iteration": i
        })
        
        if i % 1000 == 0 and i > 0:
            logger.log("simulation_progress", test=test_type, n=sample_size, iter=i)

    return results

def aggregate_results(
    all_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate simulation results to calculate error rates.
    
    Args:
        all_results: List of all result dictionaries.
        
    Returns:
        Dictionary with aggregated statistics.
    """
    df = pd.DataFrame(all_results)
    
    # Group by condition
    grouped = df.groupby(["sample_size", "effect_size", "test_type", "hypothesis_state"])
    
    summary = []
    for (n, eff, test, hyp), group in grouped:
        p_vals = group["p_value"].values
        alpha = 0.05 # Default, could be parameterized
        rejections = np.sum(p_vals < alpha)
        total = len(p_vals)
        error_rate = rejections / total if total > 0 else 0.0
        
        summary.append({
            "sample_size": n,
            "effect_size": eff,
            "test_type": test,
            "hypothesis_state": hyp,
            "n_iterations": total,
            "rejections": int(rejections),
            "error_rate": float(error_rate),
            "mean_p_value": float(np.mean(p_vals)),
            "median_p_value": float(np.median(p_vals))
        })
    
    return summary

@log_operation("run_full_simulation_grid")
def main():
    """
    Main entry point to run the full simulation grid and write results.
    Implements the vectorized loop for T016.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run simulation grid")
    parser.add_argument("--min-n", type=int, default=5, help="Minimum sample size")
    parser.add_argument("--max-n", type=int, default=500, help="Maximum sample size")
    parser.add_argument("--step", type=int, default=5, help="Step for sample size")
    parser.add_argument("--iterations", type=int, default=1000, help="Iterations per condition")
    parser.add_argument("--tests", type=str, nargs="+", default=["t-test", "anova", "chi-squared"])
    parser.add_argument("--effects", type=float, nargs="+", default=[0.0, 0.5])
    parser.add_argument("--hypotheses", type=str, nargs="+", default=["null", "alt"])
    parser.add_argument("--output", type=str, default="data/simulation/p_values_raw.csv")
    parser.add_argument("--alpha", type=float, default=0.05)
    
    args = parser.parse_args()
    
    logger.log("simulation_start", args=vars(args))
    
    all_results = []
    
    # Grid search loop
    # To optimize memory, we process in batches or write incrementally if needed.
    # For T016 requirement: "vectorized loop... collect all p-values and write... to_csv"
    # We collect in a list and write once at the end. If memory is an issue, T047 handles streaming.
    
    for n in range(args.min_n, args.max_n + 1, args.step):
        for effect in args.effects:
            for test in args.tests:
                for hyp in args.hypotheses:
                    # Run iterations
                    batch_results = run_simulation_condition(
                        sample_size=n,
                        effect_size=effect,
                        test_type=test,
                        hypothesis=hyp,
                        alpha=args.alpha,
                        n_iterations=args.iterations
                    )
                    all_results.extend(batch_results)
                    
                    logger.log("condition_complete", n=n, effect=effect, test=test, hyp=hyp, count=len(batch_results))
    
    # Write results
    write_p_values_raw(all_results, args.output)
    
    logger.log("simulation_complete", total_rows=len(all_results), output=args.output)
    print(f"Simulation complete. Wrote {len(all_results)} rows to {args.output}")

if __name__ == "__main__":
    main()