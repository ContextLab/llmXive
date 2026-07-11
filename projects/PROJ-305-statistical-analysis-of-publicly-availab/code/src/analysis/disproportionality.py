"""
Disproportionality Analysis Module for VAERS Data.

Implements calculation of Reporting Odds Ratio (ROR), Proportional Reporting Ratio (PRR),
and Information Component (IC) with continuity correction for zero-count cells.
"""
import os
import sys
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for signal detection
ROR_THRESHOLD = 2.0
PRR_THRESHOLD = 1.5
IC_THRESHOLD = 0.0
MIN_REPORTS = 5

def apply_continuity_correction(a: int, b: int, c: int, d: int) -> Tuple[float, float, float, float]:
    """
    Apply continuity correction (add 0.5) to all cells of a 2x2 contingency table
    to prevent division by zero and stabilize estimates for small counts.
    
    Args:
        a: Event count in exposed group (COVID-19)
        b: Non-event count in exposed group (COVID-19)
        c: Event count in unexposed group (Non-COVID)
        d: Non-event count in unexposed group (Non-COVID)
    
    Returns:
        Tuple of corrected counts (a', b', c', d')
    """
    # Add 0.5 to all cells as per continuity correction
    a_corr = a + 0.5
    b_corr = b + 0.5
    c_corr = c + 0.5
    d_corr = d + 0.5
    
    logger.debug(f"Continuity correction applied: ({a}, {b}, {c}, {d}) -> ({a_corr}, {b_corr}, {c_corr}, {d_corr})")
    return a_corr, b_corr, c_corr, d_corr

def calculate_ror(a: float, b: float, c: float, d: float) -> Tuple[float, float]:
    """
    Calculate Reporting Odds Ratio (ROR) and 95% Confidence Interval.
    
    ROR = (a/c) / (b/d) = (a*d) / (b*c)
    
    Args:
        a: Event count in exposed group (with continuity correction)
        b: Non-event count in exposed group (with continuity correction)
        c: Event count in unexposed group (with continuity correction)
        d: Non-event count in unexposed group (with continuity correction)
    
    Returns:
        Tuple of (ROR, 95% CI lower bound, 95% CI upper bound)
    """
    if b == 0 or c == 0:
        logger.warning("Zero count in denominator after correction, returning None")
        return float('nan'), float('nan'), float('nan')
    
    # ROR calculation
    ror = (a * d) / (b * c)
    
    # Log ROR and standard error for CI
    log_ror = math.log(ror)
    se_log_ror = math.sqrt(1/a + 1/b + 1/c + 1/d)
    
    # 95% CI
    z = 1.96
    ci_lower = math.exp(log_ror - z * se_log_ror)
    ci_upper = math.exp(log_ror + z * se_log_ror)
    
    return ror, ci_lower, ci_upper

def calculate_prr(a: int, b: int, c: int, d: int) -> Tuple[float, float, float]:
    """
    Calculate Proportional Reporting Ratio (PRR) and 95% Confidence Interval.
    
    PRR = (a / (a+b)) / (c / (c+d))
    
    Args:
        a: Event count in exposed group (with continuity correction)
        b: Non-event count in exposed group (with continuity correction)
        c: Event count in unexposed group (with continuity correction)
        d: Non-event count in unexposed group (with continuity correction)
    
    Returns:
        Tuple of (PRR, 95% CI lower bound, 95% CI upper bound)
    """
    total_exposed = a + b
    total_unexposed = c + d
    
    if total_exposed == 0 or total_unexposed == 0:
        logger.warning("Zero total in a group after correction, returning None")
        return float('nan'), float('nan'), float('nan')
    
    prop_exposed = a / total_exposed
    prop_unexposed = c / total_unexposed
    
    if prop_unexposed == 0:
        logger.warning("Zero proportion in unexposed group, returning None")
        return float('nan'), float('nan'), float('nan')
    
    prr = prop_exposed / prop_unexposed
    
    # Log PRR and standard error for CI
    log_prr = math.log(prr)
    se_log_prr = math.sqrt((1/a) - (1/total_exposed) + (1/c) - (1/total_unexposed))
    
    # 95% CI
    z = 1.96
    ci_lower = math.exp(log_prr - z * se_log_prr)
    ci_upper = math.exp(log_prr + z * se_log_prr)
    
    return prr, ci_lower, ci_upper

