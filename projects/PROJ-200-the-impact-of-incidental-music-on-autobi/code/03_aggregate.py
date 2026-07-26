"""
Script T03_aggregate.py: Orchestrates the aggregation phase of the pipeline.

This script performs the following steps:
1. Joins exposure data with matched cues (T025 logic).
2. Aggregates data to the User-Track Pair level (T026 logic).
3. Filters out tracks with zero variance/zero pairs (T027 logic).
4. Enforces match rate threshold (T036 logic).
5. Saves the final `user_track_pairs.parquet` artifact (T029 logic).

This script is invoked by the quickstart run-book to replace the missing
`code/03_aggregate.py` referenced in the execution feedback.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from aggregation import (
    join_exposure_data,
    aggregate_to_user_track,
    filter_zero_variance,
    enforce_match_rate,
    main as aggregation_main
)
from config import get_project_root, get_config_dict
from utils import setup_logging, get_logger

def main():
    """
    Main entry point for the aggregation script.
    Orchestrates the pipeline steps defined in User Story 2 (T025-T029).
    """
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Aggregation Phase (T03_aggregate.py)")
    
    root = get_project_root()
    config = get_config_dict()
    
    # Define paths based on config
    processed_dir = root / "data" / "processed"
    ingested_path = processed_dir / "ingested_cohort.parquet"
    output_path = processed_dir / "user_track_pairs.parquet"
    
    # Verify prerequisites
    if not ingested_path.exists():
        logger.error(f"Prerequisite file missing: {ingested_path}")
        logger.error("Run T013/T018 (Ingestion) before running this script.")
        sys.exit(1)
    
    logger.info(f"Loading ingested cohort from: {ingested_path}")
    try:
        # The aggregation module's main function orchestrates the steps
        # join_exposure_data -> aggregate_to_user_track -> filter_zero_variance -> enforce_match_rate
        # and writes the final parquet file.
        
        # We call the main function from the aggregation module which handles the flow.
        # However, to be explicit and ensure we follow the task dependencies:
        
        # 1. Join Exposure Data (T025)
        #    Input: ingested_cohort.parquet, matched cues (from previous step or internal state)
        #    Note: The aggregation module expects the cues to be available. 
        #    In a real pipeline, this might come from a previous script or a global state.
        #    For this script, we assume the data is ready to be processed by the module's main flow.
        
        # 2. Execute the aggregation pipeline
        #    The aggregation.main() function is designed to run the full flow.
        #    We pass the necessary paths if the function signature allows, 
        #    otherwise we rely on the module's internal logic to find files.
        
        # Since `aggregation.main` is the orchestrator for T025-T029:
        aggregation_main()
        
        # Verify output
        if output_path.exists():
            logger.info(f"Successfully generated: {output_path}")
            logger.info("Aggregation Phase Complete.")
        else:
            logger.error(f"Failed to generate expected output: {output_path}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during aggregation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()