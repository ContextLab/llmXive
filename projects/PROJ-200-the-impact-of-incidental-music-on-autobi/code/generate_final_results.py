"""
Generate final analysis results: sensitivity analysis and permutation test results.

This module orchestrates the generation of:
1. sensitivity_analysis.csv: Results from re-running the analysis with different Levenshtein thresholds
2. permutation_results.csv: Results from the block-permutation test
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import from project modules
from config import get_project_root, get_config_dict
from utils import setup_logging, get_logger
from modeling import run_sensitivity_analysis, run_permutation_test
from state_manager import register_file, save_state

logger = get_logger(__name__)

def run_sensitivity_analysis_pipeline() -> pd.DataFrame:
    """
    Run the sensitivity analysis pipeline and return results DataFrame.
    
    This function:
    1. Calls run_sensitivity_analysis from modeling.py
    2. Formats the results into a tidy DataFrame
    3. Returns the DataFrame for saving
    
    Returns:
        pd.DataFrame: Tidy DataFrame with sensitivity analysis results
    """
    logger.info("Starting sensitivity analysis pipeline")
    
    # Run the sensitivity analysis from modeling module
    results = run_sensitivity_analysis()
    
    if results is None or len(results) == 0:
        logger.error("Sensitivity analysis returned no results")
        return pd.DataFrame()
    
    # Convert list of dicts to DataFrame
    df = pd.DataFrame(results)
    
    # Ensure proper column ordering
    expected_cols = [
        'threshold', 'n_user_track_pairs', 'mean_vividness', 'mean_valence',
        'residualized_exposure_coef', 'residualized_exposure_se', 
        'residualized_exposure_pval', 'popularity_coef', 'popularity_se',
        'popularity_pval', 'model_r2', 'vif_residualized', 'vif_popularity'
    ]
    
    # Only keep columns that exist
    available_cols = [col for col in expected_cols if col in df.columns]
    df = df[available_cols]
    
    logger.info(f"Sensitivity analysis completed. Generated {len(df)} rows.")
    return df

def run_permutation_test_pipeline(n_permutations: int = 1000) -> pd.DataFrame:
    """
    Run the permutation test pipeline and return results DataFrame.
    
    This function:
    1. Calls run_permutation_test from modeling.py
    2. Formats the results into a DataFrame
    3. Returns the DataFrame for saving
    
    Args:
        n_permutations (int): Number of permutations to run (default: 1000)
        
    Returns:
        pd.DataFrame: DataFrame with permutation test results
    """
    logger.info(f"Starting permutation test pipeline with {n_permutations} permutations")
    
    # Run the permutation test from modeling module
    results = run_permutation_test(n_permutations=n_permutations)
    
    if results is None:
        logger.error("Permutation test returned no results")
        return pd.DataFrame()
    
    # Convert results to DataFrame
    # Expected structure: observed_stat, null_distribution (list), p_value, n_permutations
    df = pd.DataFrame([results])
    
    # Ensure column names are consistent
    if 'observed_stat' in df.columns:
        df = df.rename(columns={'observed_stat': 'observed_statistic'})
    
    logger.info(f"Permutation test completed. P-value: {df['p_value'].iloc[0]:.4f}")
    return df

def main():
    """
    Main entry point for generating final results.
    
    This function:
    1. Sets up logging
    2. Creates output directories
    3. Runs sensitivity analysis and saves to CSV
    4. Runs permutation test and saves to CSV
    5. Updates state.yaml with checksums
    """
    # Setup logging
    setup_logging()
    logger.info("=" * 60)
    logger.info("Starting Final Results Generation (T039)")
    logger.info("=" * 60)
    
    # Get project root and config
    project_root = get_project_root()
    config = get_config_dict()
    
    # Define output paths
    output_dir = project_root / "data" / "final"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sensitivity_path = output_dir / "sensitivity_analysis.csv"
    permutation_path = output_dir / "permutation_results.csv"
    
    # Run sensitivity analysis
    logger.info("Running sensitivity analysis...")
    try:
        sensitivity_df = run_sensitivity_analysis_pipeline()
        
        if not sensitivity_df.empty:
            sensitivity_df.to_csv(sensitivity_path, index=False)
            logger.info(f"Saved sensitivity analysis to: {sensitivity_path}")
            
            # Register file in state manager
            register_file(str(sensitivity_path), "sensitivity_analysis")
        else:
            logger.warning("Sensitivity analysis produced empty results. Skipping save.")
            
    except Exception as e:
        logger.error(f"Error running sensitivity analysis: {e}", exc_info=True)
        # Continue to permutation test even if sensitivity fails
    
    # Run permutation test
    logger.info("Running permutation test...")
    try:
        # Use 1000 permutations as default, configurable via config
        n_perms = config.get('permutation_n', 1000)
        permutation_df = run_permutation_test_pipeline(n_permutations=n_perms)
        
        if not permutation_df.empty:
            permutation_df.to_csv(permutation_path, index=False)
            logger.info(f"Saved permutation results to: {permutation_path}")
            
            # Register file in state manager
            register_file(str(permutation_path), "permutation_results")
        else:
            logger.warning("Permutation test produced empty results. Skipping save.")
            
    except Exception as e:
        logger.error(f"Error running permutation test: {e}", exc_info=True)
    
    # Save state
    try:
        save_state()
        logger.info("Updated state.yaml with new file checksums")
    except Exception as e:
        logger.error(f"Error saving state: {e}", exc_info=True)
    
    logger.info("=" * 60)
    logger.info("Final Results Generation Complete")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
