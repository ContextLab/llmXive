"""
Diagnostics module for Gut Microbiome-Sleep Architecture Correlation Study.

Implements sensitivity analysis, collinearity diagnostics, and power analysis.
Ensures reproducibility via explicit seed pinning per Constitution Principle I.
"""
import os
import random
import numpy as np
import pandas as pd
from scipy import stats
import json
from pathlib import Path

# Explicitly pin random seeds for reproducibility
# This satisfies Constitution Principle I
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)

def set_diagnostics_seed(seed: int = SEED) -> None:
    """
    Re-pins all random seeds for the diagnostics module.
    Useful for ensuring reproducibility across multiple runs or sub-processes.
    
    Args:
        seed: Integer seed value (default: 42)
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def calculate_vif(df: pd.DataFrame, columns: list) -> dict:
    """
    Calculate Variance Inflation Factor (VIF) for multivariate predictors.
    
    Args:
        df: Input DataFrame
        columns: List of column names to calculate VIF for
        
    Returns:
        dict: VIF values for each column
    """
    if len(columns) < 2:
        return {col: np.inf for col in columns}
    
    vif_results = {}
    
    for i, col in enumerate(columns):
        # Create design matrix for this column
        y = df[col].values
        X = df[[c for c in columns if c != col]].values
        
        # Add constant
        X = sm.add_constant(X)
        
        try:
            # Fit OLS regression
            model = sm.OLS(y, X).fit()
            # VIF = 1 / (1 - R^2)
            r_squared = model.rsquared
            vif = 1 / (1 - r_squared) if r_squared < 1 else np.inf
            vif_results[col] = vif
        except Exception:
            vif_results[col] = np.inf
    
    return vif_results

def detect_perfect_multicollinearity(df: pd.DataFrame, columns: list) -> dict:
    """
    Detect perfect multicollinearity via matrix rank check.
    
    Args:
        df: Input DataFrame
        columns: List of column names to check
        
    Returns:
        dict: Detection results with flags for perfect multicollinearity
    """
    if len(columns) < 2:
        return {
            'detected': False,
            'rank': None,
            'expected_rank': None,
            'problematic_columns': []
        }
    
    X = df[columns].values
    rank = np.linalg.matrix_rank(X)
    expected_rank = len(columns)
    
    detected = rank < expected_rank
    
    problematic = []
    if detected:
        # Identify problematic columns by checking each column's contribution
        for i, col in enumerate(columns):
            X_reduced = np.delete(X, i, axis=1)
            rank_reduced = np.linalg.matrix_rank(X_reduced)
            if rank_reduced == rank:
                problematic.append(col)
    
    return {
        'detected': detected,
        'rank': rank,
        'expected_rank': expected_rank,
        'problematic_columns': problematic
    }

def run_sensitivity_analysis(
    correlation_results: list,
    alpha_levels: list = [0.01, 0.05, 0.10]
) -> dict:
    """
    Run sensitivity analysis on correlation results at different significance levels.
    
    Args:
        correlation_results: List of correlation result dictionaries
        alpha_levels: List of significance levels to test (default: [0.01, 0.05, 0.10])
        
    Returns:
        dict: Sensitivity analysis results with findings at each alpha level
    """
    results = {
        'alpha_levels': alpha_levels,
        'findings_by_alpha': {},
        'stability_metrics': {}
    }
    
    # Extract p-values and correlations
    p_values = []
    correlations = []
    pairs = []
    
    for res in correlation_results:
        if res.get('success') and res.get('p_value') is not None:
            p_values.append(res['p_value'])
            correlations.append(res.get('correlation', res.get('coefficient')))
            pairs.append((res.get('predictor'), res.get('outcome')))
    
    if not p_values:
        return results
    
    for alpha in alpha_levels:
        significant_count = sum(1 for p in p_values if p < alpha)
        significant_pairs = [
            pairs[i] for i, p in enumerate(p_values) if p < alpha
        ]
        
        results['findings_by_alpha'][f'alpha_{alpha}'] = {
            'threshold': alpha,
            'significant_count': significant_count,
            'total_tests': len(p_values),
            'significant_pairs': significant_pairs,
            'percentage_significant': (significant_count / len(p_values)) * 100 if p_values else 0
        }
    
    # Calculate stability metrics
    if len(alpha_levels) > 1:
        counts = [results['findings_by_alpha'][f'alpha_{alpha}']['significant_count'] 
                 for alpha in alpha_levels]
        mean_count = np.mean(counts)
        std_count = np.std(counts)
        cv = (std_count / mean_count) if mean_count > 0 else 0
        
        results['stability_metrics'] = {
            'mean_significant_count': mean_count,
            'std_significant_count': std_count,
            'coefficient_of_variation': cv,
            'stability_assessment': 'stable' if cv < 0.2 else 'moderate' if cv < 0.5 else 'unstable'
        }
    
    return results

def calculate_power(
    n: int,
    expected_r: float = 0.3,
    alpha: float = 0.05,
    power: float = 0.80
) -> dict:
    """
    Calculate statistical power for correlation analysis.
    
    Args:
        n: Sample size
        expected_r: Expected correlation coefficient (default: 0.3)
        alpha: Significance level (default: 0.05)
        power: Desired power (default: 0.80)
        
    Returns:
        dict: Power analysis results
    """
    if n < 3:
        return {
            'power': 0,
            'minimum_n_required': None,
            'is_adequate': False,
            'message': 'Sample size too small for power analysis'
        }
    
    try:
        # Calculate power using t-distribution
        # t = r * sqrt((n-2) / (1-r^2))
        t_stat = expected_r * np.sqrt((n - 2) / (1 - expected_r**2))
        df = n - 2
        
        # Calculate power
        power_value = 1 - stats.t.cdf(t_stat, df) + stats.t.cdf(-t_stat, df)
        
        # Calculate minimum N required for desired power
        # Using approximation: n = (Z_alpha + Z_beta)^2 / r^2 + 3
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)
        min_n = ((z_alpha + z_beta)**2 / expected_r**2) + 3
        
        is_adequate = power_value >= power
        
        return {
            'power': power_value,
            'minimum_n_required': int(np.ceil(min_n)),
            'is_adequate': is_adequate,
            'current_n': n,
            'expected_r': expected_r,
            'alpha': alpha,
            'message': 'Adequate power' if is_adequate else f'Underpowered: need {int(np.ceil(min_n))} samples for {power*100}% power'
        }
    except Exception as e:
        return {
            'power': 0,
            'minimum_n_required': None,
            'is_adequate': False,
            'error': str(e)
        }

def run_collinearity_diagnostics(
    df: pd.DataFrame,
    columns: list,
    vif_threshold: float = 5.0
) -> dict:
    """
    Run comprehensive collinearity diagnostics.
    
    Args:
        df: Input DataFrame
        columns: List of column names to analyze
        vif_threshold: VIF threshold for flagging (default: 5.0)
        
    Returns:
        dict: Collinearity diagnostics report
    """
    # Detect perfect multicollinearity
    multicollinearity = detect_perfect_multicollinearity(df, columns)
    
    # Calculate VIF if no perfect multicollinearity
    if not multicollinearity['detected']:
        vif_results = calculate_vif(df, columns)
    else:
        vif_results = {col: np.inf for col in columns}
    
    # Identify high VIF columns
    high_vif_columns = [col for col, vif in vif_results.items() if vif > vif_threshold]
    
    return {
        'perfect_multicollinearity': multicollinearity,
        'vif_results': vif_results,
        'high_vif_columns': high_vif_columns,
        'vif_threshold': vif_threshold,
        'summary': {
            'total_columns': len(columns),
            'perfectly_collinear': multicollinearity['detected'],
            'high_vif_count': len(high_vif_columns)
        }
    }

def generate_diagnostics_report(
    correlation_results: list,
    df: pd.DataFrame,
    predictor_cols: list,
    outcome_cols: list,
    alpha_levels: list = [0.01, 0.05, 0.10],
    power_threshold: float = 0.80
) -> dict:
    """
    Generate comprehensive diagnostics report.
    
    Args:
        correlation_results: List of correlation result dictionaries
        df: Input DataFrame
        predictor_cols: List of predictor column names
        outcome_cols: List of outcome column names
        alpha_levels: List of significance levels for sensitivity analysis
        power_threshold: Minimum required power (default: 0.80)
        
    Returns:
        dict: Comprehensive diagnostics report
    """
    # Set seed for reproducibility
    set_diagnostics_seed(SEED)
    
    # Run sensitivity analysis
    sensitivity = run_sensitivity_analysis(correlation_results, alpha_levels)
    
    # Run collinearity diagnostics on predictors
    collinearity = run_collinearity_diagnostics(df, predictor_cols)
    
    # Run power analysis
    n_samples = len(df)
    power_analysis = calculate_power(n_samples, expected_r=0.3, alpha=0.05, power=power_threshold)
    
    return {
        'sensitivity_analysis': sensitivity,
        'collinearity_diagnostics': collinearity,
        'power_analysis': power_analysis,
        'sample_size': n_samples,
        'predictor_count': len(predictor_cols),
        'outcome_count': len(outcome_cols),
        'generated_at': pd.Timestamp.now().isoformat()
    }