"""
Disproportionality Analysis Module for VAERS Data.
Implements ROR, PRR, IC calculations with continuity correction and confidence intervals.
"""
import os
import sys
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_continuity_correction(a: int, b: int, c: int, d: int) -> Tuple[float, float, float, float]:
    """
    Apply 0.5 continuity correction to a 2x2 contingency table to avoid division by zero.
    
    Args:
        a: Event in exposed group (COVID-19 + Event)
        b: No event in exposed group (COVID-19 + No Event)
        c: Event in unexposed group (Non-COVID + Event)
        d: No event in unexposed group (Non-COVID + No Event)
    
    Returns:
        Tuple of corrected (a, b, c, d)
    """
    return (a + 0.5, b + 0.5, c + 0.5, d + 0.5)

def build_contingency_table(df: pd.DataFrame, soc_code: str, 
                            exposed_col: str = 'VAX_TYPE_GROUP', 
                            event_col: str = 'SOC_CODE') -> Dict[str, int]:
    """
    Build a 2x2 contingency table for a specific SOC code.
    
    Table structure:
                | Event (SOC match) | No Event (SOC mismatch)
    -----------------------------------------------------------
    Exposed (COVID)   |      a        |          b
    Unexposed (Non-COVID) |      c        |          d
    
    Args:
        df: DataFrame with 'VAX_TYPE_GROUP' and 'SOC_CODE' columns
        soc_code: The specific SOC code to analyze
        exposed_col: Column name for exposure status
        event_col: Column name for event status
    
    Returns:
        Dictionary with keys 'a', 'b', 'c', 'd'
    """
    # Create mask for event presence
    event_mask = df[event_col] == soc_code
    
    # Create mask for exposure (COVID-19)
    exposed_mask = df[exposed_col] == 'COVID-19'
    
    # Calculate counts
    a = int((event_mask & exposed_mask).sum())
    b = int((~event_mask & exposed_mask).sum())
    c = int((event_mask & ~exposed_mask).sum())
    d = int((~event_mask & ~exposed_mask).sum())
    
    return {'a': a, 'b': b, 'c': c, 'd': d}

def calculate_ror(a: float, b: float, c: float, d: float) -> float:
    """
    Calculate Reporting Odds Ratio (ROR).
    ROR = (a/c) / (b/d) = (a*d) / (b*c)
    
    Args:
        a, b, c, d: Continuity-corrected contingency table values
    
    Returns:
        ROR value
    """
    if b * c == 0:
        return float('inf')
    return (a * d) / (b * c)

def calculate_prr(a: float, b: float, c: float, d: float) -> float:
    """
    Calculate Proportional Reporting Ratio (PRR).
    PRR = (a / (a+b)) / (c / (c+d))
    
    Args:
        a, b, c, d: Continuity-corrected contingency table values
    
    Returns:
        PRR value
    """
    if (a + b) == 0 or (c + d) == 0:
        return float('inf')
    
    p1 = a / (a + b)
    p2 = c / (c + d)
    
    if p2 == 0:
        return float('inf')
    
    return p1 / p2

def calculate_ic(a: float, b: float, c: float, d: float) -> float:
    """
    Calculate Information Component (IC).
    IC = log2( (a / (a+b)) / ( (a+c) / (a+b+c+d) ) )
    
    Args:
        a, b, c, d: Continuity-corrected contingency table values
    
    Returns:
        IC value
    """
    total = a + b + c + d
    if total == 0 or (a + b) == 0 or (a + c) == 0:
        return float('nan')
    
    observed = a / (a + b)
    expected = (a + c) / total
    
    if expected == 0:
        return float('inf')
    
    return math.log2(observed / expected)

