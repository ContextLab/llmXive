"""
Metrics calculation module.
Defines functions for calculating Type I error, Power, Confidence Intervals, and Trend Verification.
Includes Chi-squared specific error rate calculations.
"""
import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Optional
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import pandas as pd

def calculate_type1_error(p_values: List[float], alpha: float = 0.05) -> float:
    """
    Calculate the observed Type I error rate.
    
    Args:
        p_values: List of p-values from simulations under the null hypothesis.
        alpha: Significance level threshold.
    
    Returns:
        Proportion of p-values <= alpha.
    """
    if not p_values:
        return 0.0
    
    significant_count = sum(1 for p in p_values if p <= alpha)
    return significant_count / len(p_values)

def calculate_power(p_values: List[float], alpha: float = 0.05) -> float:
    """
    Calculate the observed statistical power.
    
    Args:
        p_values: List of p-values from simulations under the alternative hypothesis.
        alpha: Significance level threshold.
    
    Returns:
        Proportion of p-values <= alpha.
    """
    if not p_values:
        return 0.0
    
    significant_count = sum(1 for p in p_values if p <= alpha)
    return significant_count / len(p_values)

def clopper_pearson_ci(p_values: List[float], alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate the Clopper-Pearson confidence interval for the observed error rate.
    
    Args:
        p_values: List of p-values.
        alpha: Significance level for the test (threshold for significance).
               Note: This is different from the confidence level for the CI.
               We assume a 95% CI for the error rate estimate.
    
    Returns:
        Tuple of (lower_bound, upper_bound) for the 95% CI.
    """
    if not p_values:
        return (0.0, 0.0)
    
    n = len(p_values)
    successes = sum(1 for p in p_values if p <= alpha)
    
    # Clopper-Pearson interval
    # Using beta distribution quantiles
    # Lower bound: beta.ppf(0.025, successes, n - successes + 1)
    # Upper bound: beta.ppf(0.975, successes + 1, n - successes)
    # Handle edge cases where successes is 0 or n
    
    if successes == 0:
        lower = 0.0
    else:
        lower = stats.beta.ppf(0.025, successes, n - successes + 1)
    
    if successes == n:
        upper = 1.0
    else:
        upper = stats.beta.ppf(0.975, successes + 1, n - successes)
    
    return (lower, upper)

def train_logistic_model(data: pd.DataFrame) -> Any:
    """
    Train a logistic regression model relating dependency strength to error outcome.
    
    Args:
        data: DataFrame with columns 'dependency_strength', 'is_significant' (0/1).
    
    Returns:
        Trained LogisticRegression model.
    """
    if 'dependency_strength' not in data.columns or 'is_significant' not in data.columns:
        raise ValueError("Data must contain 'dependency_strength' and 'is_significant' columns.")
    
    X = data[['dependency_strength']].values
    y = data['is_significant'].values
    
    model = LogisticRegression()
    model.fit(X, y)
    
    # Verify convergence and AUC
    try:
        auc = roc_auc_score(y, model.predict_proba(X)[:, 1])
        if auc <= 0.5:
            print(f"Warning: Model AUC is {auc}, which is <= 0.5.")
    except Exception as e:
        print(f"Warning: Could not calculate AUC: {e}")
    
    return model

def verify_trend_monotonicity(df: pd.DataFrame, 
                              strength_col: str = 'dependency_strength', 
                              error_rate_col: str = 'observed_error_rate',
                              alpha: float = 0.05) -> Tuple[float, float, str]:
    """
    Calculate the Spearman rank correlation to verify monotonic increase of error rates 
    with dependency strength (r).
    
    This implements the trend test required by US-1 AC-2.
    
    Args:
        df: DataFrame containing the aggregated simulation results.
            Must contain columns for dependency strength and observed error rate.
        strength_col: Name of the column containing dependency strength values (r).
        error_rate_col: Name of the column containing observed error rates.
        alpha: Significance threshold for the trend test p-value.
    
    Returns:
        Tuple of (spearman_correlation, p_value, trend_status).
        trend_status is 'MONOTONIC_INCREASE' if p < alpha and rho > 0, 
        otherwise 'NON_MONOTONIC' or 'NO_TREND'.
    """
    if strength_col not in df.columns or error_rate_col not in df.columns:
        raise ValueError(f"DataFrame must contain '{strength_col}' and '{error_rate_col}' columns.")
    
    # Remove any rows with NaN values in the relevant columns
    valid_df = df[[strength_col, error_rate_col]].dropna()
    
    if len(valid_df) < 2:
        return (0.0, 1.0, "INSUFFICIENT_DATA")
    
    # Calculate Spearman rank correlation
    rho, p_value = stats.spearmanr(valid_df[strength_col], valid_df[error_rate_col])
    
    # Determine trend status
    if p_value < alpha and rho > 0:
        trend_status = "MONOTONIC_INCREASE"
    elif p_value < alpha and rho < 0:
        trend_status = "MONOTONIC_DECREASE"
    else:
        trend_status = "NO_SIGNIFICANT_TREND"
    
    return (rho, p_value, trend_status)

def calculate_chi_squared_error_rate(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate the observed Type I error rate specifically for Chi-squared tests.
    
    This function implements the Chi-squared error rate calculation and reporting
    required by FR-005 for User Story 2. It provides the same core calculation as
    calculate_type1_error but is explicitly named and documented for Chi-squared
    test results to ensure clarity in reporting and aggregation.
    
    Args:
        p_values: List of p-values from Chi-squared simulations under the null hypothesis.
        alpha: Significance level threshold (default 0.05).
    
    Returns:
        Dictionary containing:
            - 'error_rate': The observed error rate (proportion of significant tests).
            - 'total_tests': Total number of tests performed.
            - 'significant_count': Number of tests that were significant.
            - 'ci_lower': Lower bound of 95% Clopper-Pearson CI.
            - 'ci_upper': Upper bound of 95% Clopper-Pearson CI.
    """
    if not p_values:
        return {
            'error_rate': 0.0,
            'total_tests': 0,
            'significant_count': 0,
            'ci_lower': 0.0,
            'ci_upper': 0.0
        }
    
    total_tests = len(p_values)
    significant_count = sum(1 for p in p_values if p <= alpha)
    error_rate = significant_count / total_tests
    
    # Calculate Clopper-Pearson CI
    ci_lower, ci_upper = clopper_pearson_ci(p_values, alpha)
    
    return {
        'error_rate': error_rate,
        'total_tests': total_tests,
        'significant_count': significant_count,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper
    }

def aggregate_chi_squared_results(results_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate Chi-squared error rate results from multiple simulation runs.
    
    Args:
        results_list: List of dictionaries containing Chi-squared results.
                      Each dict should have keys: 'dependency_strength', 'error_rate',
                      'ci_lower', 'ci_upper', 'total_tests', 'significant_count'.
    
    Returns:
        DataFrame with aggregated results sorted by dependency strength.
    """
    if not results_list:
        return pd.DataFrame()
    
    df = pd.DataFrame(results_list)
    
    # Ensure required columns exist
    required_cols = ['dependency_strength', 'error_rate', 'ci_lower', 'ci_upper', 'total_tests', 'significant_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in results: {missing_cols}")
    
    # Sort by dependency strength
    df = df.sort_values('dependency_strength').reset_index(drop=True)
    
    return df