def calculate_ic(a: float, b: float, c: float, d: float) -> Tuple[float, float, float]:
    """
    Calculate Information Component (IC) and 95% Confidence Interval.
    
    IC = log2((a * N) / ((a+b) * (a+c))) where N = a+b+c+d
    
    Args:
        a: Event count in exposed group (with continuity correction)
        b: Non-event count in exposed group (with continuity correction)
        c: Event count in unexposed group (with continuity correction)
        d: Non-event count in unexposed group (with continuity correction)
    
    Returns:
        Tuple of (IC, 95% CI lower bound, 95% CI upper bound)
    """
    n = a + b + c + d
    
    if n == 0 or (a+b) == 0 or (a+c) == 0:
        logger.warning("Zero total or marginal sum, returning None")
        return float('nan'), float('nan'), float('nan')
    
    expected = ((a + b) * (a + c)) / n
    
    if expected == 0:
        logger.warning("Expected count is zero, returning None")
        return float('nan'), float('nan'), float('nan')
    
    ic = math.log2(a / expected)
    
    # Standard error for IC
    se_ic = math.sqrt(1/a - 1/(a+b) + 1/expected - 1/(a+b+c+d))
    
    # 95% CI
    z = 1.96
    ci_lower = ic - z * se_ic
    ci_upper = ic + z * se_ic
    
    return ic, ci_lower, ci_upper

def build_contingency_table(df: pd.DataFrame, soc_code: str, 
                            case_col: str = 'SOC_CODE', 
                            group_col: str = 'VAX_TYPE',
                            case_value: str = 'COVID-19') -> Tuple[int, int, int, int]:
    """
    Build a 2x2 contingency table for a specific SOC.
    
    Table structure:
                | Event (SOC) | No Event (Not SOC) | Total
    ---------------------------------------------------------
    Exposed     | a           | b                  | a+b
    Unexposed   | c           | d                  | c+d
    
    Args:
        df: DataFrame with vaccine and SOC data
        soc_code: The SOC code to analyze
        case_col: Column name for SOC codes
        group_col: Column name for vaccine groups
        case_value: Value indicating the exposed group (default: 'COVID-19')
    
    Returns:
        Tuple of (a, b, c, d) counts
    """
    # Exposed group (COVID-19)
    exposed = df[df[group_col] == case_value]
    a = len(exposed[exposed[case_col] == soc_code])
    b = len(exposed[exposed[case_col] != soc_code])
    
    # Unexposed group (Non-COVID)
    unexposed = df[df[group_col] != case_value]
    c = len(unexposed[unexposed[case_col] == soc_code])
    d = len(unexposed[unexposed[case_col] != soc_code])
    
    logger.debug(f"Contingency table for {soc_code}: a={a}, b={b}, c={c}, d={d}")
    return a, b, c, d

def calculate_disproportionality_metrics(df: pd.DataFrame, 
                                         soc_codes: List[str],
                                         case_col: str = 'SOC_CODE',
                                         group_col: str = 'VAX_TYPE',
                                         case_value: str = 'COVID-19') -> pd.DataFrame:
    """
    Calculate ROR, PRR, and IC for a list of SOC codes.
    
    Applies continuity correction (add 0.5) to all cells to handle zero counts.
    
    Args:
        df: Cleaned DataFrame with vaccine and SOC data
        soc_codes: List of SOC codes to analyze
        case_col: Column name for SOC codes
        group_col: Column name for vaccine groups
        case_value: Value indicating the exposed group
    
    Returns:
        DataFrame with calculated metrics for each SOC
    """
    results = []
    
    for soc_code in soc_codes:
        # Build contingency table
        a, b, c, d = build_contingency_table(df, soc_code, case_col, group_col, case_value)
        
        # Check minimum report threshold
        total_reports = a + c
        if total_reports < MIN_REPORTS:
            logger.info(f"Skipping {soc_code}: only {total_reports} reports (min: {MIN_REPORTS})")
            continue
        
        # Apply continuity correction to prevent division by zero
        a_corr, b_corr, c_corr, d_corr = apply_continuity_correction(a, b, c, d)
        
        # Calculate metrics
        ror, ror_ci_lower, ror_ci_upper = calculate_ror(a_corr, b_corr, c_corr, d_corr)
        prr, prr_ci_lower, prr_ci_upper = calculate_prr(a_corr, b_corr, c_corr, d_corr)
        ic, ic_ci_lower, ic_ci_upper = calculate_ic(a_corr, b_corr, c_corr, d_corr)
        
        results.append({
            'soc_code': soc_code,
            'total_reports': total_reports,
            'exposed_events': a,
            'unexposed_events': c,
            'ror': ror,
            'ror_ci_lower': ror_ci_lower,
            'ror_ci_upper': ror_ci_upper,
            'prr': prr,
            'prr_ci_lower': prr_ci_lower,
            'prr_ci_upper': prr_ci_upper,
            'ic': ic,
            'ic_ci_lower': ic_ci_lower,
            'ic_ci_upper': ic_ci_upper
        })
    
    return pd.DataFrame(results)