def calculate_p_value_chi2(a: float, b: float, c: float, d: float) -> float:
    """
    Calculate p-value using Chi-squared test with Yates' continuity correction.
    Uses the standard formula for 2x2 table chi-squared statistic.
    
    Args:
        a, b, c, d: Continuity-corrected contingency table values
    
    Returns:
        p-value from chi-squared distribution (1 degree of freedom)
    """
    n = a + b + c + d
    if n == 0:
        return 1.0
    
    # Expected values
    row1 = a + b
    row2 = c + d
    col1 = a + c
    col2 = b + d
    
    if row1 == 0 or row2 == 0 or col1 == 0 or col2 == 0:
        return 1.0
    
    # Chi-squared with Yates' correction
    # |ad - bc| - n/2
    numerator = abs(a * d - b * c) - (n / 2)
    if numerator < 0:
        numerator = 0
    
    denominator = (row1 * row2 * col1 * col2) / (n ** 2)
    
    if denominator == 0:
        return 1.0
    
    chi2 = (numerator ** 2) / denominator
    
    # Approximate p-value using survival function of chi-squared(1)
    # Using the approximation: p = exp(-chi2/2) for large chi2
    # For better accuracy, we use the standard normal approximation
    z = math.sqrt(chi2)
    # Standard normal CDF approximation
    p_value = 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))
    
    return max(0.0, min(1.0, p_value))

def calculate_ci_ror(a: float, b: float, c: float, d: float, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for ROR.
    CI = exp(ln(ROR) ± Z * sqrt(1/a + 1/b + 1/c + 1/d))
    
    Args:
        a, b, c, d: Continuity-corrected contingency table values
        alpha: Significance level (default 0.05 for 95% CI)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if a <= 0 or b <= 0 or c <= 0 or d <= 0:
        return (float('-inf'), float('inf'))
    
    lor = math.log((a * d) / (b * c))
    se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    
    # Z-score for 95% CI
    z = 1.96 if alpha == 0.05 else 2.576
    
    lower = math.exp(lor - z * se)
    upper = math.exp(lor + z * se)
    
    return (lower, upper)

def calculate_ci_prr(a: float, b: float, c: float, d: float, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for PRR.
    CI = exp(ln(PRR) ± Z * sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d)))
    
    Args:
        a, b, c, d: Continuity-corrected contingency table values
        alpha: Significance level (default 0.05 for 95% CI)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if a <= 0 or c <= 0:
        return (float('-inf'), float('inf'))
    
    p1 = a / (a + b)
    p2 = c / (c + d)
    
    if p1 <= 0 or p2 <= 0:
        return (float('-inf'), float('inf'))
    
    lpr = math.log(p1 / p2)
    se = math.sqrt((1/a) - (1/(a+b)) + (1/c) - (1/(c+d)))
    
    z = 1.96 if alpha == 0.05 else 2.576
    
    lower = math.exp(lpr - z * se)
    upper = math.exp(lpr + z * se)
    
    return (lower, upper)

