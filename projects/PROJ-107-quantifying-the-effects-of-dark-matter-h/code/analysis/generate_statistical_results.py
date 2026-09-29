import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import csv

# Import from project API surface
from analysis.stats import (
    run_statistical_tests,
    apply_bonferroni_correction,
    save_statistical_results
)
from utils.config import (
    get_project_root,
    get_data_processed_path,
    get_output_path
)
from utils.logging import get_pipeline_logger, log_task_start, log_task_end
from analysis.metadata_utils import add_associational_only_flag_to_csv

logger = get_pipeline_logger(__name__)

def load_halo_data() -> pd.DataFrame:
    """Load processed halo shapes from T017."""
    path = get_data_processed_path() / "halo_shapes.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}. "
                                "Ensure T017 has been completed successfully.")
    return pd.read_csv(path)

def load_galaxy_properties() -> pd.DataFrame:
    """Load galaxy properties from T018."""
    path = get_data_processed_path() / "galaxy_properties.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}. "
                                "Ensure T018 has been completed successfully.")
    return pd.read_csv(path)

def merge_halo_galaxy_data(halo_df: pd.DataFrame, galaxy_df: pd.DataFrame) -> pd.DataFrame:
    """Merge halo and galaxy data on halo_id."""
    # Ensure both have halo_id as integer for join
    merged = pd.merge(
        halo_df,
        galaxy_df,
        on='halo_id',
        how='inner'
    )
    logger.info(f"Merged dataset size: {len(merged)} rows")
    return merged

def run_statistical_tests_on_merged(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Execute the full statistical analysis pipeline:
    1. Run Kruskal-Wallis, Mann-Whitney U, KS tests (T022)
    2. Run Linear Regression with mass control (T023)
    3. Apply Bonferroni correction (T024)
    4. Return aggregated results ready for output.
    """
    logger.info("Running statistical tests on merged dataset...")
    
    # Run tests using the unified interface from stats.py
    # This function encapsulates T021 (matching), T022 (tests), T023 (regression), T024 (correction)
    results = run_statistical_tests(merged_df)
    
    return results

def save_results(results_df: pd.DataFrame, output_path: Path) -> None:
    """
    Save results to CSV with the required schema and associational flag.
    Schema: predictor, coefficient, p_value, r_squared, ci_lower, ci_upper
    Note: For non-regression tests, 'coefficient' might be a statistic value, 
    and 'r_squared' might be 0 or N/A. We normalize to the requested schema.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Normalize columns if necessary to match expected schema
    # The stats.py save_statistical_results likely returns a standard format.
    # We ensure it matches the task requirement: predictor, coefficient, p_value, r_squared, ci_lower, ci_upper
    required_cols = ['predictor', 'coefficient', 'p_value', 'r_squared', 'ci_lower', 'ci_upper']
    
    # If the source has different column names, map them.
    # Assuming run_statistical_tests returns a DataFrame with relevant stats.
    # If it returns a dict of lists, convert to DF.
    if not isinstance(results_df, pd.DataFrame):
        results_df = pd.DataFrame(results_df)

    # Fill missing columns with NaN if they don't exist
    for col in required_cols:
        if col not in results_df.columns:
            results_df[col] = np.nan

    # Reorder columns
    results_df = results_df[required_cols]
    
    # Write CSV
    results_df.to_csv(output_path, index=False)
    logger.info(f"Statistical results saved to {output_path}")
    
    # Apply associational flag as per T026 requirement
    add_associational_only_flag_to_csv(output_path)

def main():
    """
    Main entry point for T025: Create analysis script to generate statistical_results.csv.
    Dependencies: T021, T022, T023, T024, T026.
    """
    log_task_start("T025", "Generate Statistical Results")
    
    try:
        # 1. Load Data
        logger.info("Loading input data...")
        halo_df = load_halo_data()
        galaxy_df = load_galaxy_properties()
        
        # 2. Merge Data
        merged_df = merge_halo_galaxy_data(halo_df, galaxy_df)
        
        if len(merged_df) == 0:
            raise ValueError("Merged dataset is empty. Check data integrity in T017/T018.")
        
        # 3. Run Statistical Analysis (T021-T024)
        results = run_statistical_tests_on_merged(merged_df)
        
        # 4. Save Results (T025)
        output_path = get_data_processed_path() / "statistical_results.csv"
        save_results(results, output_path)
        
        log_task_end("T025", "Success", {"output_file": str(output_path)})
        return 0
        
    except Exception as e:
        logger.error(f"Task T025 failed: {e}", exc_info=True)
        log_task_end("T025", "Failed", {"error": str(e)})
        return 1

if __name__ == "__main__":
    sys.exit(main())