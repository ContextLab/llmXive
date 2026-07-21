"""
Final Results Generation Module for T039.

This module orchestrates the generation of sensitivity analysis and permutation test results
by calling the underlying modeling functions and saving the outputs to CSV files.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import from sibling modules based on provided API surface
from config import get_project_root, get_config_dict
from modeling import run_sensitivity_analysis, run_permutation_test
from utils import setup_logging, get_logger
from state_manager import register_file, save_state

logger = get_logger(__name__)

def run_sensitivity_analysis_pipeline() -> Optional[str]:
    """
    Executes the sensitivity analysis pipeline and saves results to CSV.
    
    Returns:
        str: Path to the generated CSV file, or None if failed.
    """
    logger.info("Starting sensitivity analysis pipeline...")
    project_root = get_project_root()
    output_dir = project_root / "data" / "final"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "sensitivity_analysis.csv"

    try:
        # Call the modeling function which handles the full loop and aggregation
        results_df = run_sensitivity_analysis()
        
        if results_df is None or results_df.empty:
            logger.error("Sensitivity analysis returned no results.")
            return None

        # Ensure required columns exist
        required_cols = ['threshold', 'match_rate', 'coefficient', 'p_value', 'std_err']
        for col in required_cols:
            if col not in results_df.columns:
                logger.warning(f"Column {col} missing in sensitivity results, adding as NaN.")
                results_df[col] = np.nan

        # Save to CSV
        results_df.to_csv(output_path, index=False)
        logger.info(f"Sensitivity analysis results saved to {output_path}")
        
        # Register in state manager
        checksum = register_file(output_path)
        logger.info(f"Registered sensitivity_analysis.csv with checksum: {checksum}")
        
        return str(output_path)
    except Exception as e:
        logger.error(f"Error during sensitivity analysis pipeline: {e}", exc_info=True)
        return None

def run_permutation_test_pipeline() -> Optional[str]:
    """
    Executes the permutation test pipeline and saves results to CSV.
    
    Returns:
        str: Path to the generated CSV file, or None if failed.
    """
    logger.info("Starting permutation test pipeline...")
    project_root = get_project_root()
    output_dir = project_root / "data" / "final"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "permutation_results.csv"

    try:
        # Call the modeling function which handles the block-permutation logic
        results_df = run_permutation_test()
        
        if results_df is None or results_df.empty:
            logger.error("Permutation test returned no results.")
            return None

        # Ensure required columns exist
        required_cols = ['iteration', 'statistic']
        for col in required_cols:
            if col not in results_df.columns:
                logger.warning(f"Column {col} missing in permutation results, adding as NaN.")
                results_df[col] = np.nan

        # Save to CSV
        results_df.to_csv(output_path, index=False)
        logger.info(f"Permutation test results saved to {output_path}")
        
        # Register in state manager
        checksum = register_file(output_path)
        logger.info(f"Registered permutation_results.csv with checksum: {checksum}")
        
        return str(output_path)
    except Exception as e:
        logger.error(f"Error during permutation test pipeline: {e}", exc_info=True)
        return None

def main():
    """
    Main entry point for generating final results (T039).
    """
    setup_logging()
    logger.info("=== Starting T039: Final Results Generation ===")
    
    # Run Sensitivity Analysis
    sens_path = run_sensitivity_analysis_pipeline()
    
    # Run Permutation Test
    perm_path = run_permutation_test_pipeline()
    
    if sens_path and perm_path:
        logger.info("=== T039 Completed Successfully ===")
        return 0
    else:
        logger.error("=== T039 Failed: Missing outputs ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())
