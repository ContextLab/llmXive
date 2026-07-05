"""
Script to verify DFT functional metadata for the Perovskite Stability Pipeline.

This script ensures that the model metadata explicitly states the DFT functional
(PBE) used to generate the training labels, as required by the research specification.

Usage:
    python code/run_verify_metadata.py --results-dir results
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.model_metadata import main as verify_metadata_main
from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

def main():
    """
    Entry point for the metadata verification script.
    """
    logger.info("Starting DFT functional metadata verification...")
    
    try:
        # Run the verification logic
        exit_code = verify_metadata_main()
        
        if exit_code == 0:
            log_pipeline_event("Metadata verification completed successfully", level="INFO")
            logger.info("DFT functional verification PASSED")
        else:
            log_pipeline_event("Metadata verification FAILED", level="ERROR")
            logger.error("DFT functional verification FAILED")
        
        return exit_code

    except Exception as e:
        logger.exception(f"Unexpected error during metadata verification: {e}")
        log_pipeline_event(f"Metadata verification crashed: {e}", level="ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())
