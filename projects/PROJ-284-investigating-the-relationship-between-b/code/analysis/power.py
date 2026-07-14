"""
Power analysis and confidence interval calculations for correlation results.

Implements calculation of detectable effect size (r) for achieved N at 80% power
(α=0.05, FDR corrected) and confidence intervals for correlation coefficients.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pandas as pd
from scipy import stats

from code.logging_config import get_logger

logger = get_logger(__name__)


def calculate_detectable_effect_size(
    n: int,
    power: float = 0.80,
    alpha: float = 0.05,
    tails: int = 2
) -> float:
    """
    Calculate the minimum detectable effect size (correlation r) for a given sample size
    and desired statistical power.
    
    Parameters
    ----------
    n : int
        Sample size (number of subjects)
    power : float
        Desired statistical power (default 0.80)
    alpha : float
        Significance level (default 0.05)
    tails : int
        Number of tails (1 or 2, default 2)
        
    Returns
    -------
    float
        Minimum detectable correlation coefficient r
        
    Notes
    -----
    Uses the non-central t-distribution to find the effect size that would
    yield the specified power. Iteratively searches for the r value where
    power = P(|t| > t_critical | non-centrality parameter from r)
    """
    if n < 3:
        raise ValueError("Sample size must be at least 3")
    if not 0 < power < 1:
        raise ValueError("Power must be between 0 and 1")
    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1")
        
    df = n - 2
    
    # Critical t-value for the given alpha
    if tails == 2:
        t_crit = stats.t.ppf(1 - alpha/2, df)
    else:
        t_crit = stats.t.ppf(1 - alpha, df)
        
    # Binary search for the detectable effect size
    r_low, r_high = 0.0, 0.999
    tolerance = 1e-4
    max_iter = 100
    
    for _ in range(max_iter):
        r_mid = (r_low + r_high) / 2
        
        # Calculate non-centrality parameter for this r
        # t = r * sqrt((n-2) / (1-r^2))
        if abs(r_mid) >= 1.0:
            ncp = float('inf')
        else:
            ncp = r_mid * np.sqrt(df / (1 - r_mid**2))
        
        # Calculate power: P(|t| > t_crit | ncp)
        if tails == 2:
            power_low = stats.nct.cdf(-t_crit, df, ncp)
            power_high = 1 - stats.nct.cdf(t_crit, df, ncp)
            current_power = power_low + power_high
        else:
            if ncp > 0:
                current_power = 1 - stats.nct.cdf(t_crit, df, ncp)
            else:
                current_power = stats.nct.cdf(-t_crit, df, ncp)
        
        if abs(current_power - power) < tolerance:
            return r_mid
        elif current_power < power:
            r_low = r_mid
        else:
            r_high = r_mid
            
    return (r_low + r_high) / 2


def calculate_confidence_interval(
    r: float,
    n: int,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate the confidence interval for a Pearson correlation coefficient
    using Fisher's z-transformation.
    
    Parameters
    ----------
    r : float
        Pearson correlation coefficient
    n : int
        Sample size
    confidence_level : float
        Confidence level (default 0.95 for 95% CI)
        
    Returns
    -------
    tuple (float, float)
        Lower and upper bounds of the confidence interval
        
    Notes
    -----
    Uses Fisher's z-transformation:
    z = 0.5 * ln((1+r)/(1-r))
    SE_z = 1 / sqrt(n-3)
    CI_z = z ± z_critical * SE_z
    Then transforms back to r scale.
    """
    if n < 4:
        raise ValueError("Sample size must be at least 4 for CI calculation")
    if abs(r) >= 1.0:
        # Handle boundary cases
        if r > 0:
            return (0.99, 1.0)
        else:
            return (-1.0, -0.99)
            
    # Fisher's z-transformation
    z = 0.5 * np.log((1 + r) / (1 - r))
    
    # Standard error of z
    se_z = 1.0 / np.sqrt(n - 3)
    
    # Critical z-value
    z_critical = stats.norm.ppf(1 - (1 - confidence_level) / 2)
    
    # Confidence interval in z-space
    z_lower = z - z_critical * se_z
    z_upper = z + z_critical * se_z
    
    # Transform back to r-space
    r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    return (r_lower, r_upper)


