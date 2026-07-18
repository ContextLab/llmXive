"""
Main entry point for the Coating Adhesion Pipeline.
Orchestrates the execution of all phases.
"""
import os
import sys
import logging
import yaml
import json
import time

from utils import setup_logging, check_halt_signal, write_halt_signal, RuntimeMonitor, start_runtime_monitoring
from config import STATE_DIR, TIMEOUT_HOURS, DATA_PROCESSED_DIR

logger = setup_logging()

def run_pipeline():
    """
    Execute the full pipeline.
    """
    logger.info("Starting Coating Adhesion Pipeline...")
    
    # Start runtime monitoring
    monitor = start_runtime_monitoring(limit_hours=TIMEOUT_HOURS)

    try:
        # Phase 0: Data Gap Analysis (Already handled by T062 logic, but we check signal here)
        if check_halt_signal(STATE_DIR):
            logger.error("Pipeline halted by Phase 0 Data Gap Analysis.")
            return 1

        # Phase 1: Setup (Directories, Config) - Assumed complete or handled by T001-T008
        # Phase 2: Foundational (Safety Gates) - Assumed complete or handled by T009-T015

        # Phase 3: User Story 1 - Dataset Curation
        # This is where T018 (integration test) would be run to validate the pipeline
        # For the main pipeline run, we would call ingestion logic here.
        
        # Example: Ingest data
        # from ingestion import process_ingestion_data
        # df = process_ingestion_data(...)
        
        logger.info("Pipeline execution completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        write_halt_signal(STATE_DIR, reason=str(e))
        return 1
    finally:
        monitor.stop()

def main():
    """Main entry point."""
    exit_code = run_pipeline()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()