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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/disproportionality.log')
    ]
)
logger = logging.getLogger(__name__)

def apply_continuity_correction(count: int) -> float:
    """
    Apply continuity correction (add 0.5) to a count to prevent division by zero.
    """
    return float(count) + 0.5

def build_contingency_table(df: pd.DataFrame, soc_code: str) -> Dict[str, int]:
    """
    Build a 2x2 contingency table for a specific SOC.
    
    Columns:
    - a: COVID-19 reports with the SOC
    - b: Full Non-COVID reports with the SOC
    - c: COVID-19 reports without the SOC
    - d: Full Non-COVID reports without the SOC
    
    The input dataframe MUST contain 'VAX_TYPE' and 'SOC_CODE' columns.
    'VAX_TYPE' should be 'COVID-19' or 'Non-COVID' (as per T015/T016 cleaning).
    """
    # Filter for the specific SOC
    soc_mask = df['SOC_CODE'] == soc_code
    
    # Group counts
    covid_with_soc = len(df[(df['VAX_TYPE'] == 'COVID-19') & soc_mask])
    noncovid_with_soc = len(df[(df['VAX_TYPE'] == 'Non-COVID') & soc_mask])
    
    covid_total = len(df[df['VAX_TYPE'] == 'COVID-19'])
    noncovid_total = len(df[df['VAX_TYPE'] == 'Non-COVID'])
    
    a = covid_with_soc
    b = noncovid_with_soc
    c = covid_total - covid_with_soc
    d = noncovid_total - noncovid_with_soc
    
    return {'a': a, 'b': b, 'c': c, 'd': d}

def calculate_ror(a: float, b: float, c: float, d: float) -> Optional[float]:
    """
    Calculate Reporting Odds Ratio (ROR).
    ROR = (a/c) / (b/d) = (a*d) / (b*c)
    """
    if b * c == 0:
        return None
    return (a * d) / (b * c)

def calculate_prr(a: float, b: float, c: float, d: float) -> Optional[float]:
    """
    Calculate Proportional Reporting Ratio (PRR).
    PRR = (a / (a+c)) / (b / (b+d))
    """
    if (a + c) == 0 or (b + d) == 0:
        return None
    return (a / (a + c)) / (b / (b + d))

def calculate_ic(a: float, b: float, c: float, d: float) -> Optional[float]:
    """
    Calculate Information Component (IC).
    IC = log2( (a * (a+b+c+d)) / ((a+c) * (a+b)) )
    """
    n = a + b + c + d
    if n == 0 or (a + c) == 0 or (a + b) == 0:
        return None
    expected = ((a + c) * (a + b)) / n
    if expected == 0:
        return None
    return math.log2(a / expected)

def calculate_ci_ror(a: float, b: float, c: float, d: float) -> Optional[Tuple[float, float]]:
    """
    Calculate 95% Confidence Interval for ROR.
    CI = exp( ln(ROR) ± 1.96 * sqrt(1/a + 1/b + 1/c + 1/d) )
    """
    ror = calculate_ror(a, b, c, d)
    if ror is None or ror <= 0:
        return None
    
    se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    ln_ror = math.log(ror)
    lower = math.exp(ln_ror - 1.96 * se)
    upper = math.exp(ln_ror + 1.96 * se)
    return (lower, upper)

def calculate_ci_prr(a: float, b: float, c: float, d: float) -> Optional[Tuple[float, float]]:
    """
    Calculate 95% Confidence Interval for PRR.
    CI = exp( ln(PRR) ± 1.96 * sqrt(1/a - 1/(a+c) + 1/b - 1/(b+d)) )
    """
    prr = calculate_prr(a, b, c, d)
    if prr is None or prr <= 0:
        return None
    
    try:
        se = math.sqrt((1/a) - (1/(a+c)) + (1/b) - (1/(b+d)))
        ln_prr = math.log(prr)
        lower = math.exp(ln_prr - 1.96 * se)
        upper = math.exp(ln_prr + 1.96 * se)
        return (lower, upper)
    except (ValueError, ZeroDivisionError):
        return None

