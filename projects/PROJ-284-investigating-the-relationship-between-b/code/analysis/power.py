"""
Power analysis and confidence interval calculations for correlation studies.

Implements:
- Detectable effect size (r) calculation for achieved N at 80% power (α=0.05, FDR corrected).
- Confidence interval calculation for observed correlations.
"""
from __future__ import annotations

import os
import math
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
    fdr_adjusted_alpha: Optional[float] = None,
    alternative: str = "two-sided"
) -> float:
    """
    Calculate the minimum detectable effect size (Pearson r) for a given sample size
    at a specified power level, accounting for FDR correction if provided.
    
    This replaces the spec's FR-008 "post-hoc power analysis" per the Implementation
    Plan's approved technical strategy.
    
    Args:
        n: Sample size (number of subjects).
        power: Desired statistical power (default 0.80).
        alpha: Significance level (default 0.05).
        fdr_adjusted_alpha: Optional FDR-corrected alpha threshold. If provided,
            this overrides the standard `alpha` for the calculation.
        alternative: Type of test ("two-sided", "greater", "less").
            
    Returns:
        The minimum detectable Pearson correlation coefficient (r).
        
    Raises:
        ValueError: If n is too small or power/alpha are out of bounds.
    """
    if n < 3:
        raise ValueError(f"Sample size n={n} is too small for power analysis (min 3).")
    if not (0 < power < 1):
        raise ValueError(f"Power must be between 0 and 1, got {power}.")
    if not (0 < alpha < 1):
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}.")

    # Use FDR-adjusted alpha if provided, otherwise use standard alpha
    effective_alpha = fdr_adjusted_alpha if fdr_adjusted_alpha is not None else alpha

    # Degrees of freedom
    df = n - 2

    # Critical t-value for the given alpha and degrees of freedom
    # For two-sided test, split alpha
    if alternative == "two-sided":
        t_crit = stats.t.ppf(1 - (effective_alpha / 2), df)
    elif alternative == "greater":
        t_crit = stats.t.ppf(1 - effective_alpha, df)
    elif alternative == "less":
        t_crit = stats.t.ppf(effective_alpha, df)
    else:
        raise ValueError(f"Unknown alternative: {alternative}")

    # Calculate non-centrality parameter (nct) required to achieve the desired power
    # We need to find nct such that the probability of t > t_crit (or < -t_crit) equals power.
    # This is solved numerically.
    
    def power_func(nct):
        if alternative == "two-sided":
            # Probability of rejecting null given nct
            p_val = 1 - stats.nct.cdf(t_crit, df, nct) + stats.nct.cdf(-t_crit, df, nct)
        elif alternative == "greater":
            p_val = 1 - stats.nct.cdf(t_crit, df, nct)
        else: # less
            p_val = stats.nct.cdf(t_crit, df, nct)
        return p_val - power

    # Initial guess for nct based on normal approximation
    # r = sqrt(t^2 / (t^2 + df))
    # nct approx = r * sqrt(n)
    # We can use a simple root finding method
    try:
        # Use Brent's method or bisection
        # Search range: -10 to 10 usually covers reasonable effect sizes
        nct_solution = stats.brentq(power_func, -10, 10)
    except ValueError:
        # If root finding fails (e.g., power is unreachable with any r), return max possible
        # or raise a specific error
        raise ValueError(f"Could not find detectable effect size for n={n}, power={power}. "
                       "The desired power might be unattainable with any valid correlation.")

    # Convert non-centrality parameter back to effect size r
    # nct = r * sqrt(n - 2) / sqrt(1 - r^2)
    # Solving for r: r = nct / sqrt(nct^2 + df)
    r_detectable = nct_solution / math.sqrt(nct_solution**2 + df)
    
    # Ensure r is within valid bounds [-1, 1]
    r_detectable = max(-1.0, min(1.0, r_detectable))
    
    logger.info(f"Detectable effect size for n={n}, power={power:.2f}, alpha={effective_alpha:.4f}: r={r_detectable:.4f}")
    return r_detectable


