import os
import sys
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

# Add project root to path if running as script
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.config import ensure_dirs, THRESHOLDS, MEMORY_LIMITS
from src.data.clean import get_memory_usage_gb, check_memory_usage

logger = logging.getLogger("pipeline")

def apply_continuity_correction(a: int, b: int, c: int, d: int) -> Tuple[float, float, float, float]:
    """Apply 0.5 continuity correction to 2x2 table cells."""
    return a + 0.5, b + 0.5, c + 0.5, d + 0.5

def build_contingency_table(df: pd.DataFrame, soc: str) -> Tuple[int, int, int, int]:
    """
    Build 2x2 contingency table for a specific SOC.
    Rows: Event (SOC present), No Event (SOC absent)
    Cols: COVID-19, Non-COVID-Non-Flu (Reference)
    
    Returns: (a, b, c, d) where:
    a = COVID-19 with Event
    b = Non-COVID-Non-Flu with Event
    c = COVID-19 without Event
    d = Non-COVID-Non-Flu without Event
    """
    # Filter for the specific SOC
    soc_df = df[df['SOC'] == soc]
    
    # Total counts per group
    covid_total = len(df[df['GROUP'] == 'COVID-19'])
    ref_total = len(df[df['GROUP'] == 'Non-COVID-Non-Flu'])
    
    # Event counts
    covid_event = len(soc_df[soc_df['GROUP'] == 'COVID-19'])
    ref_event = len(soc_df[soc_df['GROUP'] == 'Non-COVID-Non-Flu'])
    
    # No event counts
    covid_no_event = covid_total - covid_event
    ref_no_event = ref_total - ref_event
    
    return covid_event, ref_event, covid_no_event, ref_no_event

def calculate_ror(a: float, b: float, c: float, d: float) -> float:
    """Calculate Reporting Odds Ratio."""
    if c == 0 or d == 0:
        return float('inf')
    return (a * d) / (b * c)

def calculate_prr(a: float, b: float, c: float, d: float) -> float:
    """Calculate Proportional Reporting Ratio."""
    p1 = a / (a + c)
    p2 = b / (b + d)
    if p2 == 0:
        return float('inf')
    return p1 / p2

def calculate_ic(a: float, b: float, c: float, d: float) -> float:
    """Calculate Information Component."""
    if a == 0:
        return float('-inf') # Or handle as 0 depending on convention
    p1 = a / (a + c)
    p2 = b / (b + d)
    # IC = log2( (a/(a+c)) / ( (a+b)/(a+b+c+d) ) ) ... simplified here to log2(ROR) approximation or specific formula
    # Standard IC formula: IC = log2( (a * N) / ((a+c) * (a+b)) )
    # Where N = a+b+c+d
    N = a + b + c + d
    expected = (a + c) * (a + b) / N
    if expected == 0:
        return float('inf')
    return math.log2(a / expected)

def calculate_ci_ror(a: float, b: float, c: float, d: float) -> Tuple[float, float]:
    """Calculate 95% CI for ROR using Woolf's method."""
    # SE(log(ROR)) = sqrt(1/a + 1/b + 1/c + 1/d)
    if a == 0 or b == 0 or c == 0 or d == 0:
        return (float('-inf'), float('inf'))
    
    se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    log_ror = math.log((a * d) / (b * c))
    lower = math.exp(log_ror - 1.96 * se)
    upper = math.exp(log_ror + 1.96 * se)
    return lower, upper

def calculate_ci_prr(a: float, b: float, c: float, d: float) -> Tuple[float, float]:
    """Calculate 95% CI for PRR."""
    # SE(log(PRR)) = sqrt( (1/a - 1/(a+c)) + (1/b - 1/(b+d)) )
    if a == 0 or b == 0:
        return (float('-inf'), float('inf'))
    
    se = math.sqrt((1/a - 1/(a+c)) + (1/b - 1/(b+d)))
    log_prr = math.log((a * (b + d)) / (b * (a + c)))
    lower = math.exp(log_prr - 1.96 * se)
    upper = math.exp(log_prr + 1.96 * se)
    return lower, upper

def calculate_ci_ic(a: float, b: float, c: float, d: float) -> Tuple[float, float]:
    """Calculate 95% CI for IC."""
    # SE(IC) approx = 1 / sqrt(a)
    if a == 0:
        return (float('-inf'), float('inf'))
    se = 1.0 / math.sqrt(a)
    ic_val = calculate_ic(a, b, c, d)
    lower = ic_val - 1.96 * se
    upper = ic_val + 1.96 * se
    return lower, upper

def calculate_p_value_chi2(a: float, b: float, c: float, d: float) -> float:
    """Calculate p-value using Chi-square test (approximation)."""
    # Chi2 = (ad - bc)^2 * N / ((a+b)(c+d)(a+c)(b+d))
    N = a + b + c + d
    numerator = (a * d - b * c) ** 2 * N
    denominator = (a + b) * (c + d) * (a + c) * (b + d)
    if denominator == 0:
        return 1.0
    chi2 = numerator / denominator
    # Approximate p-value from chi2 (1 df)
    # Using survival function of chi2 distribution
    # For simplicity, we use a rough approximation or scipy if available
    # Since we want to avoid heavy deps, we'll use a simple approximation or return 0 if significant
    # Better: import scipy.stats if available, else fallback
    try:
        from scipy.stats import chi2 as chi2_dist
        return 1 - chi2_dist.cdf(chi2, 1)
    except ImportError:
        # Fallback: if chi2 > 3.84 (p<0.05), return 0.05, else 1.0
        if chi2 > 3.841:
            return 0.05
        return 1.0