def calculate_ci_ic(a: float, b: float, c: float, d: float, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for IC.
    IC_CI = IC ± Z * sqrt(1/a + 1/c)
    Note: This is an approximation for the IC variance.
    
    Args:
        a, b, c, d: Continuity-corrected contingency table values
        alpha: Significance level (default 0.05 for 95% CI)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if a <= 0 or c <= 0:
        return (float('-inf'), float('inf'))
    
    ic = calculate_ic(a, b, c, d)
    if math.isnan(ic) or math.isinf(ic):
        return (float('-inf'), float('inf'))
    
    se = math.sqrt(1/a + 1/c)
    z = 1.96 if alpha == 0.05 else 2.576
    
    lower = ic - z * se
    upper = ic + z * se
    
    return (lower, upper)

def calculate_disproportionality_metrics(df: pd.DataFrame, soc_code: str, 
                                         continuity_correction: bool = True) -> Dict[str, Any]:
    """
    Calculate all disproportionality metrics for a given SOC code.
    
    Args:
        df: DataFrame with 'VAX_TYPE_GROUP' and 'SOC_CODE' columns
        soc_code: The SOC code to analyze
        continuity_correction: Whether to apply 0.5 correction
    
    Returns:
        Dictionary with ROR, PRR, IC, p-value, and confidence intervals
    """
    table = build_contingency_table(df, soc_code)
    a, b, c, d = table['a'], table['b'], table['c'], table['d']
    
    # Apply continuity correction if requested
    if continuity_correction:
        a, b, c, d = apply_continuity_correction(a, b, c, d)
    
    # Calculate metrics
    ror = calculate_ror(a, b, c, d)
    prr = calculate_prr(a, b, c, d)
    ic = calculate_ic(a, b, c, d)
    p_value = calculate_p_value_chi2(a, b, c, d)
    
    # Calculate confidence intervals
    ci_ror = calculate_ci_ror(a, b, c, d)
    ci_prr = calculate_ci_prr(a, b, c, d)
    ci_ic = calculate_ci_ic(a, b, c, d)
    
    return {
        'soc_code': soc_code,
        'a': int(table['a']),
        'b': int(table['b']),
        'c': int(table['c']),
        'd': int(table['d']),
        'ror': ror,
        'prr': prr,
        'ic': ic,
        'p_value': p_value,
        'ror_ci_lower': ci_ror[0],
        'ror_ci_upper': ci_ror[1],
        'prr_ci_lower': ci_prr[0],
        'prr_ci_upper': ci_prr[1],
        'ic_ci_lower': ci_ic[0],
        'ic_ci_upper': ci_ic[1]
    }

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
    
    Returns:
        List of adjusted p-values
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with their original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate adjusted p-values
    adjusted = [0.0] * n
    min_adj = 1.0
    
    for i in range(n - 1, -1, -1):
        rank = i + 1
        adj_p = min(1.0, sorted_p_values[i] * n / rank)
        min_adj = min(min_adj, adj_p)
        adjusted[sorted_indices[i]] = min_adj
    
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        adjusted[sorted_indices[i]] = min(adjusted[sorted_indices[i]], adjusted[sorted_indices[i+1]])
    
    return adjusted

def run_analysis(df: pd.DataFrame, min_reports: int = 5) -> pd.DataFrame:
    """
    Run disproportionality analysis on all SOCs with at least min_reports.
    
    Args:
        df: Cleaned DataFrame with 'VAX_TYPE_GROUP' and 'SOC_CODE' columns
        min_reports: Minimum number of total reports required for analysis
    
    Returns:
        DataFrame with all metrics and signal flags
    """
    logger.info(f"Running disproportionality analysis on {len(df)} records")
    
    # Filter SOCs with at least min_reports
    soc_counts = df['SOC_CODE'].value_counts()
    valid_socs = soc_counts[soc_counts >= min_reports].index.tolist()
    
    logger.info(f"Analyzing {len(valid_socs)} SOCs with >= {min_reports} reports")
    
    results = []
    for soc in valid_socs:
        try:
            metrics = calculate_disproportionality_metrics(df, soc)
            results.append(metrics)
        except Exception as e:
            logger.warning(f"Error processing SOC {soc}: {e}")
            continue
    
    if not results:
        logger.warning("No results generated")
        return pd.DataFrame()
    
    df_results = pd.DataFrame(results)
    
    # Apply Benjamini-Hochberg correction
    df_results['adjusted_p'] = benjamini_hochberg(df_results['p_value'].tolist())
    
    # Flag signals based on 2-out-of-3 rule
    # ROR>2.0/CI>1.0, PRR>1.5/CI>1.0, IC>0/CI>0
    df_results['signal_ror'] = (df_results['ror'] > 2.0) & (df_results['ror_ci_lower'] > 1.0)
    df_results['signal_prr'] = (df_results['prr'] > 1.5) & (df_results['prr_ci_lower'] > 1.0)
    df_results['signal_ic'] = (df_results['ic'] > 0) & (df_results['ic_ci_lower'] > 0)
    
    # 2-out-of-3 rule
    df_results['is_signal'] = (
        df_results['signal_ror'].astype(int) + 
        df_results['signal_prr'].astype(int) + 
        df_results['signal_ic'].astype(int)
    ) >= 2
    
    return df_results

def main():
    """Main entry point for disproportionality analysis."""
    # Example usage
    logger.info("Disproportionality analysis module loaded")
    
    # Create sample data for testing
    data = {
        'VAX_TYPE_GROUP': ['COVID-19'] * 100 + ['Non-COVID'] * 100,
        'SOC_CODE': ['SOC001'] * 20 + ['SOC002'] * 10 + ['SOC003'] * 5 + 
                    ['SOC001'] * 15 + ['SOC002'] * 5 + ['SOC003'] * 2
    }
    df = pd.DataFrame(data)
    
    results = run_analysis(df, min_reports=5)
    if not results.empty:
        print(results.to_string())
    else:
        logger.warning("No results to display")

if __name__ == "__main__":
    main()
