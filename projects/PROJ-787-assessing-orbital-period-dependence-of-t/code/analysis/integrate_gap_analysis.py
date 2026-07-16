"""
Integration script for User Story 2: Gap Location Estimation.

This script orchestrates the full analysis pipeline for US2:
1. Loads the deduplicated planet dataset (output of T015).
2. Bins planets by orbital period (T021 logic).
3. Fits GMM to each bin to find gap locations (T022/T023/T024 logic).
4. Aggregates results into a single CSV: data/processed/gap_locations.csv.

Dependencies:
- code/analysis/binning.py (create_log_bins, assign_bin_index, bin_planets_by_period, save_binned_data)
- code/analysis/gmm_fitter.py (fit_gmm_to_radius_distribution, calculate_gap_location, bootstrap_gap_estimation, process_binned_data)
- code/ingest/loaders.py (load_deduplicated_planets)
- code/utils/logging_config.py (setup_logging, get_logger)
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path if running as script
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.binning import bin_planets_by_period, save_binned_data
from analysis.gmm_fitter import process_binned_data
from ingest.loaders import load_deduplicated_planets
from utils.logging_config import setup_logging, get_logger
from utils.config import get_config

def run_integration_pipeline(logger: logging.Logger, config: dict):
    """
    Execute the full US2 integration pipeline.
    
    Steps:
    1. Load deduplicated planets.
    2. Bin by period.
    3. Fit GMM to each bin.
    4. Aggregate results.
    5. Save to data/processed/gap_locations.csv.
    """
    logger.info("Starting US2 Integration Pipeline")
    
    # 1. Load Data
    logger.info("Loading deduplicated planets...")
    planets_df = load_deduplicated_planets()
    if planets_df is None or planets_df.empty:
        logger.error("Failed to load deduplicated planets. Aborting.")
        raise RuntimeError("No data loaded for US2 integration.")
    
    logger.info(f"Loaded {len(planets_df)} planets.")
    
    # 2. Binning
    logger.info("Binning planets by orbital period...")
    # Parameters from spec: log-spaced bins, min 30 planets per bin (merge if needed)
    min_bin_size = config.get('us2', {}).get('min_bin_size', 30)
    max_period_days = config.get('us2', {}).get('max_period_days', 100)
    
    binned_df, bin_stats = bin_planets_by_period(
        planets_df, 
        min_bin_size=min_bin_size, 
        max_period=max_period_days
    )
    
    # Save intermediate binned data for inspection
    binned_path = Path(config['paths']['processed']) / "binned_planets.csv"
    save_binned_data(binned_df, binned_path)
    logger.info(f"Saved binned data to {binned_path}")
    
    # 3. GMM Fitting & Gap Calculation
    logger.info("Fitting GMM and calculating gap locations...")
    gap_results = process_binned_data(binned_df, logger)
    
    if not gap_results:
        logger.warning("No gap locations were successfully calculated.")
        # Create an empty result file with correct schema to prevent downstream crashes
        results_df = pd.DataFrame(columns=[
            'bin_index', 'bin_center_log_period', 'weighted_mean_period',
            'gap_location', 'gap_uncertainty', 'status', 'n_planets'
        ])
    else:
        results_df = pd.DataFrame(gap_results)
        
        # Ensure required columns exist
        required_cols = [
            'bin_index', 'bin_center_log_period', 'weighted_mean_period',
            'gap_location', 'gap_uncertainty', 'status', 'n_planets'
        ]
        for col in required_cols:
            if col not in results_df.columns:
                results_df[col] = None
                
        # Sort by bin index
        results_df = results_df.sort_values('bin_index')
    
    # 4. Save Final Output
    output_path = Path(config['paths']['processed']) / "gap_locations.csv"
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved final gap locations to {output_path}")
    
    logger.info("US2 Integration Pipeline completed successfully.")
    return results_df

def main():
    """Entry point for the integration script."""
    setup_logging(log_level=logging.INFO)
    logger = get_logger(__name__)
    
    # Load configuration
    try:
        from utils.config import load_config
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        config = {
            'paths': {
                'processed': str(Path(__file__).resolve().parents[2] / 'data' / 'processed'),
                'raw': str(Path(__file__).resolve().parents[2] / 'data' / 'raw')
            },
            'us2': {
                'min_bin_size': 30,
                'max_period_days': 100
            }
        }

    try:
        run_integration_pipeline(logger, config)
    except Exception as e:
        logger.exception("Pipeline execution failed.")
        raise

if __name__ == "__main__":
    main()