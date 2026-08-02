import os
import sys
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np
from scipy import stats

# Import from project utils to ensure consistent thresholds and background rates
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import KNOWN_BACKGROUND_RATES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def apply_continuity_correction(count: int) -> float:
    """
    Apply continuity correction (add 0.5) to prevent division by zero.
    """
    return count + 0.5

def build_contingency_table(df: pd.DataFrame, soc_code: str) -> Dict[str, int]:
    """
    Build a 2x2 contingency table for a specific SOC.
    
    Returns:
        dict: {
            'a': COVID-19 with event,
            'b': COVID-19 without event,
            'c': Non-COVID with event,
            'd': Non-COVID without event
        }
    """
    # Filter for the specific SOC
    soc_df = df[df['SOC'] == soc_code]
    
    if soc_df.empty:
        return {'a': 0, 'b': 0, 'c': 0, 'd': 0}
    
    # Count events in COVID-19 group
    covid_events = soc_df[soc_df['VAX_TYPE'] == 'COVID-19'].shape[0]
    # Count non-events in COVID-19 group (Total COVID - Events)
    # We assume the input dataframe only contains relevant reports, 
    # so 'b' is the count of COVID reports NOT in this specific SOC row?
    # Correction: The contingency table logic in disproportionality analysis
    # usually compares the count of the specific event (SOC) vs all other events 
    # within the exposure groups.
    
    # Let's re-interpret based on standard VAERS analysis:
    # a = Count(COVID AND SOC)
    # b = Count(COVID AND NOT SOC) -> This requires the total count of COVID reports
    # c = Count(Non-COVID AND SOC)
    # d = Count(Non-COVID AND NOT SOC) -> This requires the total count of Non-COVID reports
    
    # However, the input 'df' is likely already filtered to contain only the reports 
    # of interest. If 'df' is the full cleaned dataset:
    
    total_covid = df[df['VAX_TYPE'] == 'COVID-19'].shape[0]
    total_non_covid = df[df['VAX_TYPE'] == 'Non-COVID'].shape[0]
    
    a = soc_df[soc_df['VAX_TYPE'] == 'COVID-19'].shape[0]
    c = soc_df[soc_df['VAX_TYPE'] == 'Non-COVID'].shape[0]
    
    b = total_covid - a
    d = total_non_covid - c
    
    return {'a': a, 'b': b, 'c': c, 'd': d}

def calculate_ror(a: int, b: int, c: int, d: int) -> float:
    """
    Calculate Reporting Odds Ratio (ROR).
    ROR = (a/b) / (c/d) = (a*d) / (b*c)
    """
    if b == 0 or c == 0:
        return float('inf')
    return (a * d) / (b * c)

def calculate_prr(a: int, b: int, c: int, d: int) -> float:
    """
    Calculate Proportional Reporting Ratio (PRR).
    PRR = (a / (a+c)) / (b / (b+d))
    """
    if (a + c) == 0 or (b + d) == 0:
        return float('inf')
    return (a / (a + c)) / (b / (b + d))

def calculate_ic(a: int, b: int, c: int, d: int) -> float:
    """
    Calculate Information Component (IC).
    IC = log2( (a * (a+b+c+d)) / ((a+c) * (a+b)) )
    """
    total = a + b + c + d
    if (a + c) == 0 or (a + b) == 0 or a == 0:
        return float('-inf')
    expected = ((a + c) * (a + b)) / total
    if expected == 0:
        return float('inf')
    return math.log2(a / expected)

def calculate_p_value_chi2(a: int, b: int, c: int, d: int) -> float:
    """
    Calculate p-value using Chi-square test for independence.
    """
    # Observed matrix
    observed = np.array([[a, b], [c, d]])
    try:
        chi2, p, dof, expected = stats.chi2_contingency(observed, correction=True)
        return p
    except Exception:
        return 1.0