def calculate_confidence_interval(
    r: float,
    n: int,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate the confidence interval for an observed Pearson correlation coefficient
    using Fisher's z-transformation.
    
    Args:
        r: Observed Pearson correlation coefficient.
        n: Sample size.
        confidence_level: Confidence level (default 0.95).
            
    Returns:
        A tuple (lower_bound, upper_bound) for the confidence interval of r.
        
    Raises:
        ValueError: If r is out of bounds or n is too small.
    """
    if not (-1.0 <= r <= 1.0):
        raise ValueError(f"Correlation r must be between -1 and 1, got {r}.")
    if n < 3:
        raise ValueError(f"Sample size n={n} is too small (min 3).")

    # Fisher's z-transformation
    # z = 0.5 * ln((1+r)/(1-r))
    # Handle edge cases where r is exactly 1 or -1
    if abs(r) == 1.0:
        # If r is exactly 1 or -1, the CI is technically [1, 1] or [-1, -1]
        # but practically, we might return a very narrow interval or handle as special case
        # For stability, we'll return the same value
        return (r, r)

    z = 0.5 * math.log((1 + r) / (1 - r))
    
    # Standard error of z
    se_z = 1.0 / math.sqrt(n - 3)
    
    # Critical z-value for the confidence level
    z_crit = stats.norm.ppf(1 - (1 - confidence_level) / 2)
    
    # Confidence interval in z-space
    z_lower = z - z_crit * se_z
    z_upper = z + z_crit * se_z
    
    # Transform back to r-space
    r_lower = (math.exp(2 * z_lower) - 1) / (math.exp(2 * z_lower) + 1)
    r_upper = (math.exp(2 * z_upper) - 1) / (math.exp(2 * z_upper) + 1)
    
    logger.info(f"95% CI for r={r:.4f}, n={n}: [{r_lower:.4f}, {r_upper:.4f}]")
    return (r_lower, r_upper)


def generate_power_analysis_report(
    correlation_results_path: str,
    output_path: str,
    fdr_alpha: Optional[float] = None,
    power_target: float = 0.80,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Generate a power analysis report based on existing correlation results.
    
    Reads correlation results, calculates detectable effect sizes for the
    achieved sample size, and computes confidence intervals for significant
    findings.
    
    Args:
        correlation_results_path: Path to the CSV file containing correlation results.
            Expected columns: 'metric_name', 'r', 'p', 'q', 'significant'.
        output_path: Path where the report CSV will be saved.
        fdr_alpha: The FDR-corrected alpha threshold used for significance.
        power_target: Target statistical power (default 0.80).
        confidence_level: Confidence level for intervals (default 0.95).
            
    Returns:
        A dictionary containing the report data and summary statistics.
    """
    logger.info(f"Generating power analysis report from {correlation_results_path}")
    
    if not os.path.exists(correlation_results_path):
        raise FileNotFoundError(f"Correlation results file not found: {correlation_results_path}")
    
    df = pd.read_csv(correlation_results_path)
    
    # Get sample size from the data (assuming all rows have the same N)
    # We infer N from the degrees of freedom if available, or assume a standard
    # For now, we'll assume the user provides the N or we extract it from context.
    # Since this is a post-hoc analysis, we need N. 
    # If not in the file, we might need to pass it or infer from other data.
    # Let's assume N is a constant for the study and we'll try to infer or default.
    # A robust implementation would require N as an input or find it in metadata.
    # For this task, we'll assume N is derived from the correlation calculation context
    # or passed explicitly. Since the function signature doesn't have N, we'll try to
    # infer it or raise an error if not obvious.
    # However, the task description implies we calculate for "achieved N".
    # Let's assume the correlation results file has a 'n' column or we can infer.
    # If not, we'll need to ask. But to be robust, let's assume we can get it from
    # the first row if available, or we need to pass it.
    # Given the constraints, let's assume the caller ensures N is known or the file has it.
    # If the file doesn't have N, we'll raise an error.
    
    if 'n' not in df.columns:
        # Try to infer from other columns or raise error
        # For now, let's assume we need to pass N explicitly or it's in the file.
        # Since the function signature is fixed by the task, we'll assume N is
        # available in the context or we raise an error.
        # To make it work, let's assume N is a global constant or passed via environment?
        # No, better to require it. But the task says "for achieved N".
        # Let's assume the correlation results were generated with a known N.
        # We'll add a check: if N is not in the file, we can't proceed.
        # However, to satisfy the task, we'll assume N is passed or inferred.
        # Let's assume the file has a 'n' column. If not, we'll try to get it from the
        # correlation calculation step (which might have written it).
        # For this implementation, we'll assume the file has 'n' or we raise an error.
        # But to be safe, let's assume N is 100 as a placeholder if not found? No, that's bad.
        # We'll raise an error if N is not found.
        raise ValueError("Sample size 'n' not found in correlation results. "
                       "Please ensure the file contains a 'n' column or pass N explicitly.")
    
    n = df['n'].iloc[0]  # Assuming constant N across subjects
    
    report_data = []
    
    for _, row in df.iterrows():
        metric = row['metric_name']
        r_val = row['r']
        p_val = row['p']
        q_val = row['q']
        is_sig = row['significant']
        
        # Calculate detectable effect size
        # Use FDR-adjusted alpha if provided, otherwise use the row's q or standard alpha
        alpha_to_use = fdr_alpha if fdr_alpha is not None else (q_val if is_sig else 0.05)
        detectable_r = calculate_detectable_effect_size(
            n=n,
            power=power_target,
            alpha=0.05, # Standard alpha for the test
            fdr_adjusted_alpha=alpha_to_use
        )
        
        # Calculate confidence interval
        ci_lower, ci_upper = calculate_confidence_interval(
            r=r_val,
            n=n,
            confidence_level=confidence_level
        )
        
        report_data.append({
            'metric_name': metric,
            'observed_r': r_val,
            'p_value': p_val,
            'fdr_q': q_val,
            'significant': is_sig,
            'sample_size': n,
            'detectable_r_80pct_power': detectable_r,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'power_analysis_notes': f"Detectable r for 80% power (α={alpha_to_use:.4f}) is {detectable_r:.4f}"
        })
    
    report_df = pd.DataFrame(report_data)
    report_df.to_csv(output_path, index=False)
    
    logger.info(f"Power analysis report saved to {output_path}")
    
    return {
        'file_path': output_path,
        'sample_size': n,
        'power_target': power_target,
        'confidence_level': confidence_level,
        'metrics_analyzed': len(report_data),
        'significant_metrics': report_df['significant'].sum(),
        'data': report_data
    }


def main():
    """
    Main entry point for power analysis.
    
    Reads correlation results from data/analysis/correlation_results.csv
    and generates a power analysis report at data/analysis/power_analysis.csv.
    """
    logger.info("Starting power analysis main")
    
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    input_path = base_dir / "data" / "analysis" / "correlation_results.csv"
    output_path = base_dir / "data" / "analysis" / "power_analysis.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        print(f"Error: Input file not found: {input_path}")
        print("Please run the correlation analysis first (T024, T025).")
        return 1
    
    try:
        # Generate report
        report = generate_power_analysis_report(
            correlation_results_path=str(input_path),
            output_path=str(output_path),
            fdr_alpha=0.05,  # Typical FDR threshold
            power_target=0.80,
            confidence_level=0.95
        )
        
        print(f"Power analysis complete.")
        print(f"Report saved to: {output_path}")
        print(f"Sample size: {report['sample_size']}")
        print(f"Metrics analyzed: {report['metrics_analyzed']}")
        print(f"Significant metrics: {report['significant_metrics']}")
        
        return 0
        
    except Exception as e:
        logger.exception(f"Power analysis failed: {e}")
        print(f"Error during power analysis: {e}")
        return 1


if __name__ == "__main__":
    exit(main())