def calculate_ci_ic(a: float, b: float, c: float, d: float) -> Optional[Tuple[float, float]]:
    """
    Calculate 95% Confidence Interval for IC.
    CI = IC ± 1.96 * SE(IC)
    SE(IC) ≈ sqrt(1/a - 1/(a+c) + 1/b - 1/(b+d)) (approximation using binomial variance)
    Note: Exact SE for IC is complex; using standard approximation.
    """
    ic = calculate_ic(a, b, c, d)
    if ic is None:
        return None
    
    try:
        # Approximation for SE of IC
        term1 = (1/a) - (1/(a+c)) if (a+c) > 0 else 0
        term2 = (1/b) - (1/(b+d)) if (b+d) > 0 else 0
        if term1 < 0: term1 = 0
        if term2 < 0: term2 = 0
        se = math.sqrt(term1 + term2)
        
        lower = ic - 1.96 * se
        upper = ic + 1.96 * se
        return (lower, upper)
    except (ValueError, ZeroDivisionError):
        return None

def calculate_p_value_chi2(a: float, b: float, c: float, d: float) -> Optional[float]:
    """
    Calculate p-value using Chi-squared test (approximation).
    Chi2 = (ad - bc)^2 * (a+b+c+d) / ((a+b)(c+d)(a+c)(b+d))
    """
    n = a + b + c + d
    if n == 0:
        return None
    
    numerator = (a * d - b * c) ** 2 * n
    denominator = (a + b) * (c + d) * (a + c) * (b + d)
    
    if denominator == 0:
        return None
    
    chi2 = numerator / denominator
    
    # Approximate p-value from Chi2 with 1 degree of freedom
    # Using standard normal approximation for large chi2 or lookup
    # For simplicity, we use a basic approximation or scipy if available
    # Since we want to avoid heavy deps, we use a simple approximation:
    # p ≈ exp(-chi2/2) is a very rough lower bound for large chi2
    # Better: use scipy.stats if available, else return None or approx
    try:
        import scipy.stats as stats
        return stats.chi2.sf(chi2, 1)
    except ImportError:
        # Fallback: rough approximation for p-value (not exact)
        # If chi2 > 3.84, p < 0.05. We return a placeholder or None.
        # For strict compliance, we should have scipy.
        # Given requirements.txt includes scipy, we assume it's there.
        # If not, we raise an error or return None.
        return None

