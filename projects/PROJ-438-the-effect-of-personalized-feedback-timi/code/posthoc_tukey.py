"""
Post-hoc Tukey HSD analysis for feedback timing groups.

Implements Tukey's Honestly Significant Difference test to control 
family-wise error rate when performing pairwise comparisons between
feedback timing groups (Immediate, Delayed, Variable).

Output: data/processed/tukey_hsd_results.csv
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from logging_config import get_logger, info, warning, error, debug

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

logger = get_logger(__name__)

def load_binned_data() -> pd.DataFrame:
    """
    Load the binned learner data from the previous processing step.
    
    Returns:
        DataFrame with learner records including 'feedback_group' and 'final_grade'
    
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If required columns are missing
    """
    input_path = DATA_PROCESSED / "learners_binned.csv"
    
    if not input_path.exists():
        error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['learner_id', 'final_grade', 'feedback_group']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    info(f"Loaded {len(df)} learner records from {input_path}")
    return df

def run_tukey_hsd(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform Tukey HSD post-hoc pairwise comparisons on feedback groups.
    
    Args:
        df: DataFrame with 'final_grade' and 'feedback_group' columns
    
    Returns:
        Dictionary containing:
            - 'results': DataFrame with Tukey HSD test results
            - 'summary': Dictionary with key statistics
            - 'significant_pairs': List of tuples with significant comparisons
    """
    # Filter out any rows with missing values in key columns
    clean_df = df.dropna(subset=['final_grade', 'feedback_group'])
    
    if len(clean_df) < 3:
        error("Insufficient data for Tukey HSD test (need at least 3 observations)")
        raise ValueError("Insufficient data for Tukey HSD test")
    
    # Check that we have at least 2 groups
    unique_groups = clean_df['feedback_group'].unique()
    if len(unique_groups) < 2:
        error(f"Need at least 2 groups for pairwise comparison, found {len(unique_groups)}")
        raise ValueError(f"Need at least 2 groups for pairwise comparison, found {len(unique_groups)}")
    
    info(f"Running Tukey HSD on {len(clean_df)} observations across {len(unique_groups)} groups: {list(unique_groups)}")
    
    try:
        # Perform Tukey HSD test
        tukey = pairwise_tukeyhsd(
            endog=clean_df['final_grade'],
            groups=clean_df['feedback_group'],
            alpha=0.05
        )
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(tukey.summary2().data[1:])
        results_df.columns = ['Group1', 'Group2', 'Mean Difference', 'Std Err', 'Lower CI', 'Upper CI', 'Reject']
        
        # Clean up column names and types
        results_df['Mean Difference'] = pd.to_numeric(results_df['Mean Difference'], errors='coerce')
        results_df['Std Err'] = pd.to_numeric(results_df['Std Err'], errors='coerce')
        results_df['Lower CI'] = pd.to_numeric(results_df['Lower CI'], errors='coerce')
        results_df['Upper CI'] = pd.to_numeric(results_df['Upper CI'], errors='coerce')
        results_df['Reject'] = results_df['Reject'].astype(bool)
        
        # Identify significant pairs
        significant_pairs = []
        for _, row in results_df.iterrows():
            if row['Reject']:
                significant_pairs.append((row['Group1'], row['Group2'], row['Mean Difference']))
        
        info(f"Found {len(significant_pairs)} significant pairwise comparisons")
        
        summary = {
            'total_observations': len(clean_df),
            'num_groups': len(unique_groups),
            'groups': list(unique_groups),
            'significant_comparisons': len(significant_pairs),
            'alpha': 0.05,
            'method': 'Tukey HSD'
        }
        
        return {
            'results': results_df,
            'summary': summary,
            'significant_pairs': significant_pairs
        }
        
    except Exception as e:
        error(f"Tukey HSD test failed: {str(e)}")
        raise

def save_results(results: Dict[str, Any]) -> Path:
    """
    Save Tukey HSD results to CSV file.
    
    Args:
        results: Dictionary containing 'results' DataFrame and 'summary'
    
    Returns:
        Path to the saved file
    """
    output_path = DATA_PROCESSED / "tukey_hsd_results.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the results DataFrame
    results['results'].to_csv(output_path, index=False)
    
    # Save summary as a separate JSON file for easy access
    summary_path = DATA_PROCESSED / "tukey_hsd_summary.json"
    import json
    with open(summary_path, 'w') as f:
        json.dump(results['summary'], f, indent=2)
    
    info(f"Saved Tukey HSD results to {output_path}")
    info(f"Saved Tukey HSD summary to {summary_path}")
    
    return output_path

def main():
    """Main execution function for Tukey HSD post-hoc analysis."""
    info("=" * 60)
    info("Starting Tukey HSD Post-hoc Analysis")
    info("=" * 60)
    
    try:
        # Load binned data
        df = load_binned_data()
        
        # Run Tukey HSD test
        results = run_tukey_hsd(df)
        
        # Save results
        output_path = save_results(results)
        
        # Print summary
        info("\nTukey HSD Test Summary:")
        info(f"  Total observations: {results['summary']['total_observations']}")
        info(f"  Number of groups: {results['summary']['num_groups']}")
        info(f"  Groups: {', '.join(results['summary']['groups'])}")
        info(f"  Significant pairwise comparisons: {results['summary']['significant_comparisons']}")
        
        if results['significant_pairs']:
            info("\nSignificant Pairs:")
            for pair in results['significant_pairs']:
                info(f"  {pair[0]} vs {pair[1]}: Mean Diff = {pair[2]:.4f}")
        
        info("\n" + "=" * 60)
        info("Tukey HSD Post-hoc Analysis Complete")
        info(f"Results saved to: {output_path}")
        info("=" * 60)
        
    except FileNotFoundError as e:
        error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error during Tukey HSD analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
