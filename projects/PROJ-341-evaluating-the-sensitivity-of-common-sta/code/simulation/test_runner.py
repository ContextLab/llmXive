import numpy as np
from scipy import stats
from typing import Tuple, List, Dict, Any, Optional, Union
import warnings
import json
import os
from code.simulation.data_generator import generate_normal_data, generate_contingency_table_data
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback
from code.simulation.logging_config import get_logger

def run_t_test(group1: np.ndarray, group2: np.ndarray, alpha: float = 0.05) -> Tuple[float, bool]:
    """
    Run a two-sample t-test.
    
    Args:
        group1: First group of data
        group2: Second group of data
        alpha: Significance level
        
    Returns:
        Tuple of (p-value, is_significant)
    """
    try:
        t_stat, p_value = stats.ttest_ind(group1, group2)
        is_significant = p_value < alpha
        return p_value, is_significant
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error in t-test: {e}")
        return 1.0, False

def run_anova(groups: List[np.ndarray], alpha: float = 0.05) -> Tuple[float, bool]:
    """
    Run a one-way ANOVA test.
    
    Args:
        groups: List of groups of data
        alpha: Significance level
        
    Returns:
        Tuple of (p-value, is_significant)
    """
    try:
        f_stat, p_value = stats.f_oneway(*groups)
        is_significant = p_value < alpha
        return p_value, is_significant
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error in ANOVA: {e}")
        return 1.0, False

def run_chi_squared(table: np.ndarray, alpha: float = 0.05) -> Tuple[float, bool]:
    """
    Run a chi-squared test with fallback logic.
    
    Args:
        table: Contingency table
        alpha: Significance level
        
    Returns:
        Tuple of (p-value, is_significant)
    """
    try:
        p_value, is_significant = run_chi_squared_with_fallback(table, alpha)
        return p_value, is_significant
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error in chi-squared test: {e}")
        return 1.0, False

def run_simulation_condition(
    n: int,
    effect_size: float,
    test_type: str,
    hypothesis: str,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a single simulation condition.
    
    Args:
        n: Sample size per group
        effect_size: Effect size (Cohen's d for t-test, f for ANOVA, etc.)
        test_type: Type of test ('t-test', 'anova', 'chi-squared')
        hypothesis: 'null' or 'alternative'
        alpha: Significance level
        seed: Optional random seed
        
    Returns:
        Dictionary containing results
    """
    logger = get_logger()
    
    # Generate data based on hypothesis and test type
    if hypothesis == 'null':
        # For null hypothesis, no effect
        if test_type == 't-test':
            group1 = generate_normal_data(n, mean=0, std=1, seed=seed)
            group2 = generate_normal_data(n, mean=0, std=1, seed=seed+1 if seed else None)
        elif test_type == 'anova':
            groups = [generate_normal_data(n, mean=0, std=1, seed=seed+i) for i in range(3)]
        elif test_type == 'chi-squared':
            # Equal probabilities for null
            probs = [[0.25, 0.25], [0.25, 0.25]]
            table = generate_contingency_table_data(n * 4, probs, seed=seed)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
    else:
        # For alternative hypothesis, apply effect
        if test_type == 't-test':
            group1 = generate_normal_data(n, mean=0, std=1, seed=seed)
            group2 = generate_normal_data(n, mean=effect_size, std=1, seed=seed+1 if seed else None)
        elif test_type == 'anova':
            # Apply effect to second group
            groups = [
                generate_normal_data(n, mean=0, std=1, seed=seed),
                generate_normal_data(n, mean=effect_size, std=1, seed=seed+1 if seed else None),
                generate_normal_data(n, mean=0, std=1, seed=seed+2 if seed else None)
            ]
        elif test_type == 'chi-squared':
            # Apply effect to probabilities
            base_prob = 0.25
            effect = effect_size / 4
            probs = [
                [base_prob - effect, base_prob + effect],
                [base_prob + effect, base_prob - effect]
            ]
            table = generate_contingency_table_data(n * 4, probs, seed=seed)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
    
    # Run the appropriate test
    if test_type == 't-test':
        p_value, is_significant = run_t_test(group1, group2, alpha)
    elif test_type == 'anova':
        p_value, is_significant = run_anova(groups, alpha)
    elif test_type == 'chi-squared':
        p_value, is_significant = run_chi_squared(table, alpha)
    else:
        raise ValueError(f"Unknown test type: {test_type}")
    
    return {
        'sample_size': n,
        'effect_size': effect_size,
        'test_type': test_type,
        'p_value': p_value,
        'hypothesis_state': hypothesis,
        'is_significant': is_significant
    }

def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate simulation results.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Dictionary containing aggregated statistics
    """
    if not results:
        return {}
        
    df = pd.DataFrame(results)
    
    aggregated = {}
    for (n, effect, test, hyp), group in df.groupby(['sample_size', 'effect_size', 'test_type', 'hypothesis_state']):
        key = f"{n}_{effect}_{test}_{hyp}"
        aggregated[key] = {
            'total_iterations': len(group),
            'significant_count': group['is_significant'].sum(),
            'p_value_mean': group['p_value'].mean(),
            'p_value_std': group['p_value'].std()
        }
        
    return aggregated
