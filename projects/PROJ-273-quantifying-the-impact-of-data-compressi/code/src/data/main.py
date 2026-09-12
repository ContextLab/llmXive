import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error
from src.utils.config import get_project_root, ensure_dir
from src.data.fetch_loop import run_fetch_loop

logger = get_logger(__name__)

def main():
    """
    Main entry point for the download-inject-validate pipeline.
    
    Orchestrates the fetch -> inject -> validate loop to produce
    a validated dataset of >= 5 events with complete spin metadata.
    
    Operates under Amended FR-001.
    """
    log_step_start("Data Pipeline: Download-Inject-Validate")
    
    try:
        project_root = get_project_root()
        output_dir = project_root / "data" / "processed" / "validated_events"
        ensure_dir(output_dir)
        
        logger.info(f"Output directory: {output_dir}")
        
        # Configuration
        target_events = 5
        max_attempts = 50
        detector = "L1"
        
        logger.info(f"Running pipeline: target={target_events}, max_attempts={max_attempts}, detector={detector}")
        
        # Run the fetch loop
        validated_events = run_fetch_loop(
            target_events=target_events,
            max_attempts=max_attempts,
            detector=detector
        )
        
        # Save the validated dataset
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dataset_file = output_dir / f"validated_events_{timestamp}.json"
        
        with open(dataset_file, 'w') as f:
            json.dump(validated_events, f, indent=2, default=str)
        
        logger.info(f"Validated dataset saved to: {dataset_file}")
        logger.info(f"Total events: {len(validated_events)}")
        
        log_step_complete("Data Pipeline: Download-Inject-Validate", {
            "events_found": len(validated_events),
            "output_file": str(dataset_file)
        })
        
        return 0
        
    except Exception as e:
        log_step_error("Data Pipeline: Download-Inject-Validate", str(e))
        logger.error(f"Pipeline failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())