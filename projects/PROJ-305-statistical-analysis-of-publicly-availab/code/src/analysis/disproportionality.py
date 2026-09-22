import os
import sys
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

# Import logging configuration from main if available, otherwise setup basic
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import from config for background rates if needed in future, though T024 focuses on calculation
# from src.utils.config import KNOWN_BACKGROUND_RATES  # Available in T004

def apply_continuity_correction(count: float) -> float:
    """Apply 0.5 continuity correction to prevent division by zero."""
    return count + 0.5

def build_contingency_table(df: pd.DataFrame, soc_code: str, target_group: str = "COVID-19") -> Dict[str, int]:
    """
    Build a 2x2 contingency table for a specific SOC and group.
    
    Returns:
        dict: {
            'a': events in target group,
            'b': non-events in target group,
            'c': events in reference group,
            'd': non-events in reference group
        }
    """
    # Filter for the specific SOC
    soc_df = df[df['SOC_CODE'] == soc_code]
    
    # Target group counts (a + b)
    target_df = soc_df[soc_df['VAX_TYPE'] == target_group]
    a = len(target_df) # Events in target (since we filtered by SOC, all are events for this SOC)
    # We need total target group size from the full dataset to calculate 'b' (non-events)
    # However, the standard approach for ROR/PRR in this context usually compares 
    # the proportion of the specific event (SOC) in Target vs Reference.
    # So:
    # a = count of SOC in Target
    # c = count of SOC in Reference
    # b = Total Target - a
    # d = Total Reference - c
    
    # Let's get total counts per group from the full dataframe passed in
    # Assuming df contains only the cleaned data for the analysis period
    total_target = len(df[df['VAX_TYPE'] == target_group])
    total_ref = len(df[df['VAX_TYPE'] != target_group]) # Assuming binary split or we need specific ref group
    
    # If the dataframe is pre-filtered to just the two groups of interest:
    if 'VAX_TYPE' in df.columns:
        # Count occurrences of SOC in target
        a = len(soc_df[soc_df['VAX_TYPE'] == target_group])
        # Count occurrences of SOC in reference (non-target)
        c = len(soc_df[soc_df['VAX_TYPE'] != target_group])
        
        b = total_target - a
        d = total_ref - c
    else:
        raise ValueError("DataFrame must contain 'VAX_TYPE' column")
        
    return {'a': a, 'b': b, 'c': c, 'd': d}

def calculate_ror(a: float, b: float, c: float, d: float) -> float:
    """Calculate Reporting Odds Ratio: (a/b) / (c/d) = (a*d) / (b*c)"""
    if b == 0 or c == 0:
        return float('nan')
    return (a * d) / (b * c)

def calculate_prr(a: float, b: float, c: float, d: float) -> float:
    """Calculate Proportional Reporting Ratio: (a/(a+b)) / (c/(c+d))"""
    if (a + b) == 0 or (c + d) == 0:
        return float('nan')
    p1 = a / (a + b)
    p2 = c / (c + d)
    if p2 == 0:
        return float('nan')
    return p1 / p2

def calculate_ic(a: float, b: float, c: float, d: float) -> float:
    """Calculate Information Component: log2( (a/(a+b)) / (a+c)/(a+b+c+d) )"""
    total = a + b + c + d
    if total == 0 or (a + b) == 0 or (a + c) == 0:
        return float('nan')
    observed = a / (a + b)
    expected = (a + c) / total
    if expected == 0:
        return float('nan')
    return math.log2(observed / expected)

