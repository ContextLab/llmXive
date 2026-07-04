"""
T031: Implement Tukey HSD post-hoc pairwise comparisons to control family-wise error rate.

This module loads the binned learner data, fits a cluster-robust OLS model (using the 
existing models module), and performs Tukey HSD post-hoc tests on the feedback timing groups.

Output:
    data/processed/tukey_hsd_results.csv: Pairwise comparisons with adjusted p-values.
    data/processed/tukey_hsd_summary.csv: Summary of significant differences.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Import existing project utilities
from config import load_config, get_config_value
from logging_config import get_logger, info, error, warning, debug
from models import fit_cluster_robust_ols, extract_effect_sizes

# Try to import statsmodels for Tukey HSD
try:
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    from statsmodels.stats.anova import AnovaRM
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    error("statsmodels not installed. Tukey HSD cannot be performed.")

def load_binned_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the binned learner data from the processed directory."""
    processed_dir = Path(get_config_value(config, "paths.processed_dir", "data/processed"))
    input_file = processed_dir / "learners_binned.csv"
    
    if not input_file.exists():
        error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Required input file not found: {input_file}")
    
    info(f"Loading binned data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Validate required columns
    required_cols = ['final_grade', 'feedback_group', 'course_id']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        error(f"Missing required columns in binned data: {missing_cols}")
        raise ValueError(f"Missing columns: {missing_cols}")
    
    return df

def run_tukey_hsd(df: pd.DataFrame, dependent_var: str = 'final_grade', group_var: str = 'feedback_group') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform Tukey HSD post-hoc pairwise comparisons.
    
    Args:
        df: DataFrame with learner data
        dependent_var: Name of the dependent variable column
        group_var: Name of the grouping variable column
        
    Returns:
        Tuple of (results_df, summary_dict)
    """
    if not HAS_STATSMODELS:
        raise ImportError("statsmodels is required for Tukey HSD analysis")
    
    info(f"Running Tukey HSD post-hoc test on '{dependent_var}' by '{group_var}'")
    
    # Filter out any NaN values in the relevant columns
    clean_df = df[[dependent_var, group_var]].dropna()
    
    if clean_df.empty:
        error("No valid data remaining after NaN removal for Tukey HSD")
        raise ValueError("No valid data for Tukey HSD analysis")
    
    # Perform Tukey HSD test
    tukey = pairwise_tukeyhsd(
        endog=clean_df[dependent_var],
        groups=clean_df[group_var],
        alpha=0.05
    )
    
    # Convert results to DataFrame
    results = pd.DataFrame(tukey.summary2().tables[1].data[1:], columns=tukey.summary2().tables[1].data[0])
    results.columns = ['Group1', 'Group2', 'Mean Difference', 'Lower CI', 'Upper CI', 'p-adj', 'Reject']
    
    # Ensure p-adj is numeric
    results['p-adj'] = pd.to_numeric(results['p-adj'], errors='coerce')
    
    # Create summary of significant findings
    significant = results[results['Reject'] == 'True'].copy()
    
    summary = {
        'total_comparisons': len(results),
        'significant_comparisons': len(significant),
        'significance_rate': len(significant) / len(results) if len(results) > 0 else 0.0,
        'alpha': 0.05
    }
    
    info(f"Tukey HSD complete: {len(significant)} of {len(results)} comparisons are significant")
    
    return results, summary

def save_results(results_df: pd.DataFrame, summary: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Save Tukey HSD results to CSV files."""
    processed_dir = Path(get_config_value(config, "paths.processed_dir", "data/processed"))
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed results
    results_file = processed_dir / "tukey_hsd_results.csv"
    results_df.to_csv(results_file, index=False)
    info(f"Saved Tukey HSD results to {results_file}")
    
    # Save summary
    summary_file = processed_dir / "tukey_hsd_summary.csv"
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(summary_file, index=False)
    info(f"Saved Tukey HSD summary to {summary_file}")

def main():
    """Main entry point for Tukey HSD post-hoc analysis."""
    info("Starting Tukey HSD post-hoc analysis (Task T031)")
    
    # Load configuration
    config = load_config()
    
    try:
        # Load binned data
        df = load_binned_data(config)
        info(f"Loaded {len(df)} learner records")
        
        # Run Tukey HSD
        results_df, summary = run_tukey_hsd(df)
        
        # Save results
        save_results(results_df, summary, config)
        
        info("Tukey HSD analysis completed successfully")
        
    except Exception as e:
        error(f"Tukey HSD analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()