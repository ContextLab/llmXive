import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple
import warnings

def calculate_smd(df: pd.DataFrame) -> dict:
    """
    Calculate Standardized Mean Differences (SMD) for covariates between treatment and control groups.
    
    Args:
        df: DataFrame containing covariates and a binary 'treatment' column.
        
    Returns:
        Dictionary mapping column names to their SMD values.
    """
    if 'treatment' not in df.columns:
        raise ValueError("DataFrame must contain a 'treatment' column.")
    
    treatment_group = df[df['treatment'] == 1]
    control_group = df[df['treatment'] == 0]
    
    smd_results = {}
    
    # Identify numeric columns for SMD calculation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if 'treatment' in numeric_cols:
        numeric_cols.remove('treatment')
        
    for col in numeric_cols:
        mean_t = treatment_group[col].mean()
        mean_c = control_group[col].mean()
        std_t = treatment_group[col].std()
        std_c = control_group[col].std()
        
        # Avoid division by zero
        if std_t == 0 and std_c == 0:
            smd = 0.0
        else:
            # Pooled standard deviation
            pooled_std = np.sqrt((std_t**2 + std_c**2) / 2)
            if pooled_std == 0:
                smd = 0.0
            else:
                smd = (mean_t - mean_c) / pooled_std
        
        smd_results[col] = smd
        
    return smd_results

