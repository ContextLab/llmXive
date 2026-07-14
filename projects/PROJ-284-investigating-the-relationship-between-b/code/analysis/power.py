"""
Power analysis module.
Implements T026.

Calculates detectable effect size for achieved sample size at 80% power.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

from code.logging_config import get_logger

logger = get_logger(__name__)

def calculate_detectable_effect_size(
    n: int, 
    power: float = 0.80, 
    alpha: float = 0.05, 
    tail: int = 2
) -> float:
    """
    Calculate the minimum detectable effect size (r) for a given sample size.
    
    Args:
        n: Sample size
        power: Desired statistical power (default 0.80)
        alpha: Significance level (default 0.05)
        tail: 1 for one-tailed, 2 for two-tailed (default 2)
        
    Returns:
        Minimum detectable Pearson correlation coefficient (r)
    """
    if n < 3:
        logger.log("calculate_detectable_effect_size", error="Sample size too small")
        return float('nan')
    
    # Degrees of freedom
    df = n - 2
    
    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # We need to find r such that the power (probability of rejecting H0) equals the target power.
    # Under H1 (correlation = r), the test statistic follows a non-central t-distribution
    # with non-centrality parameter (ncp) = r * sqrt((n-2) / (1-r^2)).
    # Power = P(|T| > t_crit | ncp) = 1 - (CDF(t_crit) - CDF(-t_crit))
    
    # Binary search for r
    r_low, r_high = 0.0, 0.999
    tolerance = 1e-5
    max_iter = 100
    iter_count = 0
    
    while r_high - r_low > tolerance and iter_count < max_iter:
        r_mid = (r_low + r_high) / 2
        if r_mid < 1e-10: # Avoid division by zero if r is essentially 0
            ncp = 0.0
        else:
            ncp = r_mid * np.sqrt(df / (1 - r_mid**2))
        
        # Calculate power: P(T > t_crit) + P(T < -t_crit)
        # CDF of non-central t
        cdf_high = stats.nct.cdf(t_crit, df, ncp)
        cdf_low = stats.nct.cdf(-t_crit, df, ncp)
        
        power_est = (1 - cdf_high) + cdf_low
        
        if power_est < power:
            r_low = r_mid
        else:
            r_high = r_mid
        
        iter_count += 1
    
    return (r_low + r_high) / 2

def generate_power_analysis_report(
    correlations_df: pd.DataFrame,
    output_path: str
) -> str:
    """
    Generate a power analysis report based on correlation results.
    
    Args:
        correlations_df: DataFrame with correlation results including 'n' column
        output_path: Path to save the report
        
    Returns:
        Formatted power analysis report string
    """
    if correlations_df.empty:
        report = "No correlation data available for power analysis."
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
        return report
    
    # Determine sample size N.
    # Prefer explicit 'n' column, otherwise infer from row count.
    if 'n' in correlations_df.columns:
        # Use the median or mode if multiple subjects have different N (unlikely here)
        # or just the first value if consistent.
        n_est = int(correlations_df['n'].iloc[0])
    else:
        # Infer N from the number of rows if each row is a subject
        n_est = len(correlations_df)
    
    if n_est < 3:
        report = f"Sample size (N={n_est}) is too small for power analysis."
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
        return report
        
    # Calculate detectable effect size
    detectable_r = calculate_detectable_effect_size(n_est, power=0.80, alpha=0.05)
    
    report_lines = [
        "# Power Analysis Report",
        "",
        f"**Sample Size (N)**: {n_est}",
        f"**Target Power**: 80%",
        f"**Significance Level (α)**: 0.05",
        f"**FDR Correction Applied**: Yes (assumed for context)",
        "",
        "## Detectable Effect Size",
        "",
        f"With N={n_est}, the minimum detectable correlation coefficient (r) at 80% power "
        f"is approximately **{detectable_r:.3f}** (two-tailed, α=0.05).",
        "",
        "## Interpretation",
        "",
        f"- Correlations with |r| > {detectable_r:.3f} are likely to be detected as significant with 80% power.",
        f"- Correlations with |r| < {detectable_r:.3f} may be underpowered and require larger sample sizes.",
        "",
        "## Notes",
        "",
        "- This analysis assumes a simple correlation test. FDR correction reduces effective power.",
        "- The actual detectable effect size may vary depending on the number of comparisons and FDR threshold."
    ]
    
    report = "\n".join(report_lines)
    
    # Write to file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.log(
        "generate_power_analysis_report",
        status="success",
        n=n_est,
        detectable_r=detectable_r,
        output_path=output_path
    )
    
    return report

def main() -> None:
    """Main entry point for power analysis."""
    corr_path = Path("data/analysis/correlations.csv")
    output_path = Path("data/analysis/power_analysis.txt")
    
    if not corr_path.exists():
        logger.log("power_main", status="error", message=f"Correlation data not found at {corr_path}")
        print(f"Error: Correlation data not found at {corr_path}")
        # Create empty report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write("Power analysis could not be performed: correlation data not found.")
        return
    
    try:
        df = pd.read_csv(corr_path)
        report = generate_power_analysis_report(df, str(output_path))
        print(f"Power analysis report generated at {output_path}")
        print(report)
    except Exception as e:
        logger.log("power_main", status="error", message=f"Power analysis failed: {e}")
        print(f"Error in power analysis: {e}")
        # Fallback
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(f"Power analysis failed: {str(e)}")

if __name__ == "__main__":
    main()