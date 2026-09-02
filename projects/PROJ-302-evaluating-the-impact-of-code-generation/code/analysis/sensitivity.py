import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import from sibling modules based on API surface
from analysis.statistical_test import run_full_analysis
from utils.config import get_config, ensure_directories

logger = logging.getLogger(__name__)

def load_analysis_data(input_path: str) -> pd.DataFrame:
    """
    Load the processed analysis dataset containing review durations and group labels.
    Expects a parquet file with columns: 'review_duration', 'generation_source', 'repo_stars', etc.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Analysis data file not found: {input_path}")
    
    logger.info(f"Loading analysis data from {input_path}")
    df = pd.read_parquet(path)
    
    required_cols = ['review_duration', 'generation_source']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in analysis data: {missing}")
    
    return df

def stratify_by_stars(df: pd.DataFrame, n_bins: int = 4) -> Dict[str, pd.DataFrame]:
    """
    Stratify the dataset into subsets based on repository star-count quartiles.
    Returns a dictionary mapping bin labels to DataFrames.
    """
    if 'repo_stars' not in df.columns:
        # Fallback if star count isn't directly available, try to infer from repo_id or assume uniform
        # For this task, we assume 'repo_stars' exists as per data model. 
        # If missing, we might need to join with repo metadata, but for now we assume it's in the processed data.
        logger.warning("Column 'repo_stars' not found. Attempting to stratify by index or failing.")
        # If the column is truly missing, we cannot stratify by stars.
        # We raise an error to fail loudly rather than fabricate a stratification.
        raise ValueError("Column 'repo_stars' is required for stratification but not found in data.")

    # Ensure numeric
    df = df.copy()
    df['repo_stars'] = pd.to_numeric(df['repo_stars'], errors='coerce').fillna(0)

    # Calculate quartiles
    quartiles = df['repo_stars'].quantile([0.25, 0.50, 0.75])
    bins = [-1, quartiles.iloc[0], quartiles.iloc[1], quartiles.iloc[2], float('inf')]
    labels = ['Q1', 'Q2', 'Q3', 'Q4']

    df['star_quartile'] = pd.cut(df['repo_stars'], bins=bins, labels=labels, include_lowest=True)

    subsets = {}
    for label in labels:
        subset = df[df['star_quartile'] == label]
        if len(subset) > 0:
            subsets[label] = subset
            logger.info(f"Stratum {label}: {len(subset)} samples")
        else:
            logger.warning(f"Stratum {label} is empty.")

    if len(subsets) < 2:
        logger.warning("Fewer than 2 valid strata found for sensitivity analysis.")
    
    return subsets

def run_sensitivity_analysis(subsets: Dict[str, pd.DataFrame], alpha: float = 0.05, consistency_threshold: float = 0.80) -> Dict[str, Any]:
    """
    Run statistical tests on each stratum and check for consistency.
    
    Consistency is defined as: p < alpha in >= consistency_threshold * 100% of subsets.
    
    Returns a summary dictionary including the 'consistent' boolean flag.
    """
    results = []
    significant_count = 0
    total_count = 0

    logger.info(f"Running sensitivity analysis on {len(subsets)} strata...")

    for label, subset_df in subsets.items():
        logger.info(f"Processing stratum: {label} (n={len(subset_df)})")
        
        # Filter to ensure we have both groups
        groups = subset_df['generation_source'].unique()
        if len(groups) < 2:
            logger.warning(f"Stratum {label} has only one group ({groups}). Skipping.")
            continue

        # Run full statistical test
        # Expected output from run_full_analysis: dict with 'p_value', 'test_name', 'effect_size', etc.
        try:
            test_result = run_full_analysis(subset_df, group_col='generation_source', value_col='review_duration')
            
            p_val = test_result.get('p_value')
            is_sig = False
            if p_val is not None:
                is_sig = (p_val < alpha)
                if is_sig:
                    significant_count += 1
            
            results.append({
                'stratum': label,
                'n_samples': len(subset_df),
                'p_value': p_val,
                'is_significant': is_sig,
                'test_name': test_result.get('test_name'),
                'effect_size': test_result.get('effect_size')
            })
            total_count += 1
            
        except Exception as e:
            logger.error(f"Error running test on stratum {label}: {e}")
            results.append({
                'stratum': label,
                'n_samples': len(subset_df),
                'p_value': None,
                'is_significant': False,
                'error': str(e)
            })
            total_count += 1

    if total_count == 0:
        logger.error("No valid strata found for analysis.")
        return {
            'consistent': False,
            'total_strata': 0,
            'significant_strata': 0,
            'threshold': consistency_threshold,
            'stratum_details': [],
            'message': "No valid data to analyze."
        }

    proportion_significant = significant_count / total_count
    is_consistent = proportion_significant >= consistency_threshold

    summary = {
        'consistent': is_consistent,
        'total_strata': total_count,
        'significant_strata': significant_count,
        'proportion_significant': proportion_significant,
        'threshold': consistency_threshold,
        'stratum_details': results,
        'message': f"Significant in {significant_count}/{total_count} strata ({proportion_significant:.1%}). "
                   f"Consistency threshold: {consistency_threshold:.0%}. "
                   f"Result: {'CONSISTENT' if is_consistent else 'INCONSISTENT'}."
    }

    return summary

def main():
    """
    Main entry point for the sensitivity analysis script.
    Loads data, stratifies by stars, runs tests, and writes sensitivity_summary.json.
    """
    # Configuration
    config = get_config()
    input_path = config.get('paths', {}).get('analysis_data', 'data/processed/analysis_results.parquet')
    output_dir = Path(config.get('paths', {}).get('processed_data', 'data/processed'))
    output_file = output_dir / 'sensitivity_summary.json'
    
    # Ensure output directory exists
    ensure_directories([output_dir])

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 1. Load Data
        df = load_analysis_data(input_path)
        
        # 2. Stratify
        subsets = stratify_by_stars(df)
        
        # 3. Run Analysis
        summary = run_sensitivity_analysis(subsets)
        
        # 4. Write Output
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Sensitivity analysis complete. Summary written to {output_file}")
        print(f"Result: {'Consistent' if summary['consistent'] else 'Inconsistent'}")
        print(f"Message: {summary['message']}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()