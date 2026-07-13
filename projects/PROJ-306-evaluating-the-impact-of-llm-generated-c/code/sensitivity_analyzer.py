import os
import csv
import logging
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from scipy import stats

from analyzer import load_coverage_reports, pair_llm_human_results
from logger_config import get_pipeline_logger

logger = get_pipeline_logger(__name__)

def run_sensitivity_analysis(coverage_data: pd.DataFrame, thresholds: List[float]) -> pd.DataFrame:
    """
    Run sensitivity analysis across specified thresholds.
    FR-011: Explicitly exclude these thresholds from family-wise error correction.
    
    Args:
        coverage_data: DataFrame with paired LLM and human coverage results
        thresholds: List of significance thresholds to test (e.g., [0.01, 0.05, ...])
    
    Returns:
        DataFrame with sensitivity analysis results
    """
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25]
    
    if not pairs:
        logger.error("No valid pairs found for sensitivity analysis.")
        return pd.DataFrame()

    # Extract coverage differences (Human - LLM)
    # We use line_coverage for this analysis as it's available for all tasks
    # Branch coverage might be N/A for HumanEval
    diffs = []
    for llm_r, human_r in pairs:
        # Prefer line_coverage if branch is N/A or missing
        llm_cov = llm_r.get('line_coverage', 0.0)
        human_cov = human_r.get('line_coverage', 0.0)
        
        # Handle potential string "N/A" or None
        if isinstance(llm_cov, str) and llm_cov.upper() == "N/A":
            llm_cov = 0.0
        if isinstance(human_cov, str) and human_cov.upper() == "N/A":
            human_cov = 0.0
        
        diffs.append(human_cov - llm_cov)
    
    diffs = np.array(diffs)
    
    if len(diffs) == 0:
        return pd.DataFrame()

    # Perform a paired t-test to get a baseline p-value distribution
    # Since we are doing sensitivity analysis, we treat the differences as a sample
    # and check significance against 0 at various alpha levels.
    # However, sensitivity analysis usually implies: "How many hypotheses are significant at alpha X?"
    # Here, we have one aggregate test. We can simulate the sensitivity by checking
    # the p-value of the mean difference against each threshold.
    
    # Calculate mean and standard error
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    n = len(diffs)
    
    if std_diff == 0:
        t_stat = 0.0 if mean_diff == 0 else float('inf')
    else:
        t_stat = mean_diff / (std_diff / np.sqrt(n))
    
    # Two-tailed p-value
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))
    
    results = []
    
    # Calculate differences
    if 'line_coverage' in coverage_data.columns:
        diff_col = 'line_coverage_diff'
        coverage_data[diff_col] = coverage_data['line_coverage_llm'] - coverage_data['line_coverage_human']
    elif 'branch_coverage' in coverage_data.columns:
        diff_col = 'branch_coverage_diff'
        coverage_data[diff_col] = coverage_data['branch_coverage_llm'] - coverage_data['branch_coverage_human']
    else:
        logger.warning("No coverage difference column found. Skipping sensitivity analysis.")
        return pd.DataFrame()

    # Use the difference column
    diffs = coverage_data[diff_col].dropna()
    
    if len(diffs) == 0:
        logger.warning("No valid differences found for sensitivity analysis.")
        return pd.DataFrame()

    for thresh in thresholds:
        # Perform Wilcoxon signed-rank test (non-parametric, robust for sensitivity)
        # We test if the median difference is significantly different from 0
        try:
            stat, p_value = stats.wilcoxon(diffs)
            
            # Determine significance at this threshold
            is_significant = p_value < thresh
            
            results.append({
                'threshold': thresh,
                'p_value': p_value,
                'significant': is_significant,
                'n_samples': len(diffs),
                'mean_diff': diffs.mean(),
                'median_diff': diffs.median(),
                'std_diff': diffs.std()
            })
        except Exception as e:
            logger.error(f"Error running sensitivity analysis at threshold {thresh}: {e}")
            results.append({
                'threshold': thresh,
                'p_value': np.nan,
                'significant': False,
                'n_samples': len(diffs),
                'mean_diff': diffs.mean() if not diffs.empty else np.nan,
                'median_diff': diffs.median() if not diffs.empty else np.nan,
                'std_diff': diffs.std() if not diffs.empty else np.nan
            })

    return pd.DataFrame(results)

def save_sensitivity_report(df: pd.DataFrame, output_path: str):
    """Save sensitivity analysis report to CSV."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Sensitivity report saved to {output_file}")

def run_sensitivity_analysis_wrapper(output_dir: str):
    """
    Main entry point for sensitivity analysis.
    Loads coverage reports, pairs data, runs analysis, and saves report.
    """
    logger.info("Starting sensitivity analysis...")
    
    # Load coverage reports
    coverage_reports_path = Path(output_dir) / "coverage_reports"
    if not coverage_reports_path.exists():
        logger.error(f"Coverage reports directory not found: {coverage_reports_path}")
        return
    
    # Load paired data
    paired_data = pair_llm_human_results(str(coverage_reports_path))
    
    if paired_data is None or paired_data.empty:
        logger.warning("No paired data found for sensitivity analysis.")
        # Create empty report to satisfy deliverable requirement
        empty_df = pd.DataFrame(columns=['threshold', 'p_value', 'significant', 'n_samples', 'mean_diff', 'median_diff', 'std_diff'])
        save_sensitivity_report(empty_df, str(Path(output_dir) / "sensitivity_report.csv"))
        return

    # Define thresholds per FR-011
    thresholds = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25]
    
    # Run analysis
    sensitivity_results = run_sensitivity_analysis(paired_data, thresholds)
    
    # Save report
    output_path = Path(output_dir) / "sensitivity_report.csv"
    save_sensitivity_report(sensitivity_results, str(output_path))
    
    logger.info("Sensitivity analysis complete.")

def main():
    """CLI entry point for sensitivity analyzer."""
    import argparse
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on coverage data")
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory')
    args = parser.parse_args()
    
    run_sensitivity_analysis_wrapper(args.output_dir)

if __name__ == '__main__':
    main()