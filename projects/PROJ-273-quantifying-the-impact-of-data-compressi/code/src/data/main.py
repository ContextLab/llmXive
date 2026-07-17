"""
Main orchestration script for the Download-Inject-Validate pipeline.

This script orchestrates the acquisition of real GW noise, injection of synthetic
CBC signals, and validation of the resulting dataset to produce the final
validated dataset for User Story 1.

It implements the logic to fetch batches of noise, inject signals, and validate
until >= 15 valid events are found (per Amended FR-001), or halts with an error
if max_attempts is reached.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.batch_processor import run_injection_campaign
from src.utils.config import get_config, get_paths
from src.utils.logging import setup_logging

# Constants
TARGET_EVENTS = 15
MAX_ATTEMPTS = 20
TIMEOUT_SECONDS = 300

def main():
    """
    Orchestrate the download-inject-validate pipeline.
    
    This function:
    1. Initializes logging and configuration.
    2. Calls the batch processor to run the injection campaign.
    3. Ensures the campaign runs until >= 15 valid events are found.
    4. Handles failure modes if max_attempts is reached without success.
    5. Produces the final validated dataset.
    """
    # Setup logging
    log_dir = get_paths()["logs"]
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{timestamp}.log"
    
    logger = setup_logging(log_file=log_file, level=logging.INFO)
    logger.info("=" * 60)
    logger.info("Starting Download-Inject-Validate Pipeline (T016)")
    logger.info(f"Target events: {TARGET_EVENTS}")
    logger.info(f"Max attempts: {MAX_ATTEMPTS}")
    logger.info(f"Timeout: {TIMEOUT_SECONDS}s")
    logger.info("=" * 60)

    try:
        # Get configuration
        config = get_config()
        paths = get_paths()
        
        # Ensure data directories exist
        for dir_name in ["raw", "interim", "processed", "external"]:
            dir_path = paths[dir_name]
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {dir_path}")

        # Run the injection campaign
        # This function handles:
        # - Fetching noise batches
        # - Injecting synthetic signals
        # - Validating results
        # - Stopping when >= TARGET_EVENTS valid events are found
        # - Raising an error if MAX_ATTEMPTS is reached without success
        logger.info(f"Starting injection campaign to find {TARGET_EVENTS} valid events...")
        
        valid_events = run_injection_campaign(
            target_events=TARGET_EVENTS,
            max_attempts=MAX_ATTEMPTS,
            timeout_seconds=TIMEOUT_SECONDS,
            logger=logger
        )
        
        logger.info(f"Pipeline completed successfully!")
        logger.info(f"Total valid events found: {len(valid_events)}")
        
        # Log summary of valid events
        logger.info("Valid events summary:")
        for event in valid_events:
            logger.info(f"  - {event['event_id']}: {event['detector']} at {event['timestamp']}")
        
        # Write summary report
        summary_path = paths["processed"] / "pipeline_summary.json"
        summary_data = {
            "target_events": TARGET_EVENTS,
            "max_attempts": MAX_ATTEMPTS,
            "timeout_seconds": TIMEOUT_SECONDS,
            "valid_events_count": len(valid_events),
            "events": valid_events,
            "completed_at": datetime.now().isoformat()
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"Summary report written to: {summary_path}")
        logger.info("=" * 60)
        logger.info("Pipeline execution finished successfully")
        logger.info("=" * 60)
        
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
        logger.info("=" * 60)
        logger.info("Pipeline execution FAILED")
        logger.info("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