def calculate_disproportionality_metrics(a: float, b: float, c: float, d: float) -> Dict[str, Any]:
    """
    Calculate all disproportionality metrics for a single SOC.
    """
    # Apply continuity correction to counts
    a_corr = apply_continuity_correction(a)
    b_corr = apply_continuity_correction(b)
    c_corr = apply_continuity_correction(c)
    d_corr = apply_continuity_correction(d)
    
    ror = calculate_ror(a_corr, b_corr, c_corr, d_corr)
    prr = calculate_prr(a_corr, b_corr, c_corr, d_corr)
    ic = calculate_ic(a_corr, b_corr, c_corr, d_corr)
    
    ror_ci = calculate_ci_ror(a_corr, b_corr, c_corr, d_corr)
    prr_ci = calculate_ci_prr(a_corr, b_corr, c_corr, d_corr)
    ic_ci = calculate_ci_ic(a_corr, b_corr, c_corr, d_corr)
    
    p_val = calculate_p_value_chi2(a_corr, b_corr, c_corr, d_corr)
    
    return {
        'ror': ror,
        'ror_ci_lower': ror_ci[0] if ror_ci else None,
        'ror_ci_upper': ror_ci[1] if ror_ci else None,
        'prr': prr,
        'prr_ci_lower': prr_ci[0] if prr_ci else None,
        'prr_ci_upper': prr_ci[1] if prr_ci else None,
        'ic': ic,
        'ic_ci_lower': ic_ci[0] if ic_ci else None,
        'ic_ci_upper': ic_ci[1] if ic_ci else None,
        'p_value': p_val
    }

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    Returns adjusted p-values.
    """
    if not p_values:
        return []
    
    n = len(p_values)
    # Sort p-values with indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    adjusted = [0.0] * n
    rank = n
    min_val = 1.0
    
    # Iterate backwards
    for i in range(n - 1, -1, -1):
        p = sorted_p_values[i]
        adjusted_p = p * n / (i + 1)
        if adjusted_p > min_val:
            adjusted_p = min_val
        min_val = adjusted_p
        adjusted[sorted_indices[i]] = min_val
        
    return adjusted

def run_analysis(input_path: str, output_dir: str) -> pd.DataFrame:
    """
    Run the full disproportionality analysis.
    
    1. Load cleaned data (Full Non-COVID + COVID-19).
    2. Group by SOC_CODE.
    3. Filter SOCs with >= 5 total reports.
    4. Calculate metrics for each SOC.
    5. Apply Benjamini-Hochberg correction.
    6. Apply 2-out-of-3 rule to flag signals.
    7. Return DataFrame with results.
    """
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    
    # Ensure columns exist
    required_cols = ['VAX_TYPE', 'SOC_CODE']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Filter valid VAX_TYPE
    valid_types = ['COVID-19', 'Non-COVID']
    df = df[df['VAX_TYPE'].isin(valid_types)]
    
    # Group by SOC and count
    soc_counts = df.groupby('SOC_CODE').size().reset_index(name='total_count')
    valid_soc_mask = soc_counts['total_count'] >= 5
    valid_soc_codes = soc_counts[valid_soc_mask]['SOC_CODE'].tolist()
    
    logger.info(f"Found {len(valid_soc_codes)} SOCs with >= 5 reports")
    
    results = []
    
    for soc in valid_soc_codes:
        table = build_contingency_table(df, soc)
        metrics = calculate_disproportionality_metrics(
            table['a'], table['b'], table['c'], table['d']
        )
        metrics['soc'] = soc
        metrics['total_reports'] = table['a'] + table['b'] + table['c'] + table['d']
        metrics['covid_reports'] = table['a'] + table['c']
        metrics['noncovid_reports'] = table['b'] + table['d']
        metrics['background_rate_status'] = 'UNKNOWN'
        results.append(metrics)
    
    if not results:
        logger.warning("No valid SOCs found for analysis.")
        return pd.DataFrame()
    
    df_results = pd.DataFrame(results)
    
    # Apply Benjamini-Hochberg correction
    p_values = df_results['p_value'].dropna().tolist()
    if p_values:
        adjusted_p = benjamini_hochberg(p_values)
        # Map back to dataframe (only for rows with valid p_value)
        # Create a mapping
        valid_indices = df_results['p_value'].dropna().index
        for idx, adj_val in zip(valid_indices, adjusted_p):
            df_results.loc[idx, 'p_adj'] = adj_val
        # Fill NaN for rows without p_value
        df_results['p_adj'] = df_results['p_adj'].fillna(1.0)
    else:
        df_results['p_adj'] = 1.0
    
    # Apply 2-out-of-3 rule
    # ROR > 2.0 AND CI lower > 1.0
    # PRR > 1.5 AND CI lower > 1.0
    # IC > 0 AND CI lower > 0
    
    ror_cond = (df_results['ror'] > THRESHOLDS['ror_min']) & (df_results['ror_ci_lower'] > THRESHOLDS['ror_ci_min'])
    prr_cond = (df_results['prr'] > THRESHOLDS['prr_min']) & (df_results['prr_ci_lower'] > THRESHOLDS['prr_ci_min'])
    ic_cond = (df_results['ic'] > THRESHOLDS['ic_min']) & (df_results['ic_ci_lower'] > THRESHOLDS['ic_ci_min'])
    
    # Count how many conditions are met
    met_count = ror_cond.astype(int) + prr_cond.astype(int) + ic_cond.astype(int)
    df_results['signal_flag'] = met_count >= 2
    
    logger.info(f"Analysis complete. {df_results['signal_flag'].sum()} signals detected.")
    
    return df_results

def main():
    """
    Main entry point for T022.
    """
    # Paths
    input_file = Path("data/processed/cleaned_vaers_full_non_covid.parquet")
    output_dir = Path("output")
    output_file = output_dir / "signals.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        df_results = run_analysis(str(input_file), str(output_dir))
        
        if df_results.empty:
            logger.warning("No results to write.")
            return
        
        # Save to CSV
        df_results.to_csv(output_file, index=False)
        logger.info(f"Results saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
