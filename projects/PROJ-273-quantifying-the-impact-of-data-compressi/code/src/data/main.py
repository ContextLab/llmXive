"""
Main Orchestration Script for Data Pipeline (T020)

Orchestrates the download-inject-validate pipeline for >=15 target events
(per Amended FR-001) and produces the validated dataset.
Calls T019.1 logic (run_fetch_loop).
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

from src.utils.logging import setup_logging, get_logger, log_step_start, log_step_complete, log_step_error, log_metric
from src.utils.config import get_path, ensure_dir, set_seed
from src.data.fetch_loop import run_fetch_loop

# Configure logging
setup_logging()
logger = get_logger(__name__)

# Constants (Amended FR-001)
TARGET_EVENTS = 15
MIN_VALID_EVENTS = 12

def main():
    """
    Main entry point for the data pipeline.

    1. Initialize environment (seeds, directories).
    2. Run the fetch-inject-validate loop (T019.1).
    3. Aggregate results and save final validated dataset.
    """
    log_step_start(logger, "Data Pipeline Orchestration")

    try:
        # 1. Setup
        set_seed(42)  # Pin random seed for reproducibility
        data_root = get_path("data")
        ensure_dir(data_root)
        ensure_dir(get_path("data", "raw", "noise"))
        ensure_dir(get_path("data", "interim", "injections"))
        ensure_dir(get_path("data", "processed"))

        logger.info(f"Pipeline started at {datetime.now().isoformat()}")
        logger.info(f"Target events: {TARGET_EVENTS}, Minimum valid: {MIN_VALID_EVENTS}")

        # 2. Run the fetch loop (T019.1 logic)
        # Note: The loop is configured to aim for >=12 valid events,
        # but we aim for 15 in the orchestration if possible.
        # We pass target_events=15 to the loop, but the loop logic
        # (in fetch_loop.py) handles the max_attempts constraint.
        valid_events = run_fetch_loop(
            target_events=TARGET_EVENTS,
            max_attempts=20,
            timeout_per_attempt=300
        )

        # 3. Post-processing and Final Output
        final_count = len(valid_events)
        log_metric(logger, "total_valid_events", final_count)

        if final_count < MIN_VALID_EVENTS:
            logger.error(
                f"Pipeline terminated with only {final_count} valid events "
                f"(minimum required: {MIN_VALID_EVENTS}). "
                "Proceeding with warning, but downstream tasks may fail."
            )
            # We still proceed to save what we have, as per FR-001 fallback
        else:
            logger.info(f"Pipeline successfully generated {final_count} valid events.")

        # Save the final validated dataset (list of event paths + metadata)
        output_file = get_path("data", "processed", "validated_dataset.json")
        with open(output_file, "w") as f:
            json.dump(valid_events, f, indent=2)

        log_step_complete(logger, "Data Pipeline Orchestration")
        logger.info(f"Validated dataset saved to {output_file}")

        return valid_events

    except Exception as e:
        log_step_error(logger, f"Pipeline failed: {str(e)}")
        logger.exception(e)
        raise

if __name__ == "__main__":
    main()