def calculate_ci_ror(a: int, b: int, c: int, d: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for ROR.
    CI = exp( ln(ROR) +/- Z * sqrt(1/a + 1/b + 1/c + 1/d) )
    """
    if a <= 0 or b <= 0 or c <= 0 or d <= 0:
        return (float('-inf'), float('inf'))
    
    ror = calculate_ror(a, b, c, d)
    if ror <= 0:
        return (float('-inf'), float('inf'))
        
    z = stats.norm.ppf(1 - alpha / 2)
    se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    
    log_ror = math.log(ror)
    lower = math.exp(log_ror - z * se)
    upper = math.exp(log_ror + z * se)
    
    return (lower, upper)

def calculate_ci_prr(a: int, b: int, c: int, d: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for PRR.
    Using normal approximation on log scale.
    """
    if a <= 0 or b <= 0 or c <= 0 or d <= 0:
        return (float('-inf'), float('inf'))
        
    prr = calculate_prr(a, b, c, d)
    if prr <= 0:
        return (float('-inf'), float('inf'))
        
    z = stats.norm.ppf(1 - alpha / 2)
    # SE for log(PRR) = sqrt( (1/a - 1/(a+c)) + (1/b - 1/(b+d)) )
    # Simplified approximation often used: sqrt(1/a - 1/(a+c) + 1/b - 1/(b+d))
    # Or simpler: sqrt( (1/a) - (1/(a+c)) + (1/b) - (1/(b+d)) )
    
    term1 = (1/a) - (1/(a+c))
    term2 = (1/b) - (1/(b+d))
    
    if term1 < 0: term1 = 0 # Handle numerical edge cases
    if term2 < 0: term2 = 0
    
    se = math.sqrt(term1 + term2)
    
    log_prr = math.log(prr)
    lower = math.exp(log_prr - z * se)
    upper = math.exp(log_prr + z * se)
    
    return (lower, upper)

def calculate_ci_ic(a: int, b: int, c: int, d: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for IC.
    IC_025 = IC - 1.96 * SE(IC)
    SE(IC) approx 1 / sqrt(a) * log2(e) ? 
    Standard formula: SE(IC) = sqrt( (1/a) * (log2(e))^2 ) ? 
    More robust: SE(IC) = sqrt( (1/a) - (1/(a+c)) ) * log2(e) ?
    Let's use the standard WHO-UMC approximation:
    SE(IC) = sqrt( (1/a) - (1/(a+c)) ) * log2(e) is not quite right.
    Common approximation: SE(IC) = sqrt( (1/a) * (log2(e))^2 ) = log2(e)/sqrt(a)
    Actually, for IC, the variance is often approximated as 1/a * (log2(e))^2.
    Let's use: SE = sqrt(1/a) * log2(e)
    """
    if a <= 0:
        return (float('-inf'), float('inf'))
        
    ic = calculate_ic(a, b, c, d)
    if not math.isfinite(ic):
        return (float('-inf'), float('inf'))
        
    z = stats.norm.ppf(1 - alpha / 2)
    log2_e = math.log2(math.e)
    se = (1 / math.sqrt(a)) * log2_e
    
    lower = ic - z * se
    upper = ic + z * se
    
    return (lower, upper)

def calculate_disproportionality_metrics(df: pd.DataFrame, min_reports: int = 5) -> pd.DataFrame:
    """
    Calculate ROR, PRR, IC with 95% CIs for all SOCs with >= min_reports.
    
    Args:
        df: Cleaned dataframe with columns 'VAX_TYPE', 'SOC', 'REPT_DATE', etc.
        min_reports: Minimum total reports for an SOC to be included.
        
    Returns:
        DataFrame with metrics for each SOC.
    """
    logger.info(f"Calculating disproportionality metrics for SOCs with >= {min_reports} reports...")
    
    # Count total reports per SOC
    soc_counts = df.groupby('SOC').size().reset_index(name='total_reports')
    valid_socs = soc_counts[soc_counts['total_reports'] >= min_reports]['SOC'].tolist()
    
    logger.info(f"Found {len(valid_socs)} SOCs with >= {min_reports} reports.")
    
    results = []
    
    for soc in valid_socs:
        # Build contingency table
        counts = build_contingency_table(df, soc)
        a, b, c, d = counts['a'], counts['b'], counts['c'], counts['d']
        
        # Calculate metrics
        ror = calculate_ror(a, b, c, d)
        prr = calculate_prr(a, b, c, d)
        ic = calculate_ic(a, b, c, d)
        p_val = calculate_p_value_chi2(a, b, c, d)
        
        # Calculate CIs
        ci_ror = calculate_ci_ror(a, b, c, d)
        ci_prr = calculate_ci_prr(a, b, c, d)
        ci_ic = calculate_ci_ic(a, b, c, d)
        
        # Check background rate
        bg_rate_known = soc in KNOWN_BACKGROUND_RATES
        
        results.append({
            'SOC': soc,
            'total_reports': counts['a'] + counts['c'],
            'covid_reports': counts['a'],
            'non_covid_reports': counts['c'],
            'ror': ror,
            'ror_ci_lower': ci_ror[0],
            'ror_ci_upper': ci_ror[1],
            'prr': prr,
            'prr_ci_lower': ci_prr[0],
            'prr_ci_upper': ci_prr[1],
            'ic': ic,
            'ic_ci_lower': ci_ic[0],
            'ic_ci_upper': ci_ic[1],
            'p_value': p_val,
            'background_rate_known': bg_rate_known
        })
        
    result_df = pd.DataFrame(results)
    
    # Sort by p-value ascending (most significant first)
    result_df = result_df.sort_values(by='p_value', ascending=True)
    
    logger.info(f"Disproportionality analysis complete. {len(result_df)} SOCs processed.")
    return result_df

def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """
    Apply Benjamini-Hochberg FDR correction to a series of p-values.
    
    Args:
        p_values: Series of p-values.
        
    Returns:
        Series of adjusted p-values.
    """
    n = len(p_values)
    if n == 0:
        return pd.Series(dtype=float)
        
    # Sort p-values
    sorted_indices = p_values.argsort()
    sorted_p = p_values.iloc[sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p = np.zeros(n)
    for i in range(n):
        rank = i + 1
        adjusted_p[i] = sorted_p.iloc[i] * n / rank
        
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i+1])
        
    # Cap at 1.0
    adjusted_p = np.minimum(adjusted_p, 1.0)
    
    # Reorder to original indices
    final_adjusted = pd.Series(0.0, index=p_values.index)
    final_adjusted.iloc[sorted_indices] = adjusted_p
    
    return final_adjusted

def run_analysis(input_path: str, output_path: str, min_reports: int = 5) -> None:
    """
    Run the full disproportionality analysis pipeline.
    
    Args:
        input_path: Path to the cleaned CSV/Parquet file.
        output_path: Path to save the signals CSV.
        min_reports: Minimum reports threshold.
    """
    logger.info(f"Loading data from {input_path}...")
    if input_path.endswith('.parquet'):
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)
        
    # Ensure necessary columns exist
    required_cols = ['VAX_TYPE', 'SOC']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Run metrics calculation
    metrics_df = calculate_disproportionality_metrics(df, min_reports=min_reports)
    
    # Apply BH correction
    metrics_df['adjusted_p'] = benjamini_hochberg(metrics_df['p_value'])
    
    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    metrics_df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate disproportionality metrics for VAERS data.')
    parser.add_argument('--input', type=str, required=True, help='Path to cleaned data file (CSV or Parquet).')
    parser.add_argument('--output', type=str, required=True, help='Path to save signals CSV.')
    parser.add_argument('--min-reports', type=int, default=5, help='Minimum reports per SOC.')
    
    args = parser.parse_args()
    
    run_analysis(args.input, args.output, args.min_reports)

if __name__ == '__main__':
    main()