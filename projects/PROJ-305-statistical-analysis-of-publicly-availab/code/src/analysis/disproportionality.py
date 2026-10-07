import os
import sys
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

from src.utils.config import THRESHOLDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/analysis.log')
    ]
)
logger = logging.getLogger(__name__)

def apply_continuity_correction(a: int, b: int, c: int, d: int) -> Tuple[int, int, int, int]:
    """
    Apply continuity correction (add 0.5) to zero-count cells in a 2x2 table.
    
    Table structure:
              | Event | No Event
    ----------|-------|----------
    Exposed   | a     | b
    Unexposed | c     | d
    
    Args:
        a: Exposed with event
        b: Exposed without event
        c: Unexposed with event
        d: Unexposed without event
        
    Returns:
        Tuple of (a, b, c, d) with 0.5 added to any zero cell.
    """
    a = a + 0.5 if a == 0 else a
    b = b + 0.5 if b == 0 else b
    c = c + 0.5 if c == 0 else c
    d = d + 0.5 if d == 0 else d
    return int(a), int(b), int(c), int(d)

def build_contingency_table(df: pd.DataFrame, soc: str, event_col: str = 'has_event') -> Dict[str, int]:
    """
    Build a 2x2 contingency table for a specific SOC.
    
    Args:
        df: Cleaned DataFrame with columns 'GROUP', 'has_event', 'SOC'
        soc: System Organ Class to analyze
        event_col: Column name indicating if the record is an event (1) or control (0)
        
    Returns:
        Dictionary with keys 'a', 'b', 'c', 'd' representing the 2x2 table.
    """
    soc_data = df[df['SOC'] == soc]
    
    # COVID-19 Group (Exposed)
    covid_events = len(soc_data[(soc_data['GROUP'] == 'COVID-19') & (soc_data[event_col] == 1)])
    covid_no_events = len(soc_data[(soc_data['GROUP'] == 'COVID-19') & (soc_data[event_col] == 0)])
    
    # Full Non-COVID Group (Unexposed) - includes Flu
    noncovid_events = len(soc_data[(soc_data['GROUP'] == 'Full Non-COVID') & (soc_data[event_col] == 1)])
    noncovid_no_events = len(soc_data[(soc_data['GROUP'] == 'Full Non-COVID') & (soc_data[event_col] == 0)])
    
    return {
        'a': covid_events,
        'b': covid_no_events,
        'c': noncovid_events,
        'd': noncovid_no_events
    }

def calculate_ror(a: int, b: int, c: int, d: int) -> float:
    """
    Calculate Reporting Odds Ratio (ROR).
    
    ROR = (a/b) / (c/d) = (a*d) / (b*c)
    
    Args:
        a, b, c, d: Cells of the 2x2 contingency table
        
    Returns:
        ROR value.
    """
    if b == 0 or c == 0:
        return float('inf')
    return (a * d) / (b * c)

def calculate_prr(a: int, b: int, c: int, d: int) -> float:
    """
    Calculate Proportional Reporting Ratio (PRR).
    
    PRR = (a / (a+b)) / (c / (c+d))
    
    Args:
        a, b, c, d: Cells of the 2x2 contingency table
        
    Returns:
        PRR value.
    """
    if (a + b) == 0 or (c + d) == 0:
        return float('inf')
    exposed_rate = a / (a + b)
    unexposed_rate = c / (c + d)
    if unexposed_rate == 0:
        return float('inf')
    return exposed_rate / unexposed_rate

def calculate_ic(a: int, b: int, c: int, d: int) -> float:
    """
    Calculate Information Component (IC).
    
    IC = log2((a * (a+b+c+d)) / ((a+b) * (a+c)))
    
    Args:
        a, b, c, d: Cells of the 2x2 contingency table
        
    Returns:
        IC value.
    """
    n = a + b + c + d
    if (a + b) == 0 or (a + c) == 0 or a == 0:
        return float('-inf')
    numerator = a * n
    denominator = (a + b) * (a + c)
    if denominator == 0:
        return float('-inf')
    return math.log2(numerator / denominator)

