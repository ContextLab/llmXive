import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np

from analyzer import load_coverage_reports, pair_llm_human_results, run_statistical_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_sensitivity_analysis(
    coverage_dir: Path,
    output_path: Path,
    thresholds: List[float] = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25]
) -> pd.DataFrame:
    """
    Perform sensitivity analysis across specified p-value thresholds.
    
    This function evaluates the stability of statistical conclusions (significant vs 
    non-significant) as the significance threshold varies. As per FR-011, these 
    thresholds are explicitly excluded from family-wise error correction.
    
    Args:
        coverage_dir: Path to directory containing coverage reports.
        output_path: Path where the sensitivity_report.csv will be written.
        thresholds: List of significance thresholds to test.
        
    Returns:
        DataFrame containing sensitivity analysis results.
    """
    logger.info(f"Starting sensitivity analysis with thresholds: {thresholds}")
    
    # Load and pair data
    reports = load_coverage_reports(coverage_dir)
    paired_data = pair_llm_human_results(reports)
    
    if not paired_data:
        logger.error("No paired data found for sensitivity analysis.")
        # Create empty report with correct schema
        df = pd.DataFrame(columns=['threshold', 'significant_count', 'non_significant_count', 
                                   'total_pairs', 'significance_rate'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        return df
    
    # Calculate differences for paired data
    differences = []
    for item in paired_data:
        llm_cov = item.get('llm_line_coverage', 0)
        human_cov = item.get('human_line_coverage', 0)
        if llm_cov is not None and human_cov is not None:
            diff = llm_cov - human_cov
            # Estimate standard error (simplified: using absolute diff as proxy for variability in this context)
            # In a full implementation, we would use the actual standard deviation of the differences
            # Here we assume a fixed variance for the sensitivity check on the mean difference
            # We'll simulate a t-statistic calculation based on the mean difference
            differences.append(diff)
    
    if not differences:
        logger.warning("No valid differences found.")
        df = pd.DataFrame(columns=['threshold', 'significant_count', 'non_significant_count', 
                                   'total_pairs', 'significance_rate'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        return df

    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)
    n = len(differences)
    std_err = std_diff / np.sqrt(n) if n > 0 else 1.0
    
    # Calculate t-statistic
    t_stat = mean_diff / std_err if std_err != 0 else 0.0
    
    # Calculate degrees of freedom
    df_val = n - 1 if n > 1 else 0
    
    results = []
    
    for threshold in thresholds:
        # Calculate p-value for the observed t-statistic
        # Using survival function (1 - CDF) and multiplying by 2 for two-tailed test
        from scipy import stats
        
        if df_val <= 0:
            p_value = 1.0
        else:
            # Two-tailed p-value
            p_value = 2 * stats.t.sf(np.abs(t_stat), df_val)
        
        is_significant = 1 if p_value < threshold else 0
        
        results.append({
            'threshold': threshold,
            'p_value': p_value,
            't_statistic': t_stat,
            'mean_difference': mean_diff,
            'std_error': std_err,
            'sample_size': n,
            'is_significant': is_significant,
            'conclusion': 'Significant' if is_significant else 'Not Significant'
        })
    
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df_results.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
    
    return df_results

def main():
    """Entry point for running sensitivity analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run sensitivity analysis on coverage data.')
    parser.add_argument('--coverage-dir', type=str, default='data/coverage_reports',
                        help='Directory containing coverage reports')
    parser.add_argument('--output', type=str, default='data/processed/sensitivity_report.csv',
                        help='Output path for sensitivity report CSV')
    parser.add_argument('--thresholds', type=str, default='0.01,0.05,0.10,0.15,0.20,0.25',
                        help='Comma-separated list of significance thresholds')
    
    args = parser.parse_args()
    
    coverage_dir = Path(args.coverage_dir)
    output_path = Path(args.output)
    thresholds = [float(t.strip()) for t in args.thresholds.split(',')]
    
    if not coverage_dir.exists():
        logger.error(f"Coverage directory not found: {coverage_dir}")
        return 1
    
    run_sensitivity_analysis(coverage_dir, output_path, thresholds)
    return 0

if __name__ == '__main__':
    exit(main())
