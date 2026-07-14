"""
Statistical test runner for simulation pipeline.
Executes t-tests, ANOVA, and chi-squared tests with fallback logic
and comprehensive logging.
"""
import numpy as np
from scipy import stats
from typing import Tuple, List, Dict, Any, Optional, Union
import warnings
import json
import os

# Import logging utilities
from code.simulation.logging_config import (
    get_logger, 
    log_test_result, 
    log_warning_assumption_violated,
    log_fallback_triggered,
    log_seed_usage
)
from code.simulation.data_generator import generate_normal_data, generate_multinomial_data
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback
from code.simulation import get_rng

logger = get_logger("simulation.test_runner")

def run_t_test(group1: np.ndarray, group2: np.ndarray, 
               alpha: float = 0.05, equal_var: bool = True) -> Dict[str, Any]:
    """
    Run independent samples t-test with logging.
    
    Args:
        group1: First group data
        group2: Second group data
        alpha: Significance level
        equal_var: Whether to assume equal variance
    
    Returns:
        Dictionary with p-value, statistic, and metadata
    """
    seed = int(np.random.randint(0, 2**31))
    log_seed_usage(seed, "t-test execution")
    
    # Check assumptions
    if len(group1) < 30 or len(group2) < 30:
        log_warning_assumption_violated("t-test", "normality assumption", 
                                        min(len(group1), len(group2)))
    
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=equal_var)
            
            if w:
                for warning in w:
                    log_warning_assumption_violated("t-test", str(warning.message), 
                                                    min(len(group1), len(group2)))
    except Exception as e:
        logger.error(f"t-test failed: {e}")
        raise
    
    log_test_result("t-test", len(group1) + len(group2), 0.0, p_value, 
                   "unknown", seed)
    
    return {
        "test": "t-test",
        "p_value": p_value,
        "statistic": t_stat,
        "alpha": alpha,
        "significant": p_value < alpha,
        "n_total": len(group1) + len(group2)
    }