def calculate_ci_ror(a: float, b: float, c: float, d: float, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate 95% Confidence Interval for ROR using Wald method on log scale."""
    if a == 0 or b == 0 or c == 0 or d == 0:
        # With continuity correction applied before, this shouldn't happen, but handle safely
        return (float('nan'), float('nan'))
    
    # Log(ROR)
    log_ror = math.log((a * d) / (b * c))
    
    # Standard Error of log(ROR)
    se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    
    z = 1.96 if confidence == 0.95 else 1.645 # Default to 95%
    
    lower = math.exp(log_ror - z * se)
    upper = math.exp(log_ror + z * se)
    
    return (lower, upper)

def calculate_ci_prr(a: float, b: float, c: float, d: float, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate 95% Confidence Interval for PRR."""
    if (a + b) == 0 or (c + d) == 0:
        return (float('nan'), float('nan'))
    
    p1 = a / (a + b)
    p2 = c / (c + d)
    
    if p1 == 0 or p2 == 0:
        return (float('nan'), float('nan'))
        
    log_prr = math.log(p1 / p2)
    se = math.sqrt((1 - p1) / (a * p1) + (1 - p2) / (c * p2))
    
    z = 1.96 if confidence == 0.95 else 1.645
    
    lower = math.exp(log_prr - z * se)
    upper = math.exp(log_prr + z * se)
    
    return (lower, upper)

def calculate_ci_ic(a: float, b: float, c: float, d: float, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate 95% Confidence Interval for IC using bootstrap approximation or delta method."""
    # Simplified delta method for IC CI
    # IC = log2( (a/(a+b)) / ( (a+c)/N ) )
    # Variance approx: Var(IC) = 1/(a * ln(2)^2) * (1 - a/(a+b) + a/(a+b) * (a+c)/N * (1 - (a+c)/N) ... simplified)
    # A common approximation for IC CI is: IC +/- 2 * SE, where SE = 1 / sqrt(a) * 1/ln(2)
    
    if a == 0:
        return (float('nan'), float('nan'))
        
    ic_val = calculate_ic(a, b, c, d)
    if math.isnan(ic_val):
        return (float('nan'), float('nan'))
        
    # Approximation: SE = 1 / (sqrt(a) * ln(2))
    se = 1.0 / (math.sqrt(a) * math.log(2))
    
    z = 1.96 if confidence == 0.95 else 1.645
    
    lower = ic_val - z * se
    upper = ic_val + z * se
    
    return (lower, upper)

def calculate_p_value_chi2(a: float, b: float, c: float, d: float) -> float:
    """Calculate p-value for Chi-squared test of independence."""
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
        
    e_a = (row1 * col1) / n
    e_b = (row1 * col2) / n
    e_c = (row2 * col1) / n
    e_d = (row2 * col2) / n
    
    if e_a == 0 or e_b == 0 or e_c == 0 or e_d == 0:
        return 1.0
        
    chi2 = ((a - e_a)**2 / e_a) + ((b - e_b)**2 / e_b) + ((c - e_c)**2 / e_c) + ((d - e_d)**2 / e_d)
    
    # P-value for Chi-squared with 1 degree of freedom
    # Using approximation or math.erfc
    # p = 1 - CDF(chi2)
    # For 1 df, p = erfc(sqrt(chi2/2))
    p_val = math.erfc(math.sqrt(chi2 / 2))
    
    return p_val

def calculate_disproportionality_metrics(a: float, b: float, c: float, d: float) -> Dict[str, Any]:
    """Calculate all disproportionality metrics for a 2x2 table."""
    ror = calculate_ror(a, b, c, d)
    prr = calculate_prr(a, b, c, d)
    ic = calculate_ic(a, b, c, d)
    
    ci_ror = calculate_ci_ror(a, b, c, d)
    ci_prr = calculate_ci_prr(a, b, c, d)
    ci_ic = calculate_ci_ic(a, b, c, d)
    
    p_val = calculate_p_value_chi2(a, b, c, d)
    
    return {
        'ror': ror,
        'prr': prr,
        'ic': ic,
        'ror_ci_lower': ci_ror[0],
        'ror_ci_upper': ci_ror[1],
        'prr_ci_lower': ci_prr[0],
        'prr_ci_upper': ci_prr[1],
        'ic_ci_lower': ci_ic[0],
        'ic_ci_upper': ci_ic[1],
        'p_value': p_val
    }

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []
        
    # Sort p-values with indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]
    
    adjusted = [0.0] * n
    current_min = 1.0
    
    # Iterate backwards
    for i in range(n - 1, -1, -1):
        rank = i + 1
        # BH formula: p * n / rank
        adj_val = sorted_p[i] * n / rank
        current_min = min(current_min, adj_val)
        adjusted[sorted_indices[i]] = current_min
        
    return adjusted

def run_analysis(df: pd.DataFrame, target_group: str = "COVID-19") -> pd.DataFrame:
    """
    Run disproportionality analysis on the dataframe.
    
    Args:
        df: Cleaned DataFrame with 'SOC_CODE' and 'VAX_TYPE' columns.
        target_group: The vaccine group to compare against others.
        
    Returns:
        DataFrame with metrics for each SOC.
    """
    logger.info(f"Starting disproportionality analysis for group: {target_group}")
    
    # Filter for valid SOCs and groups
    valid_df = df[df['SOC_CODE'].notna() & (df['SOC_CODE'] != '')]
    
    # Count reports per SOC
    soc_counts = valid_df.groupby('SOC_CODE').size().reset_index(name='count')
    
    # Filter SOCs with >= 5 reports
    valid_socs = soc_counts[soc_counts['count'] >= 5]['SOC_CODE'].tolist()
    logger.info(f"Analyzing {len(valid_socs)} SOCs with >= 5 reports")
    
    results = []
    
    for soc in valid_socs:
        table = build_contingency_table(valid_df, soc, target_group)
        metrics = calculate_disproportionality_metrics(
            table['a'], table['b'], table['c'], table['d']
        )
        metrics['SOC_CODE'] = soc
        metrics['total_reports'] = table['a'] + table['c']
        results.append(metrics)
        
    if not results:
        logger.warning("No SOCs met the minimum report threshold.")
        return pd.DataFrame()
        
    result_df = pd.DataFrame(results)
    
    # Apply Benjamini-Hochberg correction
    p_values = result_df['p_value'].tolist()
    adjusted_p = benjamini_hochberg(p_values)
    result_df['adjusted_p'] = adjusted_p
    
    return result_df

def main():
    """Main entry point for running the analysis."""
    # Load cleaned data
    data_path = Path("data/processed/cleaned_vaers.parquet")
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
        
    df = pd.read_parquet(data_path)
    
    # Run analysis
    results_df = run_analysis(df)
    
    if results_df.empty:
        logger.warning("No results generated.")
        return
        
    # Save results
    output_path = Path("output/signals.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Analysis complete. Results saved to {output_path}")

if __name__ == "__main__":
    main()
