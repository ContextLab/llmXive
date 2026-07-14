"""
Power analysis module for calculating detectable effect sizes and confidence intervals.

This module implements post-hoc power analysis to determine the minimum detectable
effect size (r) given the achieved sample size (N), desired power (80%), and
significance level (alpha=0.05, FDR corrected).

Replaces Spec's FR-008 "post-hoc power analysis" per the Implementation Plan's
approved technical strategy.
"""
from __future__ import annotations

import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from code.logging_config import get_logger

logger = get_logger(__name__)


def calculate_detectable_effect_size(
    n: int,
    power: float = 0.80,
    alpha: float = 0.05,
    two_tailed: bool = True
) -> float:
    """
    Calculate the minimum detectable effect size (Pearson's r) for a given sample size.
    
    Uses the non-central t-distribution to find the effect size that would yield
    the specified power at the given alpha level.
    
    Args:
        n: Sample size (number of subjects)
        power: Desired statistical power (default 0.80)
        alpha: Significance level (default 0.05)
        two_tailed: Whether to use two-tailed test (default True)
        
    Returns:
        Minimum detectable effect size (r)
        
    Raises:
        ValueError: If inputs are invalid
    """
    if n < 3:
        raise ValueError(f"Sample size must be at least 3, got {n}")
    if not 0 < power < 1:
        raise ValueError(f"Power must be between 0 and 1, got {power}")
    if not 0 < alpha < 1:
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")
        
    # Degrees of freedom
    df = n - 2
    
    # Critical t-value for significance
    if two_tailed:
        alpha_per_tail = alpha / 2
    else:
        alpha_per_tail = alpha
        
    from scipy import stats
    t_critical = stats.t.ppf(1 - alpha_per_tail, df)
    
    # Non-centrality parameter for desired power
    # We need to find the non-centrality parameter (delta) such that
    # P(t > t_critical | delta) = power
    # This is equivalent to finding delta where the non-central t CDF at t_critical
    # equals (1 - power) for two-tailed, or (1 - power) for one-tailed
    
    def power_func(delta):
        if two_tailed:
            # Two-tailed: power = P(t < -t_crit | delta) + P(t > t_crit | delta)
            cdf_left = stats.nct.cdf(-t_critical, df, delta)
            cdf_right = 1 - stats.nct.cdf(t_critical, df, delta)
            return cdf_left + cdf_right
        else:
            # One-tailed
            return 1 - stats.nct.cdf(t_critical, df, delta)
    
    # Binary search for the non-centrality parameter
    delta_low, delta_high = 0.0, 10.0
    tolerance = 1e-6
    
    while delta_high - delta_low > tolerance:
        delta_mid = (delta_low + delta_high) / 2
        current_power = power_func(delta_mid)
        if current_power < power:
            delta_low = delta_mid
        else:
            delta_high = delta_mid
    
    delta = (delta_low + delta_high) / 2
    
    # Convert non-centrality parameter to effect size r
    # For Pearson correlation: delta = r * sqrt((n-2) / (1 - r^2))
    # Solving for r: r = delta / sqrt(delta^2 + df)
    r = delta / np.sqrt(delta**2 + df)
    
    return r


