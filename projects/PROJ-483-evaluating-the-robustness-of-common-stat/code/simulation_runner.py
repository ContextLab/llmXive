"""
Simulation runner implementing the Monte Carlo loop for statistical tests.
Includes edge case handling for non-constructible null hypotheses and severe normality violations.
"""
import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional

from dependency_injector import ar1_inject

class EdgeCaseError(Exception):
    """Custom exception for edge cases that prevent valid simulation."""
    pass

def _check_normality_violation(data: np.ndarray, alpha: float = 0.01) -> bool:
    """
    Check if data violates normality assumptions severely (Shapiro-Wilk test).
    Returns True if normality is violated (p < alpha).
    """
    # Flatten data for univariate check or check each column
    if data.ndim > 1:
        # Check each group/column
        for col in range(data.shape[1] if data.ndim == 2 else 1):
            sample = data[:, col] if data.ndim == 2 else data
            if len(sample) > 3 and len(sample) <= 5000:
                _, p_val = stats.shapiro(sample)
                if p_val < alpha:
                    return True
            elif len(sample) > 5000:
                # For large samples, use Kolmogorov-Smirnov against normal
                _, p_val = stats.kstest(sample, 'norm')
                if p_val < alpha:
                    return True
    else:
        if len(data) > 3 and len(data) <= 5000:
            _, p_val = stats.shapiro(data)
            if p_val < alpha:
                return True
        elif len(data) > 5000:
            _, p_val = stats.kstest(data, 'norm')
            if p_val < alpha:
                return True
    return False

def _check_null_construction_validity(data: np.ndarray, correlation_threshold: float = 0.95) -> bool:
    """
    Check if the null hypothesis can be cleanly constructed.
    Returns False if variables are too highly correlated (multicollinearity).
    """
    if data.ndim < 2 or data.shape[1] < 2:
        return True # Single variable, no multicollinearity issue

    # Calculate correlation matrix
    corr_matrix = np.corrcoef(data, rowvar=False)
    
    # Check for near-perfect correlations (excluding self-correlation)
    np.fill_diagonal(corr_matrix, np.nan)
    max_corr = np.nanmax(np.abs(corr_matrix))
    
    return max_corr < correlation_threshold

def run_single_replication(dataset: pd.DataFrame, r: float, test_type: str, config: Dict[str, Any]) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
    """
    Run a single replication of the simulation with edge case handling.
    
    Algorithm:
    1. Generate synthetic data under true null (Normal(0,1)) or use real data.
    2. Check for edge cases before injection:
       - Null hypothesis constructability (multicollinearity)
       - Severe normality violations
    3. Inject dependency structure (AR(1)) with strength r.
    4. Apply statistical test.
    5. Record p-value and edge case metadata.
    
    Returns:
        Tuple of (p_value, edge_case_info)
        p_value is None if edge case prevented execution.
        edge_case_info is a dict describing the failure, or None if successful.
    """
    seed = config.get('random_seed', 42)
    np.random.seed(seed)
    
    n_samples = config.get('n_samples', 100)
    n_groups = 2 # For t-test
    
    # Generate data under true null: N(0, 1)
    data = np.random.normal(loc=0.0, scale=1.0, size=(n_groups, n_samples))
    
    # Edge Case 1: Check if null hypothesis can be cleanly constructed
    # (e.g., if we were using real data that is already highly correlated)
    if not _check_null_construction_validity(data):
        edge_case_info = {
            "type": "null_construction_failure",
            "reason": "Variables are highly correlated, preventing clean null hypothesis construction.",
            "max_correlation": float(np.corrcoef(data, rowvar=False)[0, 1])
        }
        return None, edge_case_info
    
    # Inject dependency structure
    injected_data = []
    for i in range(n_groups):
        group_data = data[i, :]
        # Inject AR(1) with strength r
        try:
            injected_group = ar1_inject(group_data, r=r)
        except Exception as e:
            edge_case_info = {
                "type": "injection_failure",
                "reason": f"Dependency injection failed: {str(e)}",
                "group_index": i
            }
            return None, edge_case_info
        injected_data.append(injected_group)
    
    injected_data = np.array(injected_data)
    
    # Edge Case 2: Check if injected dependency violates normality assumptions
    # beyond non-independence (e.g., extreme skewness/kurtosis from injection)
    if _check_normality_violation(injected_data):
        edge_case_info = {
            "type": "normality_violation",
            "reason": "Injected dependency structure caused severe violation of normality assumptions.",
            "dependency_strength": r
        }
        return None, edge_case_info
    
    # Apply statistical test
    try:
        if test_type == 't-test':
            # Independent samples t-test
            statistic, p_value = stats.ttest_ind(injected_data[0], injected_data[1])
        elif test_type == 'anova':
            # One-way ANOVA
            statistic, p_value = stats.f_oneway(*injected_data)
        else:
            raise ValueError(f"Unsupported test type: {test_type}")
    except Exception as e:
        edge_case_info = {
            "type": "test_execution_failure",
            "reason": f"Statistical test execution failed: {str(e)}",
            "test_type": test_type
        }
        return None, edge_case_info
    
    return p_value, None

def run_simulation(datasets: List[pd.DataFrame], r: float, test_type: str, alpha: float, config: Dict[str, Any]) -> Tuple[List[float], List[Dict[str, Any]]]:
    """
    Run the full simulation loop for a given dependency strength r.
    
    Args:
        datasets: List of datasets (unused for synthetic generation in US1)
        r: Dependency strength
        test_type: Type of statistical test ('t-test', 'anova')
        alpha: Significance level
        config: Configuration dictionary
    
    Returns:
        Tuple of (p_values, edge_case_reports)
        p_values: List of p-values from successful replications
        edge_case_reports: List of dicts describing edge case failures
    """
    n_replications = config.get('n_replications', 1000)
    p_values = []
    edge_case_reports = []
    
    base_seed = config.get('random_seed', 42)
    
    for i in range(n_replications):
        np.random.seed(base_seed + i)
        
        p_val, edge_info = run_single_replication(
            dataset=None,
            r=r,
            test_type=test_type,
            config=config
        )
        
        if p_val is not None:
            p_values.append(p_val)
        else:
            edge_case_reports.append({
                "replication_index": i,
                "r": r,
                "test_type": test_type,
                **edge_info
            })
        
        if (i + 1) % 100 == 0:
            print(f"    Completed {i + 1}/{n_replications} replications")
    
    return p_values, edge_case_reports

def save_edge_case_report(edge_case_reports: List[Dict[str, Any]], output_path: str):
    """
    Save edge case reports to a JSON file.
    
    Args:
        edge_case_reports: List of edge case dictionaries
        output_path: Path to save the JSON report
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(edge_case_reports, f, indent=2)
    print(f"Edge case report saved to {output_path}")

def main():
    """Entry point for simulation runner (for debugging/testing)."""
    print("Simulation runner module loaded.")
    return 0

if __name__ == "__main__":
    exit(main())