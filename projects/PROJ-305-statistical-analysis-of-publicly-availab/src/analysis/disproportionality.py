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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_continuity_correction(count: float) -> float:
    """
    Apply continuity correction (add 0.5) to a count to prevent division by zero.
    """
    return count + 0.5

def build_contingency_table(df: pd.DataFrame, soc_code: str, 
                            event_col: str = 'HAS_EVENT', 
                            group_col: str = 'VAX_GROUP') -> Tuple[int, int, int, int]:
    """
    Build a 2x2 contingency table for a specific SOC.
    
    Returns: (a, b, c, d)
      a = Events in COVID-19 group
      b = Non-events in COVID-19 group
      c = Events in Non-COVID group
      d = Non-events in Non-COVID group
    """
    # Filter for the specific SOC
    soc_df = df[df['SOC_CODE'] == soc_code]
    
    if soc_df.empty:
        return 0, 0, 0, 0

    # Count events and groups
    # a: Event=1, Group=COVID-19
    a = len(soc_df[(soc_df[event_col] == 1) & (soc_df[group_col] == 'COVID-19')])
    # b: Event=0, Group=COVID-19
    b = len(soc_df[(soc_df[event_col] == 0) & (soc_df[group_col] == 'COVID-19')])
    # c: Event=1, Group=Non-COVID
    c = len(soc_df[(soc_df[event_col] == 1) & (soc_df[group_col] == 'Non-COVID')])
    # d: Event=0, Group=Non-COVID
    d = len(soc_df[(soc_df[event_col] == 0) & (soc_df[group_col] == 'Non-COVID')])
    
    return a, b, c, d

def calculate_ror(a: float, b: float, c: float, d: float) -> Optional[float]:
    """
    Calculate Reporting Odds Ratio (ROR).
    ROR = (a/b) / (c/d) = (a*d) / (b*c)
    """
    if b == 0 or c == 0:
        return None
    return (a * d) / (b * c)

def calculate_prr(a: float, b: float, c: float, d: float) -> Optional[float]:
    """
    Calculate Proportional Reporting Ratio (PRR).
    PRR = (a / (a+b)) / (c / (c+d))
    """
    if (a + b) == 0 or (c + d) == 0:
        return None
    p1 = a / (a + b)
    p2 = c / (c + d)
    if p2 == 0:
        return None
    return p1 / p2

def calculate_ic(a: float, b: float, c: float, d: float) -> Optional[float]:
    """
    Calculate Information Component (IC).
    IC = log2( (a / (a+b)) / ( (a+c) / (a+b+c+d) ) )
    Note: This is a simplified version often used in pharmacovigilance.
    More formally: IC = log2( (a * N) / ((a+b) * (a+c)) )
    where N = a+b+c+d
    """
    n = a + b + c + d
    if n == 0 or (a + b) == 0 or (a + c) == 0:
        return None
    # Expected count under independence
    expected = ((a + b) * (a + c)) / n
    if expected == 0:
        return None
    return math.log2(a / expected)

def calculate_p_value_chi2(a: float, b: float, c: float, d: float) -> Optional[float]:
    """
    Calculate p-value using Chi-square test (with continuity correction).
    """
    if a + b + c + d == 0:
        return None
    try:
        # Use scipy chi2_contingency
        table = [[a, b], [c, d]]
        chi2, p, dof, expected = stats.chi2_contingency(table, correction=True)
        return p
    except Exception as e:
        logger.warning(f"Chi-square calculation failed: {e}")
        return None

def calculate_ci_ror(a: float, b: float, c: float, d: float, alpha: float = 0.05) -> Optional[Tuple[float, float]]:
    """
    Calculate 95% Confidence Interval for ROR.
    SE(ln ROR) = sqrt(1/a + 1/b + 1/c + 1/d)
    CI = exp( ln(ROR) +/- Z * SE )
    """
    if a == 0 or b == 0 or c == 0 or d == 0:
        return None
    try:
        ror = calculate_ror(a, b, c, d)
        if ror is None or ror <= 0:
            return None
        
        se = math.sqrt(1/a + 1/b + 1/c + 1/d)
        z = stats.norm.ppf(1 - alpha/2)
        ln_ror = math.log(ror)
        
        lower = math.exp(ln_ror - z * se)
        upper = math.exp(ln_ror + z * se)
        return (lower, upper)
    except Exception as e:
        logger.warning(f"ROR CI calculation failed: {e}")
        return None

def calculate_ci_prr(a: float, b: float, c: float, d: float, alpha: float = 0.05) -> Optional[Tuple[float, float]]:
    """
    Calculate 95% Confidence Interval for PRR.
    SE(ln PRR) = sqrt( b/(a*(a+b)) + d/(c*(c+d)) )
    """
    if a == 0 or b == 0 or c == 0 or d == 0:
        return None
    try:
        prr = calculate_prr(a, b, c, d)
        if prr is None or prr <= 0:
            return None
        
        se = math.sqrt( (b / (a * (a + b))) + (d / (c * (c + d))) )
        z = stats.norm.ppf(1 - alpha/2)
        ln_prr = math.log(prr)
        
        lower = math.exp(ln_prr - z * se)
        upper = math.exp(ln_prr + z * se)
        return (lower, upper)
    except Exception as e:
        logger.warning(f"PRR CI calculation failed: {e}")
        return None