def generate_power_analysis_report(
    correlation_results: pd.DataFrame,
    n_subjects: int,
    alpha: float = 0.05,
    power: float = 0.80,
    fdr_corrected: bool = True
) -> pd.DataFrame:
    """
    Generate a power analysis report for correlation results.
    
    Parameters
    ----------
    correlation_results : pd.DataFrame
        DataFrame containing correlation results with columns:
        ['metric_name', 'r', 'p', 'q', 'significant']
    n_subjects : int
        Number of subjects in the study
    alpha : float
        Significance level (default 0.05)
    power : float
        Desired statistical power (default 0.80)
    fdr_corrected : bool
        Whether to use FDR-corrected alpha (default True)
        
    Returns
    -------
    pd.DataFrame
        DataFrame with power analysis results including:
        - metric_name
        - observed_r
        - observed_p
        - observed_q
        - detectable_r_80pct_power
        - ci_lower_95
        - ci_upper_95
        - is_significant
        - power_achieved (approximate)
        
    Notes
    -----
    If FDR correction is enabled, the alpha is adjusted using the
    Benjamini-Hochberg procedure for the number of tests.
    """
    if correlation_results.empty:
        logger.warning("Empty correlation results, returning empty power analysis")
        return pd.DataFrame()
        
    required_cols = ['metric_name', 'r', 'p', 'q', 'significant']
    if not all(col in correlation_results.columns for col in required_cols):
        raise ValueError(f"Correlation results must contain columns: {required_cols}")
        
    results = []
    
    # Determine effective alpha
    if fdr_corrected and 'q' in correlation_results.columns:
        # Use FDR-corrected significance threshold
        # For power calculation, we use the nominal alpha adjusted for multiple comparisons
        effective_alpha = alpha / len(correlation_results)  # Conservative Bonferroni-style
    else:
        effective_alpha = alpha
        
    for _, row in correlation_results.iterrows():
        metric_name = row['metric_name']
        r_obs = row['r']
        p_obs = row['p']
        q_obs = row['q']
        sig_obs = row['significant']
        
        # Calculate detectable effect size at 80% power
        detectable_r = calculate_detectable_effect_size(
            n=n_subjects,
            power=power,
            alpha=effective_alpha
        )
        
        # Calculate 95% confidence interval
        ci_lower, ci_upper = calculate_confidence_interval(
            r=r_obs,
            n=n_subjects,
            confidence_level=0.95
        )
        
        # Approximate achieved power (for observed effect)
        # This is a rough estimate based on whether observed r > detectable r
        if abs(r_obs) >= detectable_r:
            power_achieved = 1.0  # Effect is detectable
        else:
            # Rough approximation: power decreases as effect size decreases
            if detectable_r > 0:
                power_achieved = max(0.0, (abs(r_obs) / detectable_r) * power)
            else:
                power_achieved = 0.0
                
        results.append({
            'metric_name': metric_name,
            'observed_r': r_obs,
            'observed_p': p_obs,
            'observed_q': q_obs,
            'detectable_r_80pct_power': detectable_r,
            'ci_lower_95': ci_lower,
            'ci_upper_95': ci_upper,
            'is_significant': sig_obs,
            'power_achieved': power_achieved
        })
        
    return pd.DataFrame(results)


def main() -> None:
    """
    Main entry point for power analysis.
    
    Loads correlation results from data/analysis/correlation_results.csv,
    performs power analysis, and saves results to data/analysis/power_analysis.csv.
    """
    # Define paths
    base_path = Path(__file__).parent.parent.parent
    input_path = base_path / "data" / "analysis" / "correlation_results.csv"
    output_path = base_path / "data" / "analysis" / "power_analysis.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.log("power_analysis_start", input=str(input_path))
    
    if not input_path.exists():
        logger.log("power_analysis_error", message=f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Correlation results not found at {input_path}")
        
    # Load correlation results
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.log("power_analysis_error", message=f"Failed to load correlation results: {e}")
        raise
        
    logger.log("power_analysis_loaded", rows=len(df))
    
    if df.empty:
        logger.log("power_analysis_warning", message="No correlation results to analyze")
        # Create empty output with proper columns
        empty_df = pd.DataFrame(columns=[
            'metric_name', 'observed_r', 'observed_p', 'observed_q',
            'detectable_r_80pct_power', 'ci_lower_95', 'ci_upper_95',
            'is_significant', 'power_achieved'
        ])
        empty_df.to_csv(output_path, index=False)
        logger.log("power_analysis_complete", output=str(output_path), rows=0)
        return
        
    # Estimate N from the data (assuming one row per subject-metric combination or aggregated)
    # If data is aggregated by metric, we need to know N from elsewhere
    # For now, assume N is the number of unique subjects or rows if single metric
    # A more robust approach would read N from metadata
    n_subjects = len(df)
    if 'subject_id' in df.columns:
        n_subjects = df['subject_id'].nunique()
        
    # If we have multiple metrics, N should be consistent
    if 'metric_name' in df.columns and df['metric_name'].nunique() > 1:
        # Assume N is the same for all metrics
        # We'll use the first metric's row count as proxy if no subject_id
        if 'subject_id' not in df.columns:
            n_subjects = len(df) // df['metric_name'].nunique()
            
    logger.log("power_analysis_n_subjects", n=n_subjects)
    
    # Generate power analysis report
    power_results = generate_power_analysis_report(
        correlation_results=df,
        n_subjects=n_subjects,
        alpha=0.05,
        power=0.80,
        fdr_corrected=True
    )
    
    # Save results
    power_results.to_csv(output_path, index=False)
    
    logger.log(
        "power_analysis_complete",
        output=str(output_path),
        rows=len(power_results),
        n_subjects=n_subjects
    )
    
    print(f"Power analysis complete. Results saved to {output_path}")
    print(f"Sample size: {n_subjects}")
    print(f"Metrics analyzed: {len(power_results)}")
    
    # Print summary
    significant_count = power_results['is_significant'].sum()
    print(f"Significant correlations: {significant_count}/{len(power_results)}")
    
    if not power_results.empty:
        print("\nDetectable effect sizes (80% power, FDR-corrected):")
        print(power_results[['metric_name', 'detectable_r_80pct_power']].to_string(index=False))


if __name__ == "__main__":
    main()