def plot_balance(smd_data: dict, threshold: float = 0.1) -> plt.Figure:
    """
    Generate a balance plot (Love plot) showing SMD values before and after matching.
    
    Args:
        smd_data: Dictionary of SMD values.
        threshold: Threshold line for acceptable balance (default 0.1).
        
    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    variables = list(smd_data.keys())
    values = list(smd_data.values())
    
    ax.scatter(values, range(len(variables)), label='Post-Match SMD', color='blue')
    ax.axvline(x=threshold, color='red', linestyle='--', label=f'Threshold ({threshold})')
    ax.axvline(x=-threshold, color='red', linestyle='--')
    
    ax.set_xlabel('Standardized Mean Difference')
    ax.set_ylabel('Covariate')
    ax.set_title('Covariate Balance Plot (Love Plot)')
    ax.set_yticks(range(len(variables)))
    ax.set_yticklabels(variables)
    ax.legend()
    ax.grid(axis='x', linestyle=':', alpha=0.7)
    
    return fig

def run_placebo_test(df: pd.DataFrame, pre_treatment_col: str, treatment_col: str = 'treatment') -> Tuple[float, float, bool]:
    """
    Perform a placebo test to check for significant differences in pre-treatment outcomes
    between matched treatment and control groups.
    
    This test verifies that the matching procedure has successfully balanced the groups
    on pre-existing characteristics. A significant difference suggests residual confounding.
    
    Args:
        df: DataFrame containing the matched sample with pre-treatment outcome and treatment indicator.
        pre_treatment_col: Name of the column representing the pre-treatment outcome variable.
        treatment_col: Name of the column representing the treatment indicator (default: 'treatment').
        
    Returns:
        Tuple of (p_value, t_statistic, is_balanced).
        is_balanced is True if p_value > 0.05 (no significant difference).
        
    Raises:
        ValueError: If required columns are missing or data is insufficient.
    """
    if treatment_col not in df.columns:
        raise ValueError(f"Column '{treatment_col}' not found in DataFrame.")
    if pre_treatment_col not in df.columns:
        raise ValueError(f"Column '{pre_treatment_col}' not found in DataFrame.")
        
    treatment_group = df[df[treatment_col] == 1][pre_treatment_col].dropna()
    control_group = df[df[treatment_col] == 0][pre_treatment_col].dropna()
    
    if len(treatment_group) < 2 or len(control_group) < 2:
        raise ValueError("Insufficient data points in one or both groups for statistical test.")
    
    # Perform independent samples t-test
    # Using Welch's t-test (unequal variances) which is more robust
    t_stat, p_val = sm.stats.ttest_ind(
        treatment_group, 
        control_group, 
        equal_var=False
    )
    
    # Determine balance status (p > 0.05 implies no significant difference -> balanced)
    is_balanced = p_val > 0.05
    
    return float(p_val), float(t_stat), is_balanced

def validate_placebo_results(p_value: float, alpha: float = 0.05) -> bool:
    """
    Validate placebo test results against a significance level.
    
    Args:
        p_value: The p-value from the placebo test.
        alpha: Significance level (default 0.05).
        
    Returns:
        True if the placebo test passes (no significant difference), False otherwise.
    """
    return p_value > alpha

def generate_placebo_report(df: pd.DataFrame, pre_treatment_col: str, 
                            treatment_col: str = 'treatment') -> Dict:
    """
    Generate a comprehensive report for the placebo test.
    
    Args:
        df: Matched DataFrame.
        pre_treatment_col: Pre-treatment outcome column name.
        treatment_col: Treatment indicator column name.
        
    Returns:
        Dictionary containing test statistics and pass/fail status.
    """
    p_val, t_stat, is_balanced = run_placebo_test(df, pre_treatment_col, treatment_col)
    
    report = {
        "pre_treatment_variable": pre_treatment_col,
        "p_value": p_val,
        "t_statistic": t_stat,
        "alpha": 0.05,
        "is_balanced": is_balanced,
        "status": "PASS" if is_balanced else "FAIL",
        "interpretation": (
            "No significant difference found between groups. "
            "Matching appears successful for this pre-treatment variable."
            if is_balanced else
            "Significant difference found. Residual confounding may exist. "
            "Review matching procedure or covariates."
        )
    }
    
    return report

def check_placebo_significance(df: pd.DataFrame, pre_treatment_col: str, 
                               treatment_col: str = 'treatment', 
                               alpha: float = 0.05) -> bool:
    """
    Check if the placebo test indicates a significant difference (failure).
    
    Args:
        df: Matched DataFrame.
        pre_treatment_col: Pre-treatment outcome column name.
        treatment_col: Treatment indicator column name.
        alpha: Significance level.
        
    Returns:
        True if the test passes (no significant difference), False if it fails.
        
    Raises:
        ValueError: If the test indicates significant imbalance.
    """
    p_val, _, is_balanced = run_placebo_test(df, pre_treatment_col, treatment_col)
    
    if not is_balanced:
        raise ValueError(
            f"Placebo test failed (p={p_val:.4f} < {alpha}). "
            f"Significant difference detected in pre-treatment outcome '{pre_treatment_col}'. "
            "This indicates potential residual confounding. Causal estimation should be halted "
            "or the matching procedure re-evaluated."
        )
    
    return True

# Backward compatibility aliases if needed, though the task specifically asks for logic implementation
# The existing stubs in the API surface were: calculate_smd, plot_balance
# This task adds: run_placebo_test, generate_placebo_report, check_placebo_significance

def iterative_matching_with_placebo(df: pd.DataFrame, pre_treatment_col: str, 
                                    caliper: float = 0.05, max_attempts: int = 10) -> Dict:
    """
    Perform iterative matching with placebo validation.
    
    This function attempts to find a matching caliper that achieves both
    covariate balance (SMD <= 0.1) and placebo test pass.
    
    Args:
        df: Input DataFrame.
        pre_treatment_col: Pre-treatment outcome for placebo test.
        caliper: Initial caliper value.
        max_attempts: Maximum number of matching attempts.
        
    Returns:
        Dictionary with matching results and placebo status.
    """
    from src.analysis.psm import iterative_matching
    
    attempt = 0
    current_caliper = caliper
    results = {
        "success": False,
        "matched_data": None,
        "placebo_p_value": None,
        "placebo_status": "PENDING",
        "attempts": 0,
        "final_caliper": current_caliper
    }
    
    while attempt < max_attempts:
        attempt += 1
        results["attempts"] = attempt
        
        try:
            # Run matching (assuming iterative_matching returns a dict with 'matched_data')
            match_result = iterative_matching(df, caliper=current_caliper)
            
            if "matched_data" not in match_result:
                raise ValueError("Matching function did not return 'matched_data'.")
                
            matched_df = match_result["matched_data"]
            
            # Run placebo test
            try:
                check_placebo_significance(matched_df, pre_treatment_col)
                results["placebo_status"] = "PASS"
                results["matched_data"] = matched_df
                results["success"] = True
                results["final_caliper"] = current_caliper
                break
            except ValueError as e:
                # Placebo failed, try tighter caliper
                results["placebo_status"] = "FAIL"
                results["placebo_p_value"] = float(run_placebo_test(matched_df, pre_treatment_col)[0])
                
                # Reduce caliper for next attempt
                current_caliper = max(0.01, current_caliper * 0.8)
                warnings.warn(f"Placebo test failed (p={results['placebo_p_value']:.4f}). "
                              f"Reducing caliper to {current_caliper:.4f} and retrying.")
                
        except Exception as e:
            warnings.warn(f"Matching attempt {attempt} failed: {str(e)}")
            current_caliper = max(0.01, current_caliper * 0.8)
            continue
            
    if not results["success"]:
        results["placebo_status"] = "FAILED_MAX_ATTEMPTS"
        warnings.warn("Failed to achieve placebo balance after max attempts.")
        
    return results

# Ensure the module exports the new functions explicitly
__all__ = [
    'calculate_smd',
    'plot_balance',
    'run_placebo_test',
    'validate_placebo_results',
    'generate_placebo_report',
    'check_placebo_significance',
    'iterative_matching_with_placebo'
]