def calculate_ci_ic(a: float, b: float, c: float, d: float, alpha: float = 0.05) -> Optional[Tuple[float, float]]:
    """
    Calculate 95% Confidence Interval for IC.
    SE(IC) = 1 / (sqrt(a) * ln(2))
    """
    if a == 0:
        return None
    try:
        ic = calculate_ic(a, b, c, d)
        if ic is None:
            return None
        
        se = 1 / (math.sqrt(a) * math.log(2))
        z = stats.norm.ppf(1 - alpha/2)
        
        lower = ic - z * se
        upper = ic + z * se
        return (lower, upper)
    except Exception as e:
        logger.warning(f"IC CI calculation failed: {e}")
        return None

def calculate_disproportionality_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate ROR, PRR, IC, and their confidence intervals for all SOCs.
    """
    logger.info("Starting disproportionality metrics calculation...")
    
    results = []
    unique_socs = df['SOC_CODE'].unique()
    total = len(unique_socs)
    
    for idx, soc in enumerate(unique_socs):
        if (idx + 1) % 50 == 0:
            logger.info(f"Processing SOC {idx+1}/{total}: {soc}")
        
        # Check minimum report count (T024 requirement: >= 5 total reports)
        # Total reports for this SOC = events + non-events in both groups
        # But effectively, we need enough data to calculate metrics.
        # We'll calculate first, then filter.
        
        a, b, c, d = build_contingency_table(df, soc)
        total_reports = a + b + c + d
        
        if total_reports < 5:
            continue

        # Apply continuity correction if any cell is 0
        # T023: Add 0.5 to zero-count cells
        a_corr = apply_continuity_correction(a) if a == 0 else a
        b_corr = apply_continuity_correction(b) if b == 0 else b
        c_corr = apply_continuity_correction(c) if c == 0 else c
        d_corr = apply_continuity_correction(d) if d == 0 else d

        ror = calculate_ror(a_corr, b_corr, c_corr, d_corr)
        prr = calculate_prr(a_corr, b_corr, c_corr, d_corr)
        ic = calculate_ic(a_corr, b_corr, c_corr, d_corr)
        p_val = calculate_p_value_chi2(a_corr, b_corr, c_corr, d_corr)
        
        ci_ror = calculate_ci_ror(a_corr, b_corr, c_corr, d_corr)
        ci_prr = calculate_ci_prr(a_corr, b_corr, c_corr, d_corr)
        ci_ic = calculate_ci_ic(a_corr, b_corr, c_corr, d_corr)

        results.append({
            'SOC_CODE': soc,
            'a': a,
            'b': b,
            'c': c,
            'd': d,
            'total_reports': total_reports,
            'ROR': ror,
            'PRR': prr,
            'IC': ic,
            'P_VALUE': p_val,
            'ROR_CI_LOWER': ci_ror[0] if ci_ror else None,
            'ROR_CI_UPPER': ci_ror[1] if ci_ror else None,
            'PRR_CI_LOWER': ci_prr[0] if ci_prr else None,
            'PRR_CI_UPPER': ci_prr[1] if ci_prr else None,
            'IC_CI_LOWER': ci_ic[0] if ci_ic else None,
            'IC_CI_UPPER': ci_ic[1] if ci_ic else None
        })
    
    return pd.DataFrame(results)

def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """
    Apply Benjamini-Hochberg FDR correction to a series of p-values.
    Returns adjusted p-values.
    """
    if p_values.empty:
        return p_values
    
    n = len(p_values)
    sorted_indices = p_values.argsort()
    sorted_p = p_values.iloc[sorted_indices]
    
    adjusted = np.zeros(n)
    for i, p in enumerate(sorted_p):
        # BH formula: p * n / rank
        rank = i + 1
        adj_p = p * n / rank
        adjusted[sorted_indices[i]] = adj_p
    
    # Ensure monotonicity (adjusted p-values should not decrease as rank increases)
    # We process from largest rank to smallest
    min_so_far = 1.0
    for i in range(n - 1, -1, -1):
        if adjusted[sorted_indices[i]] < min_so_far:
            min_so_far = adjusted[sorted_indices[i]]
        else:
            adjusted[sorted_indices[i]] = min_so_far
        
        # Cap at 1.0
        if adjusted[sorted_indices[i]] > 1.0:
            adjusted[sorted_indices[i]] = 1.0
    
    return pd.Series(adjusted, index=p_values.index)

def run_analysis(input_path: str, output_path: str) -> None:
    """
    Main entry point for running the disproportionality analysis.
    Reads cleaned data, calculates metrics, applies BH correction, and saves results.
    """
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load data
    df = pd.read_parquet(input_path) if input_path.endswith('.parquet') else pd.read_csv(input_path)
    
    # Ensure necessary columns exist
    required_cols = ['SOC_CODE', 'VAX_GROUP'] # Assuming VAX_GROUP is 'COVID-19' or 'Non-COVID'
    # The clean.py should have created a binary event column. 
    # If not present, we assume every row in the cleaned dataset is an 'event' report 
    # because the dataset is filtered to specific adverse events? 
    # Re-reading T014/T016: The clean.py filters by VAX_TYPE and maps SOC.
    # The "Event" vs "No Event" in a 2x2 table for VAERS usually implies:
    # Event = Report contains this SOC.
    # No Event = Report does NOT contain this SOC.
    # But here we are iterating per SOC.
    # Standard VAERS disproportionality:
    # a = count of reports with SOC X in COVID group
    # b = count of reports WITHOUT SOC X in COVID group (Total COVID - a)
    # c = count of reports with SOC X in Non-COVID group
    # d = count of reports WITHOUT SOC X in Non-COVID group (Total Non-COVID - c)
    
    # We need total counts per group to calculate b and d correctly.
    # The current build_contingency_table logic in this file assumes the dataframe 
    # only contains rows for the specific SOC (which is wrong for b and d).
    
    # Correction: We need the total counts of the groups.
    total_covid = len(df[df['VAX_GROUP'] == 'COVID-19'])
    total_non_covid = len(df[df['VAX_GROUP'] == 'Non-COVID'])
    
    results = []
    unique_socs = df['SOC_CODE'].unique()
    
    logger.info(f"Processing {len(unique_socs)} unique SOCs...")
    
    for idx, soc in enumerate(unique_socs):
        if (idx + 1) % 100 == 0:
            logger.info(f"Processing {idx+1}/{len(unique_socs)}")
        
        # Count reports with this SOC in each group
        a = len(df[(df['SOC_CODE'] == soc) & (df['VAX_GROUP'] == 'COVID-19')])
        c = len(df[(df['SOC_CODE'] == soc) & (df['VAX_GROUP'] == 'Non-COVID')])
        
        # Calculate b and d (Total - Event)
        b = total_covid - a
        d = total_non_covid - c
        
        total_reports = a + b + c + d # This is actually total_covid + total_non_covid
        # But the filter ">= 5 reports" usually refers to the count of the specific event (a+c).
        if (a + c) < 5:
            continue

        # Apply continuity correction
        a_corr = apply_continuity_correction(a) if a == 0 else a
        b_corr = apply_continuity_correction(b) if b == 0 else b
        c_corr = apply_continuity_correction(c) if c == 0 else c
        d_corr = apply_continuity_correction(d) if d == 0 else d

        ror = calculate_ror(a_corr, b_corr, c_corr, d_corr)
        prr = calculate_prr(a_corr, b_corr, c_corr, d_corr)
        ic = calculate_ic(a_corr, b_corr, c_corr, d_corr)
        p_val = calculate_p_value_chi2(a_corr, b_corr, c_corr, d_corr)
        
        ci_ror = calculate_ci_ror(a_corr, b_corr, c_corr, d_corr)
        ci_prr = calculate_ci_prr(a_corr, b_corr, c_corr, d_corr)
        ci_ic = calculate_ci_ic(a_corr, b_corr, c_corr, d_corr)

        results.append({
            'SOC_CODE': soc,
            'event_covid': a,
            'non_event_covid': b,
            'event_non_covid': c,
            'non_event_non_covid': d,
            'total_event_reports': a + c,
            'ROR': ror,
            'PRR': prr,
            'IC': ic,
            'P_VALUE': p_val,
            'ROR_CI_LOWER': ci_ror[0] if ci_ror else None,
            'ROR_CI_UPPER': ci_ror[1] if ci_ror else None,
            'PRR_CI_LOWER': ci_prr[0] if ci_prr else None,
            'PRR_CI_UPPER': ci_prr[1] if ci_prr else None,
            'IC_CI_LOWER': ci_ic[0] if ci_ic else None,
            'IC_CI_UPPER': ci_ic[1] if ci_ic else None
        })
    
    if not results:
        logger.warning("No results generated. Check data filters.")
        # Create empty dataframe with correct columns
        results_df = pd.DataFrame(columns=['SOC_CODE', 'ROR', 'PRR', 'IC', 'P_VALUE'])
    else:
        results_df = pd.DataFrame(results)
    
    # Apply Benjamini-Hochberg correction
    if 'P_VALUE' in results_df.columns and not results_df.empty:
        results_df['ADJ_P_VALUE'] = benjamini_hochberg(results_df['P_VALUE'])
    else:
        results_df['ADJ_P_VALUE'] = np.nan
    
    # Save results
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    results_df.to_csv(output_path, index=False)
    logger.info(f"Analysis complete. Results saved to {output_path}")

def main():
    """
    Command line entry point.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run Disproportionality Analysis")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_vaers.parquet",
                        help="Path to cleaned data (parquet or csv)")
    parser.add_argument("--output", type=str, default="output/signals.csv",
                        help="Path to output CSV")
    args = parser.parse_args()
    
    run_analysis(args.input, args.output)

if __name__ == "__main__":
    main()