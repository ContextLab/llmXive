import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def calculate_detectable_effect_size(r_values: np.ndarray, n: int, alpha: float = 0.05, power: float = 0.80) -> dict:
    """
    Calculate the detectable effect size (r) for a given sample size N at 80% power.
    
    This function performs a post-hoc power analysis to determine the minimum
    correlation coefficient that could be detected with the achieved sample size
    at the specified power level, using the FDR-corrected alpha.
    
    Parameters:
    -----------
    r_values : np.ndarray
        Array of observed correlation coefficients (r values) from the analysis.
    n : int
        The achieved sample size (number of subjects).
    alpha : float
        The significance level (default 0.05). This should be the FDR-corrected alpha.
    power : float
        The desired statistical power (default 0.80).
        
    Returns:
    --------
    dict
        Dictionary containing:
        - 'detectable_r': float, the minimum detectable effect size at given power
        - 'n': int, the sample size used
        - 'alpha': float, the significance level used
        - 'power': float, the target power
        - 'degrees_of_freedom': int, n - 2
    """
    if n < 3:
        raise ValueError("Sample size must be at least 3 for correlation power analysis")
        
    df = n - 2
    
    # Critical t-value for the given alpha and degrees of freedom
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Non-centrality parameter for the desired power
    # We need to find the non-centrality parameter (nCP) such that
    # P(t > t_crit | nCP) = power
    # This is solved iteratively or via approximation
    
    # Using the approximation: nCP ≈ t_crit + z_power
    # where z_power is the z-score for the desired power
    z_power = stats.norm.ppf(power)
    
    # Iterative solution for more accuracy
    def find_ncp(target_power, t_crit, df):
        """Find non-centrality parameter that gives target power."""
        low, high = 0, 10
        for _ in range(100):
            mid = (low + high) / 2
            # Calculate power: P(t > t_crit | ncp=mid, df)
            power_val = 1 - stats.nct.cdf(t_crit, df, mid)
            if power_val < target_power:
                low = mid
            else:
                high = mid
        return mid
    
    ncp = find_ncp(power, t_crit, df)
    
    # Convert ncp to detectable r
    # ncp = r * sqrt((n-2) / (1-r^2))
    # Solving for r: r = ncp / sqrt(ncp^2 + df)
    detectable_r = ncp / np.sqrt(ncp**2 + df)
    
    return {
        'detectable_r': float(detectable_r),
        'n': n,
        'alpha': alpha,
        'power': power,
        'degrees_of_freedom': df,
        'ncp': float(ncp)
    }

def generate_power_analysis_report(correlation_results: pd.DataFrame, n_subjects: int, 
                                  output_path: Path, alpha_fdr: float = 0.05) -> None:
    """
    Generate a power analysis report based on correlation results.
    
    Parameters:
    -----------
    correlation_results : pd.DataFrame
        DataFrame containing correlation results with columns:
        - 'metric_name': name of the metric
        - 'r': correlation coefficient
        - 'p': p-value
        - 'q': FDR-corrected p-value (q-value)
        - 'significant': boolean indicating significance
    n_subjects : int
        Number of subjects in the analysis
    output_path : Path
        Path to save the power analysis report (CSV)
    alpha_fdr : float
        FDR-corrected alpha level (default 0.05)
    """
    logger.info(f"Generating power analysis report for {n_subjects} subjects")
    
    # Calculate detectable effect size for the achieved sample size
    power_info = calculate_detectable_effect_size(
        r_values=correlation_results['r'].values,
        n=n_subjects,
        alpha=alpha_fdr,
        power=0.80
    )
    
    # Create report DataFrame
    report_data = {
        'metric_name': correlation_results['metric_name'],
        'observed_r': correlation_results['r'],
        'observed_p': correlation_results['p'],
        'observed_q': correlation_results['q'],
        'significant': correlation_results['significant'],
        'detectable_r_at_80pct_power': [power_info['detectable_r']] * len(correlation_results),
        'sample_size': [n_subjects] * len(correlation_results),
        'alpha_level': [power_info['alpha']] * len(correlation_results),
        'power_target': [power_info['power']] * len(correlation_results)
    }
    
    report_df = pd.DataFrame(report_data)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save report
    report_df.to_csv(output_path, index=False)
    logger.info(f"Power analysis report saved to {output_path}")
    
    # Log summary
    logger.info(f"Sample size: {n_subjects}")
    logger.info(f"Alpha level (FDR corrected): {power_info['alpha']}")
    logger.info(f"Detectable effect size (r) at 80% power: {power_info['detectable_r']:.4f}")
    
    # Count how many observed effects are above detectable threshold
    significant_above_threshold = report_df[
        (report_df['significant']) & 
        (report_df['observed_r'].abs() >= report_df['detectable_r_at_80pct_power'])
    ]
    
    logger.info(f"Significant correlations above detectable threshold: {len(significant_above_threshold)}")

def main():
    """
    Main function to run power analysis on correlation results.
    """
    logger.info("Starting power analysis for correlation results")
    
    # Load configuration
    config = get_config()
    
    # Define paths
    base_dir = Path(config.get('DATA_DIR', 'data'))
    analysis_dir = base_dir / 'analysis'
    output_path = analysis_dir / 'power_analysis_report.csv'
    
    # Load correlation results
    correlation_file = analysis_dir / 'correlation_results.csv'
    if not correlation_file.exists():
        logger.error(f"Correlation results file not found: {correlation_file}")
        logger.error("Please run correlation analysis (T024) before power analysis")
        return
        
    correlation_results = pd.read_csv(correlation_file)
    
    # Get sample size from the data
    # Assuming we have subject-level data in full_metrics.csv
    metrics_file = analysis_dir / 'full_metrics.csv'
    if metrics_file.exists():
        full_metrics = pd.read_csv(metrics_file)
        n_subjects = len(full_metrics['subject_id'].unique())
    else:
        # Fallback: estimate from correlation results if we have enough info
        # This is less accurate but handles edge cases
        n_subjects = len(correlation_results) + 2  # Rough estimate
        logger.warning(f"Could not determine exact sample size, using estimate: {n_subjects}")
    
    # Run power analysis
    generate_power_analysis_report(
        correlation_results=correlation_results,
        n_subjects=n_subjects,
        output_path=output_path,
        alpha_fdr=0.05  # Using standard FDR alpha, could be adjusted
    )
    
    logger.info("Power analysis completed successfully")

if __name__ == "__main__":
    main()