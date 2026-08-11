"""
Main entry point for the Equivalence Principle Testing Pipeline.

Orchestrates the full workflow: Ingestion -> Preprocessing -> Estimation -> Validation.
"""
import os
import sys
import json
import time
import argparse
from typing import Optional, Dict, Any

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config import get_config
from data.ingestion import fetch_all_satellites, verify_data_availability
from data.preprocessing import preprocess_slr_data
from data.output import run_output_pipeline
from utils.logging import init_logging, get_logger, log_progress, log_error, handle_fatal_error

logger = get_logger(__name__)

def main():
    """
    Execute the full pipeline.
    """
    # Initialize logging
    init_logging(level="INFO")
    
    start_time = time.time()
    
    try:
        # Load configuration
        config = get_config()
        log_progress(logger, "Configuration loaded successfully.")
        
        # Verify data availability
        if not verify_data_availability():
            log_error(logger, "Data availability check failed. Cannot proceed.")
            return 1
            
        # Phase 1: Ingestion
        log_progress(logger, "Starting Data Ingestion...")
        raw_df = fetch_all_satellites(config.satellite_ids)
        if raw_df is None or raw_df.empty:
            log_error(logger, "Ingestion failed: No data retrieved.")
            return 1
        log_progress(logger, f"Ingestion complete. Retrieved {len(raw_df)} points.")
        
        # Phase 2: Preprocessing
        log_progress(logger, "Starting Data Preprocessing...")
        cleaned_df = preprocess_slr_data(raw_df, config)
        log_progress(logger, f"Preprocessing complete. {len(cleaned_df)} points remaining.")
        
        # Phase 3: Output & Checksums (Task T019)
        log_progress(logger, "Saving cleaned data and computing checksums (T019)...")
        
        output_path = run_output_pipeline(
            df=cleaned_df,
            raw_dir=config.raw_data_dir,
            processed_dir=config.processed_data_dir,
            output_filename="cleaned_slr_data.csv",
            checksum_filename=".checksums.json"
        )
        
        log_progress(logger, f"Output saved to {output_path}")
        
        # Verify checksum file exists
        checksum_path = os.path.join(config.processed_data_dir, ".checksums.json")
        if os.path.exists(checksum_path):
            with open(checksum_path, 'r') as f:
                checksums = json.load(f)
            log_progress(logger, f"Checksums recorded: {checksums}")
        else:
            log_error(logger, "Checksum file was not created.")
            return 1
            
        elapsed = time.time() - start_time
        log_progress(logger, f"Pipeline completed successfully in {elapsed:.2f} seconds.")
        
        return 0
        
    except Exception as e:
        handle_fatal_error(logger, e, "Pipeline execution failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