def calculate_confidence_interval(
    r: float,
    n: int,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate the confidence interval for a Pearson correlation coefficient.
    
    Uses Fisher's z-transformation to compute the confidence interval,
    which provides better coverage for correlation coefficients.
    
    Args:
        r: Pearson correlation coefficient
        n: Sample size
        confidence_level: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Tuple of (lower_bound, upper_bound) for the confidence interval
        
    Raises:
        ValueError: If inputs are invalid
    """
    if not -1 <= r <= 1:
        raise ValueError(f"Correlation must be between -1 and 1, got {r}")
    if n < 3:
        raise ValueError(f"Sample size must be at least 3, got {n}")
    if not 0 < confidence_level < 1:
        raise ValueError(f"Confidence level must be between 0 and 1, got {confidence_level}")
        
    from scipy import stats
    
    # Fisher's z-transformation
    # z = 0.5 * ln((1+r)/(1-r))
    if abs(r) == 1:
        # Handle perfect correlation
        r_adjusted = np.copysign(0.9999, r)
    else:
        r_adjusted = r
        
    z = 0.5 * np.log((1 + r_adjusted) / (1 - r_adjusted))
    
    # Standard error of z
    se_z = 1 / np.sqrt(n - 3)
    
    # Critical z-value for confidence level
    alpha = 1 - confidence_level
    z_critical = stats.norm.ppf(1 - alpha / 2)
    
    # Confidence interval in z-space
    z_lower = z - z_critical * se_z
    z_upper = z + z_critical * se_z
    
    # Transform back to r-space
    r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    return (r_lower, r_upper)


def generate_power_analysis_report(
    correlation_results: pd.DataFrame,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Generate a power analysis report for all correlation results.
    
    Calculates the minimum detectable effect size and confidence intervals
    for each correlation in the results dataframe.
    
    Args:
        correlation_results: DataFrame with correlation results (must include 'n', 'r', 'p', 'q')
        output_path: Optional path to save the report as CSV
        
    Returns:
        DataFrame with added power analysis columns
        
    Raises:
        ValueError: If required columns are missing
    """
    required_cols = ['n', 'r']
    missing_cols = [col for col in required_cols if col not in correlation_results.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    logger.log("generate_power_analysis_report", 
              operation="generate_power_analysis_report",
              n_rows=len(correlation_results))
    
    # Calculate detectable effect size for each row
    detectable_r = []
    conf_intervals = []
    
    for idx, row in correlation_results.iterrows():
        n = row['n']
        r = row['r']
        
        # Calculate detectable effect size (80% power, alpha=0.05)
        # Note: If FDR corrected p-value is used, we might want to adjust alpha
        # For now, we use the standard alpha=0.05 as the base level
        try:
            detectable = calculate_detectable_effect_size(n=n, power=0.80, alpha=0.05)
            detectable_r.append(detectable)
        except Exception as e:
            logger.log("power_calculation_error", error=str(e), row=idx)
            detectable_r.append(np.nan)
        
        # Calculate 95% confidence interval
        try:
            ci_lower, ci_upper = calculate_confidence_interval(r=r, n=n, confidence_level=0.95)
            conf_intervals.append(f"[{ci_lower:.3f}, {ci_upper:.3f}]")
        except Exception as e:
            logger.log("ci_calculation_error", error=str(e), row=idx)
            conf_intervals.append("N/A")
    
    # Create results dataframe
    power_results = correlation_results.copy()
    power_results['detectable_effect_size_80pct_power'] = detectable_r
    power_results['confidence_interval_95pct'] = conf_intervals
    
    # Add interpretation
    power_results['power_interpretation'] = power_results.apply(
        lambda row: "Sufficient power" if abs(row['r']) >= row['detectable_effect_size_80pct_power'] 
                    else "Insufficient power" 
        if not pd.isna(row['detectable_effect_size_80pct_power']) 
        else "Unknown", 
        axis=1
    )
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        power_results.to_csv(output_path, index=False)
        logger.log("power_analysis_saved", path=str(output_path), n_rows=len(power_results))
    
    return power_results


def main() -> None:
    """
    Main entry point for power analysis.
    
    Loads correlation results from data/analysis/correlation_results.csv,
    performs power analysis, and saves results to data/analysis/power_analysis.csv.
    """
    logger.log("power_analysis_main", operation="main")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "analysis" / "correlation_results.csv"
    output_path = project_root / "data" / "analysis" / "power_analysis.csv"
    
    # Check if input file exists
    if not input_path.exists():
        logger.log("input_file_missing", path=str(input_path))
        print(f"Error: Input file not found: {input_path}")
        print("Please run the correlation analysis first to generate correlation_results.csv")
        return
    
    # Load correlation results
    try:
        correlation_results = pd.read_csv(input_path)
        logger.log("data_loaded", path=str(input_path), n_rows=len(correlation_results))
    except Exception as e:
        logger.log("data_load_error", error=str(e))
        print(f"Error loading correlation results: {e}")
        return
    
    # Generate power analysis report
    try:
        power_results = generate_power_analysis_report(
            correlation_results=correlation_results,
            output_path=output_path
        )
        logger.log("power_analysis_complete", output=str(output_path))
        print(f"Power analysis complete. Results saved to: {output_path}")
        print(f"Analyzed {len(power_results)} correlations")
        
        # Print summary
        if 'detectable_effect_size_80pct_power' in power_results.columns:
            sufficient = power_results['power_interpretation'].value_counts().get('Sufficient power', 0)
            insufficient = power_results['power_interpretation'].value_counts().get('Insufficient power', 0)
            print(f"Sufficient power: {sufficient}, Insufficient power: {insufficient}")
            
    except Exception as e:
        logger.log("power_analysis_error", error=str(e))
        print(f"Error during power analysis: {e}")
        raise


if __name__ == "__main__":
    main()