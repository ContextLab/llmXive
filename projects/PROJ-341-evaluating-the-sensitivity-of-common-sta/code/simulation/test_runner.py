import numpy as np
from scipy import stats
from typing import Tuple, List, Dict, Any, Optional, Union
import warnings
import json
import os
from code.simulation.data_generator import generate_normal_data, generate_contingency_table_data
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback

def run_t_test(data1: np.ndarray, data2: np.ndarray, alpha: float = 0.05) -> Tuple[float, str]:
    """Run independent t-test."""
    if len(data1) < 2 or len(data2) < 2:
        return np.nan, "insufficient_data"
    stat, p_val = stats.ttest_ind(data1, data2)
    return p_val, "reject" if p_val < alpha else "fail_to_reject"

def run_anova(groups: List[np.ndarray], alpha: float = 0.05) -> Tuple[float, str]:
    """Run one-way ANOVA."""
    if any(len(g) < 2 for g in groups):
        return np.nan, "insufficient_data"
    stat, p_val = stats.f_oneway(*groups)
    return p_val, "reject" if p_val < alpha else "fail_to_reject"

def run_chi_squared(table: np.ndarray, alpha: float = 0.05) -> Tuple[float, str]:
    """Run chi-squared test with fallback logic."""
    return run_chi_squared_with_fallback(table, alpha)

def run_simulation_condition(test_type: str, n: int, effect_size: float, alpha: float, iterations: int) -> List[float]:
    """Run a full simulation condition and return list of p-values."""
    p_values = []
    
    for _ in range(iterations):
        if test_type == 't-test':
            # Generate normal data with known effect size
            # H0: effect_size=0, H1: effect_size>0
            mean1 = 0
            mean2 = effect_size
            data1 = generate_normal_data(n, mean=mean1, std=1)
            data2 = generate_normal_data(n, mean=mean2, std=1)
            p_val, _ = run_t_test(data1, data2, alpha)
            if not np.isnan(p_val):
                p_values.append(p_val)
        
        elif test_type == 'anova':
            # Generate 3 groups
            means = [0, effect_size, effect_size * 1.5] if effect_size > 0 else [0, 0, 0]
            groups = [generate_normal_data(n, mean=m, std=1) for m in means]
            p_val, _ = run_anova(groups, alpha)
            if not np.isnan(p_val):
                p_values.append(p_val)
        
        elif test_type == 'chi-squared':
            # Generate contingency table
            # Simple 2x2 table logic
            # If effect_size=0, independent. If >0, dependent.
            # Mocking a simple generation logic for demonstration
            obs = generate_contingency_table_data(n, effect_size)
            p_val, _ = run_chi_squared(obs, alpha)
            if not np.isnan(p_val):
                p_values.append(p_val)
    
    return p_values

def aggregate_results(p_values: List[float], alpha: float) -> Dict[str, float]:
    """Aggregate p-values into error rates."""
    if not p_values:
        return {'rate': 0.0, 'count': 0}
    return {
        'rate': sum(1 for p in p_values if p < alpha) / len(p_values),
        'count': len(p_values)
    }

if __name__ == '__main__':
    print("Test Runner Module")