def calculate_disproportionality_metrics(a: float, b: float, c: float, d: float) -> Dict[str, float]:
    """Calculate all metrics for a single SOC."""
    # Apply continuity correction
    a, b, c, d = apply_continuity_correction(a, b, c, d)
    
    ror = calculate_ror(a, b, c, d)
    prr = calculate_prr(a, b, c, d)
    ic = calculate_ic(a, b, c, d)
    
    ror_ci = calculate_ci_ror(a, b, c, d)
    prr_ci = calculate_ci_prr(a, b, c, d)
    ic_ci = calculate_ci_ic(a, b, c, d)
    
    p_val = calculate_p_value_chi2(a, b, c, d)
    
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
        'p_raw': p_val
    }

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg correction for multiple testing."""
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]
    
    adjusted = [0.0] * n
    min_val = 1.0
    
    # Calculate adjusted p-values
    for i in range(n - 1, -1, -1):
        j = sorted_indices[i]
        adjusted[j] = min(min_val, sorted_p[i] * n / (i + 1))
        min_val = adjusted[j]
    
    # Ensure monotonicity (adjusted p-values should not decrease as raw p-values increase)
    # The loop above does a reverse pass, but we need to ensure forward monotonicity too
    # Re-sort back to original order and enforce monotonicity
    # Actually, the standard algorithm ensures monotonicity if done correctly in reverse
    # But let's double check:
    # We need to ensure adjusted[i] <= adjusted[i+1] if sorted_p[i] <= sorted_p[i+1]
    # The reverse loop already handles this by taking min with previous (which is larger index)
    
    return adjusted

def run_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run disproportionality analysis on the cleaned dataframe.
    """
    logger.info("Starting disproportionality analysis...")
    
    # Check memory
    if not check_memory_usage(limit_gb=MEMORY_LIMITS["analysis"]):
        raise MemoryError("Memory limit exceeded during analysis.")
    
    # Get unique SOCs
    socs = df['SOC'].unique()
    results = []
    
    for soc in socs:
        # Check memory periodically
        if not check_memory_usage(limit_gb=MEMORY_LIMITS["analysis"]):
            raise MemoryError("Memory limit exceeded during analysis loop.")
        
        # Count total reports for this SOC
        total_reports = len(df[df['SOC'] == soc])
        
        # Skip if < 5 reports
        if total_reports < 5:
            continue
        
        a, b, c, d = build_contingency_table(df, soc)
        metrics = calculate_disproportionality_metrics(a, b, c, d)
        metrics['soc'] = soc
        metrics['total_reports'] = total_reports
        results.append(metrics)
    
    if not results:
        logger.warning("No SOCs met the minimum report threshold (>=5).")
        return pd.DataFrame()
    
    df_results = pd.DataFrame(results)
    
    # Apply Benjamini-Hochberg correction
    p_raw = df_results['p_raw'].tolist()
    p_adj = benjamini_hochberg(p_raw)
    df_results['p_adj'] = p_adj
    
    # Apply 2-out-of-3 rule
    # ROR > 2.0 AND ROR_CI_LOWER > 1.0
    # PRR > 1.5 AND PRR_CI_LOWER > 1.0
    # IC > 0 AND IC_CI_LOWER > 0
    
    cond_ror = (df_results['ror'] > THRESHOLDS['ror_min']) & (df_results['ror_ci_lower'] > THRESHOLDS['ror_ci_min'])
    cond_prr = (df_results['prr'] > THRESHOLDS['prr_min']) & (df_results['prr_ci_lower'] > THRESHOLDS['prr_ci_min'])
    cond_ic = (df_results['ic'] > THRESHOLDS['ic_min']) & (df_results['ic_ci_lower'] > THRESHOLDS['ic_ci_min'])
    
    # 2-out-of-3: at least 2 conditions must be true
    df_results['signal_flag'] = (cond_ror.astype(int) + cond_prr.astype(int) + cond_ic.astype(int)) >= 2
    
    # Sort by signal_flag (True first) and then by p_adj
    df_results = df_results.sort_values(by=['signal_flag', 'p_adj'], ascending=[False, True])
    
    return df_results

def main():
    """Entry point for analysis."""
    ensure_dirs()
    
    # Load cleaned data
    input_file = Path("data/processed/cleaned_vaers.parquet")
    if not input_file.exists():
        logger.error("Cleaned data not found. Run cleaning first.")
        return 1
    
    df = pd.read_parquet(input_file)
    
    # Run analysis
    try:
        results_df = run_analysis(df)
    except MemoryError as e:
        logger.error(str(e))
        return 1
    
    if results_df.empty:
        logger.warning("No signals detected.")
        # Create empty output
        results_df = pd.DataFrame(columns=['soc', 'ror', 'ror_ci_lower', 'ror_ci_upper', 'prr', 'prr_ci_lower', 'prr_ci_upper', 'ic', 'ic_ci_lower', 'ic_ci_upper', 'p_adj', 'signal_flag'])
    
    # Save output
    output_file = Path("output/signals.csv")
    results_df.to_csv(output_file, index=False)
    logger.info(f"Saved signals to {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())