"""
code/run_subset_pipeline.py
Creates a static subset of the data and runs the full pipeline to verify end-to-end execution.
"""
import os
import sys
import time
import json
import logging
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from download import main as download_main
from preprocess import main as preprocess_main
from models import fit_pilot_ols, calculate_residuals, fit_full_lmm, fit_reduced_lmm, run_lrt, save_lmm_summary
from visualize import main as visualize_main
from robustness import main as robustness_main
from update_state import main as update_state_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('subset_pipeline')

def create_subset_data():
    """
    Create a static subset of the data for testing.
    This function assumes the full dataset has already been downloaded by T006/T036.
    It creates a smaller, manageable subset for the 6-hour verification run.
    """
    data_path = project_root / 'data' / 'raw' / 'data.csv'
    
    if not data_path.exists():
        logger.warning(f"Raw data not found at {data_path}. Downloading first...")
        download_main()
    
    import pandas as pd
    
    logger.info("Loading raw data for subset creation...")
    df = pd.read_csv(data_path)
    
    # Create a static subset: first 500 rows with complete data
    # This ensures we have a reproducible subset for testing
    logger.info(f"Original dataset size: {len(df)} rows")
    
    # Filter for rows with complete data in critical columns
    critical_cols = ['year', 'effect_size', 'sample_size', 'field', 'original_study_id']
    available_cols = [col for col in critical_cols if col in df.columns]
    df_clean = df.dropna(subset=available_cols)
    
    logger.info(f"Rows with complete data: {len(df_clean)}")
    
    # Take a static subset of 500 rows (or all if less)
    subset_size = min(500, len(df_clean))
    df_subset = df_clean.head(subset_size).reset_index(drop=True)
    
    subset_path = project_root / 'data' / 'raw' / 'data_subset.csv'
    df_subset.to_csv(subset_path, index=False)
    
    logger.info(f"Created subset with {subset_size} rows at {subset_path}")
    
    return subset_path

def run_pipeline_subset():
    """
    Run the full pipeline on the subset data.
    This simulates the full workflow but with a smaller dataset.
    """
    logger.info("Starting subset pipeline execution...")
    
    # 1. Preprocess
    logger.info("Step 1: Preprocessing data...")
    preprocess_main()
    
    # 2. Fit Pilot OLS
    logger.info("Step 2: Fitting Pilot OLS model...")
    fit_pilot_ols()
    
    # 3. Calculate Residuals
    logger.info("Step 3: Calculating residuals...")
    calculate_residuals()
    
    # 4. Fit LMMs and run LRT
    logger.info("Step 4: Fitting LMMs and running LRT...")
    fit_full_lmm()
    fit_reduced_lmm()
    run_lrt()
    save_lmm_summary()
    
    # 5. Visualize
    logger.info("Step 5: Generating visualizations...")
    visualize_main()
    
    # 6. Robustness checks
    logger.info("Step 6: Running robustness checks...")
    robustness_main()
    
    # 7. Update state
    logger.info("Step 7: Updating project state...")
    update_state_main()
    
    logger.info("Subset pipeline completed successfully")

def main():
    """Main entry point for subset pipeline execution."""
    logger.info("=" * 60)
    logger.info("Creating static subset and running pipeline verification")
    logger.info("=" * 60)
    
    # Create subset
    subset_path = create_subset_data()
    
    if subset_path is None:
        logger.error("Failed to create subset data")
        return 1
    
    # Run pipeline
    try:
        run_pipeline_subset()
        logger.info("✓ Subset pipeline execution successful")
        return 0
    except Exception as e:
        logger.error(f"✗ Subset pipeline execution failed: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())