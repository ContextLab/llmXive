"""
Test runner module for executing statistical tests (t-test, ANOVA, chi-squared)
with fallback logic for edge cases and comprehensive logging.
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
    log_fallback_triggered
)
from code.simulation.chi_squared_utils import (
    calculate_expected_counts,
    check_low_expected_counts,
    run_chi_squared_with_fallback
)
from code.simulation import get_rng

def run_t_test(
    group1: np.ndarray,
    group2: np.ndarray,
    alpha: float = 0.05,
    two_tailed: bool = True,
    logger_name: str = 'simulation.test_runner'
) -> Tuple[float, bool, bool]:
    """
    Run an independent samples t-test.
    
    Args:
        group1: Data for group 1
        group2: Data for group 2
        alpha: Significance level
        two_tailed: Whether to perform a two-tailed test
        logger_name: Name for the logger
    
    Returns:
        Tuple of (p_value, rejected, warning_issued)
    """
    log = get_logger(logger_name)
    warning_issued = False
    
    # Check for small sample size
    n1, n2 = len(group1), len(group2)
    if n1 < 30 or n2 < 30:
        log.warning_assumption_violated(
            "Normality assumption",
            f"Sample sizes n1={n1}, n2={n2} are < 30",
            "Results may be unreliable; consider non-parametric tests"
        )
        warning_issued = True
    
    try:
        # Perform Welch's t-test (assumes unequal variances)
        statistic, p_value = stats.ttest_ind(group1, group2, equal_var=False)
        
        if not two_tailed:
            # Convert two-tailed p-value to one-tailed if needed
            # Note: This assumes the direction is known; in practice, 
            # one should check the sign of the statistic
            if statistic > 0:
                p_value = p_value / 2
            else:
                p_value = 1 - p_value / 2
        
        rejected = p_value < alpha
        log_test_result(
            test_type="t-test",
            n=max(n1, n2),
            effect_size=0.0,  # Not calculated here, passed from caller
            p_value=p_value,
            alpha=alpha,
            rejected=rejected,
            fallback_used=False,
            warning_issued=warning_issued,
            logger=log
        )
        return p_value, rejected, warning_issued
        
    except Exception as e:
        log.error_details(
            error_type=type(e).__name__,
            error_message=str(e),
            context={"n1": n1, "n2": n2, "alpha": alpha},
            logger=log
        )
        raise

def run_anova(
    groups: List[np.ndarray],
    alpha: float = 0.05,
    logger_name: str = 'simulation.test_runner'
) -> Tuple[float, bool, bool]:
    """
    Run a one-way ANOVA test.
    
    Args:
        groups: List of arrays, one per group
        alpha: Significance level
        logger_name: Name for the logger
    
    Returns:
        Tuple of (p_value, rejected, warning_issued)
    """
    log = get_logger(logger_name)
    warning_issued = False
    
    # Check for small sample sizes
    min_n = min(len(g) for g in groups)
    if min_n < 30:
        log.warning_assumption_violated(
            "Normality assumption",
            f"Minimum group sample size is {min_n} (< 30)",
            "Results may be unreliable; consider Kruskal-Wallis test"
        )
        warning_issued = True
    
    try:
        statistic, p_value = stats.f_oneway(*groups)
        
        rejected = p_value < alpha
        log_test_result(
            test_type="ANOVA",
            n=min_n,
            effect_size=0.0,
            p_value=p_value,
            alpha=alpha,
            rejected=rejected,
            fallback_used=False,
            warning_issued=warning_issued,
            logger=log
        )
        return p_value, rejected, warning_issued
        
    except Exception as e:
        log.error_details(
            error_type=type(e).__name__,
            error_message=str(e),
            context={"num_groups": len(groups), "min_n": min_n},
            logger=log
        )
        raise

def run_chi_squared(
    contingency_table: np.ndarray,
    alpha: float = 0.05,
    logger_name: str = 'simulation.test_runner'
) -> Tuple[float, bool, bool, bool]:
    """
    Run a chi-squared test of independence with fallback logic.
    
    Args:
        contingency_table: 2D array representing the contingency table
        alpha: Significance level
        logger_name: Name for the logger
    
    Returns:
        Tuple of (p_value, rejected, fallback_used, warning_issued)
    """
    log = get_logger(logger_name)
    warning_issued = False
    fallback_used = False
    
    # Check expected cell counts
    expected_counts, low_cells = check_low_expected_counts(contingency_table)
    
    if low_cells:
        log.warning_assumption_violated(
            "Expected cell count >= 5",
            f"Found {len(low_cells)} cells with expected count < 5: {low_cells}",
            "Using fallback test (Yates' correction or Fisher's Exact)"
        )
        warning_issued = True
    
    # Run with fallback logic
    try:
        p_value, rejected, fallback_used = run_chi_squared_with_fallback(
            contingency_table, alpha
        )
        
        log_test_result(
            test_type="Chi-squared",
            n=int(contingency_table.sum()),
            effect_size=0.0,
            p_value=p_value,
            alpha=alpha,
            rejected=rejected,
            fallback_used=fallback_used,
            warning_issued=warning_issued,
            logger=log
        )
        
        if fallback_used:
            log_fallback_triggered(
                test_type="Chi-squared",
                reason="Low expected cell counts",
                fallback_test="Fisher's Exact" if contingency_table.shape == (2, 2) else "Yates' Correction",
                logger=log
            )
        
        return p_value, rejected, fallback_used, warning_issued
        
    except Exception as e:
        log.error_details(
            error_type=type(e).__name__,
            error_message=str(e),
            context={"table_shape": contingency_table.shape, "alpha": alpha},
            logger=log
        )
        raise

def run_simulation_condition(
    n: int,
    effect_size: float,
    test_type: str,
    hypothesis: str,  # 'null' or 'alternative'
    alpha: float = 0.05,
    seed: Optional[int] = None,
    logger_name: str = 'simulation.test_runner'
) -> Dict[str, Any]:
    """
    Run a single simulation condition (one iteration).
    
    Args:
        n: Sample size
        effect_size: Effect size to simulate
        test_type: Type of test ('t-test', 'anova', 'chi-squared')
        hypothesis: 'null' or 'alternative'
        alpha: Significance level
        seed: Random seed for reproducibility
        logger_name: Name for the logger
    
    Returns:
        Dictionary with p_value, rejected, fallback_used, warning_issued
    """
    log = get_logger(logger_name)
    rng = get_rng(seed)
    
    # Generate data based on test type and hypothesis
    if test_type == 't-test':
        # Two groups
        if hypothesis == 'null':
            # No difference
            group1 = rng.normal(0, 1, n)
            group2 = rng.normal(0, 1, n)
        else:
            # Difference exists
            group1 = rng.normal(0, 1, n)
            group2 = rng.normal(effect_size, 1, n)
        
        p_val, rejected, warning = run_t_test(group1, group2, alpha, logger_name=logger_name)
        return {
            'p_value': p_val,
            'rejected': rejected,
            'fallback_used': False,
            'warning_issued': warning
        }
    
    elif test_type == 'anova':
        # Three groups
        if hypothesis == 'null':
            groups = [rng.normal(0, 1, n) for _ in range(3)]
        else:
            # One group shifted
            groups = [
                rng.normal(0, 1, n),
                rng.normal(0, 1, n),
                rng.normal(effect_size, 1, n)
            ]
        
        p_val, rejected, warning = run_anova(groups, alpha, logger_name=logger_name)
        return {
            'p_value': p_val,
            'rejected': rejected,
            'fallback_used': False,
            'warning_issued': warning
        }
    
    elif test_type == 'chi-squared':
        # Contingency table
        # For null: independent, for alt: dependent
        if hypothesis == 'null':
            # Equal probabilities
            probs = [[0.25, 0.25], [0.25, 0.25]]
        else:
            # Dependent
            probs = [
                [0.15, 0.35],
                [0.35, 0.15]
            ]
        
        # Generate counts based on probabilities and sample size
        total = n
        table = np.zeros((2, 2), dtype=int)
        for i in range(2):
            for j in range(2):
                count = int(total * probs[i][j])
                table[i, j] = count
        
        # Adjust to ensure total matches
        diff = total - table.sum()
        if diff != 0:
            table[0, 0] += diff
        
        p_val, rejected, fallback, warning = run_chi_squared(
            table, alpha, logger_name=logger_name
        )
        return {
            'p_value': p_val,
            'rejected': rejected,
            'fallback_used': fallback,
            'warning_issued': warning
        }
    
    else:
        raise ValueError(f"Unknown test type: {test_type}")

def aggregate_results(
    results: List[Dict[str, Any]],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Aggregate results from multiple iterations.
    
    Args:
        results: List of result dictionaries from run_simulation_condition
        alpha: Significance level
    
    Returns:
        Dictionary with aggregated statistics
    """
    total = len(results)
    if total == 0:
        return {'total': 0, 'rejected_count': 0, 'error_rate': 0.0}
    
    rejected_count = sum(1 for r in results if r['rejected'])
    fallback_count = sum(1 for r in results if r['fallback_used'])
    warning_count = sum(1 for r in results if r['warning_issued'])
    
    return {
        'total': total,
        'rejected_count': rejected_count,
        'fallback_count': fallback_count,
        'warning_count': warning_count,
        'error_rate': rejected_count / total,
        'fallback_rate': fallback_count / total,
        'warning_rate': warning_count / total
    }
