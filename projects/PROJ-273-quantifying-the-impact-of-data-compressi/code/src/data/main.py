"""
Main orchestration script for the Data Pipeline (US1).
Orchestrates the download-inject-validate pipeline to produce the validated dataset.
Target: >=5 valid events with complete spin metadata (tilt_angle).
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))

from src.data.fetch_loop import run_fetch_loop
from src.utils.logging import setup_logging, get_logger, log_step_start, log_step_complete, log_step_error
from src.utils.config import get_project_root, ensure_dir

def main():
    """
    Orchestrate the download-inject-validate pipeline.
    Runs until >=5 valid events are found or max_attempts (50) is reached.
    Outputs: data/interim/valid_events.json
    """
    # Setup logging
    logger = setup_logging(level="INFO")
    log_step_start("Data Pipeline Orchestration", "T020")

    try:
        # Configuration
        target_valid_count = 5
        max_attempts = 50

        logger.info(f"Starting pipeline to acquire {target_valid_count} valid events.")
        logger.info(f"Maximum attempts allowed: {max_attempts}")

        # Run the fetch-inject-validate loop
        # This calls T019.1 logic which handles:
        # 1. Fetching noise from GWOSC
        # 2. Injecting synthetic signal (T013)
        # 3. Validating metadata (T014) including tilt_angle
        valid_events, stats = run_fetch_loop(
            target_count=target_valid_count,
            max_attempts=max_attempts,
            logger=logger
        )

        # Prepare output
        output_data = {
            "event_ids": valid_events,
            "count": len(valid_events),
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Ensure output directory exists
        project_root = get_project_root()
        output_dir = project_root / "data" / "interim"
        ensure_dir(output_dir)

        output_path = output_dir / "valid_events.json"

        # Write results
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Pipeline complete. Found {len(valid_events)} valid events.")
        logger.info(f"Results saved to: {output_path}")

        # Check success criteria
        if len(valid_events) < target_valid_count:
            logger.error(f"Failed to generate {target_valid_count} valid events after {max_attempts} attempts.")
            log_step_error("Data Pipeline Orchestration", "Failed to reach target event count")
            sys.exit(1)
        else:
            log_step_complete("Data Pipeline Orchestration", f"Generated {len(valid_events)} valid events")
            sys.exit(0)

    except RuntimeError as e:
        logger.error(f"Pipeline failed: {str(e)}")
        log_step_error("Data Pipeline Orchestration", str(e))
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during pipeline execution: {e}")
        log_step_error("Data Pipeline Orchestration", str(e))
        raise

if __name__ == "__main__":
    main()