def benjamini_hochberg(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """
    Apply Benjamini-Hochberg False Discovery Rate correction to p-values.
    
    Args:
        p_values: Array of raw p-values
        alpha: Significance level (default: 0.05)
    
    Returns:
        Array of adjusted p-values
    """
    n = len(p_values)
    if n == 0:
        return p_values
    
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p = np.zeros(n)
    for i in range(n):
        rank = i + 1
        adjusted_p[sorted_indices[i]] = min(sorted_p[i] * n / rank, 1.0)
    
    # Ensure monotonicity (adjusted p-values should be non-decreasing)
    for i in range(n-2, -1, -1):
        adjusted_p[sorted_indices[i]] = min(adjusted_p[sorted_indices[i]], 
                                             adjusted_p[sorted_indices[i+1]])
    
    return adjusted_p

def calculate_p_value(ror: float, ror_ci_lower: float, ror_ci_upper: float) -> float:
    """
    Calculate two-sided p-value from ROR and its confidence interval.
    
    Args:
        ror: Reporting Odds Ratio
        ror_ci_lower: Lower bound of 95% CI
        ror_ci_upper: Upper bound of 95% CI
    
    Returns:
        Two-sided p-value
    """
    if math.isnan(ror) or ror <= 0:
        return 1.0
    
    # Use log(ROR) and standard error from CI
    log_ror = math.log(ror)
    se_log_ror = (math.log(ror_ci_upper) - math.log(ror_ci_lower)) / (2 * 1.96)
    
    if se_log_ror == 0:
        return 1.0
    
    # Z-score
    z = abs(log_ror / se_log_ror)
    
    # Two-sided p-value
    p_value = 2 * (1 - stats.norm.cdf(z))
    return p_value

def run_analysis(input_path: str, output_path: str) -> None:
    """
    Main function to run disproportionality analysis on cleaned VAERS data.
    
    Args:
        input_path: Path to cleaned VAERS data (Parquet or CSV)
        output_path: Path to save results
    """
    logger.info(f"Loading data from {input_path}")
    
    # Load data
    if input_path.endswith('.parquet'):
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)
    
    logger.info(f"Loaded {len(df)} records")
    
    # Get unique SOC codes
    soc_codes = df['SOC_CODE'].dropna().unique().tolist()
    logger.info(f"Found {len(soc_codes)} unique SOC codes")
    
    # Calculate metrics
    results_df = calculate_disproportionality_metrics(df, soc_codes)
    
    # Calculate p-values
    results_df['p_value'] = results_df.apply(
        lambda row: calculate_p_value(row['ror'], row['ror_ci_lower'], row['ror_ci_upper']),
        axis=1
    )
    
    # Apply Benjamini-Hochberg correction
    results_df['adjusted_p'] = benjamini_hochberg(results_df['p_value'].values)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    results_df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """Entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run disproportionality analysis on VAERS data')
    parser.add_argument('--input', '-i', required=True, help='Input data file (CSV or Parquet)')
    parser.add_argument('--output', '-o', required=True, help='Output file path')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    run_analysis(args.input, args.output)

if __name__ == '__main__':
    main()