def run_anova(groups: List[np.ndarray], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run one-way ANOVA with logging.
    
    Args:
        groups: List of group arrays
        alpha: Significance level
    
    Returns:
        Dictionary with p-value, statistic, and metadata
    """
    seed = int(np.random.randint(0, 2**31))
    log_seed_usage(seed, "ANOVA execution")
    
    # Check assumptions
    min_n = min(len(g) for g in groups)
    if min_n < 30:
        log_warning_assumption_violated("ANOVA", "normality assumption", min_n)
    
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            f_stat, p_value = stats.f_oneway(*groups)
            
            if w:
                for warning in w:
                    log_warning_assumption_assumption_violated("ANOVA", str(warning.message), min_n)
    except Exception as e:
        logger.error(f"ANOVA failed: {e}")
        raise
    
    log_test_result("ANOVA", sum(len(g) for g in groups), 0.0, p_value, 
                   "unknown", seed)
    
    return {
        "test": "ANOVA",
        "p_value": p_value,
        "statistic": f_stat,
        "alpha": alpha,
        "significant": p_value < alpha,
        "n_total": sum(len(g) for g in groups),
        "n_groups": len(groups)
    }

def run_chi_squared(observed: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run chi-squared test with fallback logic and logging.
    
    Args:
        observed: Observed contingency table
        alpha: Significance level
    
    Returns:
        Dictionary with p-value, statistic, metadata, and fallback info
    """
    seed = int(np.random.randint(0, 2**31))
    log_seed_usage(seed, "chi-squared execution")
    
    # Use the utility function that handles fallbacks
    result = run_chi_squared_with_fallback(observed, alpha)
    
    log_test_result(
        result.get("test_name", "chi-squared"),
        int(result.get("n_total", 0)),
        0.0,
        result["p_value"],
        "unknown",
        seed,
        fallback_triggered=result.get("fallback_triggered", False)
    )
    
    if result.get("fallback_triggered"):
        log_fallback_triggered(
            "chi-squared",
            result.get("fallback_method", "unknown"),
            result.get("fallback_reason", "unknown")
        )
    
    return result

def run_simulation_condition(n: int, effect_size: float, test_type: str,
                             hypothesis: str, alpha: float = 0.05,
                             iterations: int = 1000) -> Dict[str, Any]:
    """
    Run a complete simulation condition with logging.
    
    Args:
        n: Sample size per group
        effect_size: Effect size parameter
        test_type: Type of test ('t-test', 'ANOVA', 'chi-squared')
        hypothesis: 'null' or 'alternative'
        alpha: Significance level
        iterations: Number of simulation iterations
    
    Returns:
        Aggregated results dictionary
    """
    logger.info(f"Starting simulation: n={n}, effect={effect_size}, "
               f"test={test_type}, H={hypothesis}, alpha={alpha}, "
               f"iterations={iterations}")
    
    p_values = []
    fallback_count = 0
    assumption_warnings = 0
    
    for i in range(iterations):
        log_iteration_status(i + 1, iterations, {
            "n": n,
            "effect_size": effect_size,
            "test_type": test_type,
            "hypothesis": hypothesis
        })
        
        try:
            # Generate data based on hypothesis
            if hypothesis == "null":
                # No effect - groups have same distribution
                if test_type == "t-test":
                    group1 = generate_normal_data(n, mean=0, std=1)
                    group2 = generate_normal_data(n, mean=0, std=1)
                    result = run_t_test(group1, group2, alpha)
                elif test_type == "ANOVA":
                    groups = [generate_normal_data(n, mean=0, std=1) for _ in range(3)]
                    result = run_anova(groups, alpha)
                elif test_type == "chi-squared":
                    # Create contingency table with equal expected counts
                    observed = np.random.multinomial(n * 4, [0.25, 0.25, 0.25, 0.25]).reshape(2, 2)
                    result = run_chi_squared(observed, alpha)
                else:
                    raise ValueError(f"Unknown test type: {test_type}")
            
            else:  # alternative hypothesis
                if test_type == "t-test":
                    group1 = generate_normal_data(n, mean=0, std=1)
                    group2 = generate_normal_data(n, mean=effect_size, std=1)
                    result = run_t_test(group1, group2, alpha)
                elif test_type == "ANOVA":
                    groups = [
                        generate_normal_data(n, mean=0, std=1),
                        generate_normal_data(n, mean=effect_size, std=1),
                        generate_normal_data(n, mean=effect_size * 2, std=1)
                    ]
                    result = run_anova(groups, alpha)
                elif test_type == "chi-squared":
                    # Create contingency table with different probabilities
                    probs = [0.1, 0.2, 0.3, 0.4]
                    observed = np.random.multinomial(n * 4, probs).reshape(2, 2)
                    result = run_chi_squared(observed, alpha)
                else:
                    raise ValueError(f"Unknown test type: {test_type}")
            
            p_values.append(result["p_value"])
            
            if result.get("fallback_triggered"):
                fallback_count += 1
            
            # Count assumption warnings (simplified)
            if result.get("assumption_violated"):
                assumption_warnings += 1
        
        except Exception as e:
            logger.error(f"Iteration {i+1} failed: {e}")
            # Skip this iteration but continue
            continue
    
    # Calculate results
    p_values = np.array(p_values)
    type1_error_rate = np.mean(p_values < alpha) if hypothesis == "null" else None
    type2_error_rate = np.mean(p_values >= alpha) if hypothesis == "alternative" else None
    power = 1 - type2_error_rate if hypothesis == "alternative" else None
    
    result_summary = {
        "n": n,
        "effect_size": effect_size,
        "test_type": test_type,
        "hypothesis": hypothesis,
        "alpha": alpha,
        "iterations_run": len(p_values),
        "iterations_total": iterations,
        "p_values": p_values.tolist(),
        "type1_error_rate": type1_error_rate,
        "type2_error_rate": type2_error_rate,
        "power": power,
        "fallback_count": fallback_count,
        "assumption_warnings": assumption_warnings,
        "mean_p_value": float(np.mean(p_values)),
        "std_p_value": float(np.std(p_values))
    }
    
    logger.info(f"Simulation complete: {result_summary['iterations_run']}/{iterations} "
               f"iterations successful")
    
    return result_summary

def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate results from multiple simulation runs.
    
    Args:
        results: List of result dictionaries
    
    Returns:
        Aggregated summary statistics
    """
    logger.info(f"Aggregating {len(results)} simulation results")
    
    if not results:
        return {}
    
    aggregated = {
        "total_runs": len(results),
        "by_test_type": {},
        "by_hypothesis": {},
        "overall_stats": {}
    }
    
    for result in results:
        test_type = result.get("test_type", "unknown")
        hypothesis = result.get("hypothesis", "unknown")
        
        # Aggregate by test type
        if test_type not in aggregated["by_test_type"]:
            aggregated["by_test_type"][test_type] = []
        aggregated["by_test_type"][test_type].append(result)
        
        # Aggregate by hypothesis
        if hypothesis not in aggregated["by_hypothesis"]:
            aggregated["by_hypothesis"][hypothesis] = []
        aggregated["by_hypothesis"][hypothesis].append(result)
    
    # Calculate overall statistics
    all_p_values = []
    for result in results:
        if "p_values" in result:
            all_p_values.extend(result["p_values"])
    
    if all_p_values:
        aggregated["overall_stats"] = {
            "total_p_values": len(all_p_values),
            "mean_p_value": float(np.mean(all_p_values)),
            "std_p_value": float(np.std(all_p_values)),
            "min_p_value": float(np.min(all_p_values)),
            "max_p_value": float(np.max(all_p_values))
        }
    
    logger.info(f"Aggregation complete: {aggregated['overall_stats']}")
    return aggregated