def calculate_ci_ror(a: int, b: int, c: int, d: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for ROR.
    
    CI = exp(ln(ROR) ± 1.96 * sqrt(1/a + 1/b + 1/c + 1/d))
    
    Args:
        a, b, c, d: Cells of the 2x2 contingency table
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if a == 0 or b == 0 or c == 0 or d == 0:
        return (0.0, float('inf'))
    
    z = 1.96  # For 95% CI
    se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    ror = calculate_ror(a, b, c, d)
    if ror == 0 or ror == float('inf'):
        return (0.0, float('inf'))
    
    ln_ror = math.log(ror)
    lower = math.exp(ln_ror - z * se)
    upper = math.exp(ln_ror + z * se)
    return (lower, upper)

def calculate_ci_prr(a: int, b: int, c: int, d: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for PRR.
    
    CI = exp(ln(PRR) ± 1.96 * sqrt((1/a - 1/(a+b)) + (1/c - 1/(c+d))))
    
    Args:
        a, b, c, d: Cells of the 2x2 contingency table
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if a == 0 or c == 0 or (a+b) == 0 or (c+d) == 0:
        return (0.0, float('inf'))
    
    z = 1.96
    prr = calculate_prr(a, b, c, d)
    if prr == float('inf'):
        return (0.0, float('inf'))
    
    se = math.sqrt((1/a - 1/(a+b)) + (1/c - 1/(c+d)))
    ln_prr = math.log(prr)
    lower = math.exp(ln_prr - z * se)
    upper = math.exp(ln_prr + z * se)
    return (lower, upper)

def calculate_ci_ic(a: int, b: int, c: int, d: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for IC.
    
    CI = IC ± 1.96 * sqrt(1/(a*ln(2)^2))
    
    Args:
        a, b, c, d: Cells of the 2x2 contingency table
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if a == 0:
        return (float('-inf'), float('-inf'))
    
    z = 1.96
    ic = calculate_ic(a, b, c, d)
    if ic == float('-inf'):
        return (float('-inf'), float('-inf'))
    
    se = math.sqrt(1 / (a * (math.log(2) ** 2)))
    lower = ic - z * se
    upper = ic + z * se
    return (lower, upper)

def calculate_p_value_chi2(a: int, b: int, c: int, d: int) -> float:
    """
    Calculate p-value using Chi-squared test with Yates' continuity correction.
    
    Args:
        a, b, c, d: Cells of the 2x2 contingency table
        
    Returns:
        p-value from Chi-squared test.
    """
    from scipy import stats
    
    # Create contingency table
    table = [[a, b], [c, d]]
    try:
        _, p_value, _, _ = stats.chi2_contingency(table, correction=True)
        return p_value
    except Exception as e:
        logger.warning(f"Chi-squared test failed for table {table}: {e}")
        return 1.0

def calculate_disproportionality_metrics(a: int, b: int, c: int, d: int) -> Dict[str, Any]:
    """
    Calculate all disproportionality metrics for a 2x2 table.
    
    Args:
        a, b, c, d: Cells of the 2x2 contingency table
        
    Returns:
        Dictionary containing ROR, PRR, IC, their CIs, and p-value.
    """
    # Apply continuity correction
    a_corr, b_corr, c_corr, d_corr = apply_continuity_correction(a, b, c, d)
    
    ror = calculate_ror(a_corr, b_corr, c_corr, d_corr)
    ror_ci = calculate_ci_ror(a_corr, b_corr, c_corr, d_corr)
    
    prr = calculate_prr(a_corr, b_corr, c_corr, d_corr)
    prr_ci = calculate_ci_prr(a_corr, b_corr, c_corr, d_corr)
    
    ic = calculate_ic(a_corr, b_corr, c_corr, d_corr)
    ic_ci = calculate_ci_ic(a_corr, b_corr, c_corr, d_corr)
    
    p_value = calculate_p_value_chi2(a_corr, b_corr, c_corr, d_corr)
    
    return {
        'ror': ror,
        'ror_ci_lower': ror_ci[0],
        'ror_ci_upper': ror_ci[1],
        'prr': prr,
        'prr_ci_lower': prr_ci[0],
        'prr_ci_upper': prr_ci[1],
        'ic': ic,
        'ic_ci_lower': ic_ci[0],
        'ic_ci_upper': ic_ci[1],
        'p_value': p_value
    }

def benjamini_hochberg(p_values: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Apply Benjamini-Hochberg correction for multiple testing.
    
    Args:
        p_values: List of (soc, p_value) tuples
        
    Returns:
        List of (soc, adjusted_p_value) tuples, sorted by SOC.
    """
    if not p_values:
        return []
    
    # Sort by p-value
    sorted_p = sorted(p_values, key=lambda x: x[1])
    n = len(sorted_p)
    
    # Calculate adjusted p-values
    adjusted = []
    prev_adj = 1.0
    
    for i, (soc, p) in reversed(list(enumerate(sorted_p))):
        rank = i + 1
        adj_p = min(p * n / rank, prev_adj)
        adjusted.append((soc, adj_p))
        prev_adj = adj_p
    
    # Reverse to restore original order (sorted by p-value), then sort by SOC
    adjusted.reverse()
    return sorted(adjusted, key=lambda x: x[0])

def run_analysis(input_path: str, output_path: str) -> None:
    """
    Run disproportionality analysis on cleaned data.
    
    Args:
        input_path: Path to cleaned_vaers_full_non_covid.parquet
        output_path: Path to output signals CSV
    """
    logger.info(f"Loading data from {input_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} records")
    
    # Filter SOCs with >= 5 total reports
    soc_counts = df.groupby('SOC').size()
    valid_socs = soc_counts[soc_counts >= 5].index.tolist()
    logger.info(f"Analyzing {len(valid_socs)} SOCs with >= 5 reports")
    
    results = []
    p_values_list = []
    
    for soc in valid_socs:
        contingency = build_contingency_table(df, soc)
        a, b, c, d = contingency['a'], contingency['b'], contingency['c'], contingency['d']
        
        metrics = calculate_disproportionality_metrics(a, b, c, d)
        metrics['soc'] = soc
        metrics['total_reports'] = a + b + c + d
        metrics['background_rate_status'] = 'UNKNOWN'
        
        results.append(metrics)
        p_values_list.append((soc, metrics['p_value']))
        
        logger.debug(f"SOC {soc}: ROR={metrics['ror']:.2f}, PRR={metrics['prr']:.2f}, IC={metrics['ic']:.2f}")
    
    # Apply Benjamini-Hochberg correction
    adjusted_p = benjamini_hochberg(p_values_list)
    adj_dict = dict(adjusted_p)
    for row in results:
        row['p_adj'] = adj_dict.get(row['soc'], 1.0)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Ensure all numeric columns are finite
    numeric_cols = ['ror', 'ror_ci_lower', 'ror_ci_upper', 'prr', 'prr_ci_lower', 
                   'prr_ci_upper', 'ic', 'ic_ci_lower', 'ic_ci_upper', 'p_value', 'p_adj']
    for col in numeric_cols:
        results_df[col] = results_df[col].replace([np.inf, -np.inf], np.nan)
    
    # Sort by SOC for consistent output
    results_df = results_df.sort_values('soc').reset_index(drop=True)
    
    logger.info(f"Writing results to {output_path}")
    results_df.to_csv(output_path, index=False)
    logger.info(f"Analysis complete. {len(results_df)} SOCs analyzed.")

def main():
    """Main entry point for disproportionality analysis."""
    input_path = "data/processed/cleaned_vaers_full_non_covid.parquet"
    output_path = "output/signals.csv"
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    run_analysis(input_path, output_path)

if __name__ == "__main__":
    main()