"""
Main orchestration script for the Download-Inject-Validate pipeline.

This script orchestrates the full workflow to:
1. Fetch real GW noise segments from GWOSC.
2. Inject synthetic CBC signals with known ground truth.
3. Validate metadata completeness (including spin/tilt).
4. Produce a final validated dataset of >= 15 events (per Amended FR-001).

It relies on the fetch_loop logic (T019.1) to ensure sufficient valid events
are found before proceeding.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Ensure code directory is in path for imports
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.fetch_loop import run_fetch_loop
from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error
from src.utils.config import get_project_root, ensure_dir, get_config

logger = get_logger(__name__)

# Configuration constants (matching Amended FR-001 and FR-009)
TARGET_VALID_EVENTS = 15
MAX_ATTEMPTS = 100
TIMEOUT_SECONDS = 300
MIN_VALID_FOR_ANALYSIS = 12

def main():
    log_step_start("T020", "Download-Inject-Validate Pipeline Orchestration")
    logger.info(f"Starting pipeline. Target: {TARGET_VALID_EVENTS} valid events, Max Attempts: {MAX_ATTEMPTS}")

    project_root = get_project_root()
    data_dir = project_root / "data"
    interim_dir = data_dir / "interim"
    processed_dir = data_dir / "processed"
    
    # Ensure output directories exist
    ensure_dir(interim_dir / "injections")
    ensure_dir(processed_dir)

    try:
        # Run the fetch-inject-validate loop
        # This function handles fetching noise, injecting signals, and validating metadata
        # It stops when >= TARGET_VALID_EVENTS are found or MAX_ATTEMPTS is reached.
        results = run_fetch_loop(
            target_count=TARGET_VALID_EVENTS,
            max_attempts=MAX_ATTEMPTS,
            timeout_seconds=TIMEOUT_SECONDS,
            output_dir=interim_dir / "injections"
        )

        valid_events = results.get("valid_events", [])
        total_attempts = results.get("total_attempts", 0)
        failed_attempts = results.get("failed_attempts", 0)

        logger.info(f"Pipeline completed. Total Attempts: {total_attempts}, Valid Events Found: {len(valid_events)}")

        # Post-loop validation (Amended FR-009)
        if len(valid_events) < MIN_VALID_FOR_ANALYSIS:
            error_msg = f"Insufficient valid events found after {total_attempts} attempts. Found {len(valid_events)}, required {MIN_VALID_FOR_ANALYSIS}."
            logger.error(error_msg)
            # Raise to fail loudly as per constraint 9
            raise RuntimeError(error_msg)

        # Generate final manifest
        manifest = {
            "pipeline_version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "target_count": TARGET_VALID_EVENTS,
            "max_attempts": MAX_ATTEMPTS,
            "total_attempts": total_attempts,
            "failed_attempts": failed_attempts,
            "valid_event_count": len(valid_events),
            "events": valid_events
        }

        manifest_path = processed_dir / "injection_campaign_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Final manifest written to {manifest_path}")
        log_step_complete("T020", "Pipeline successful", {
            "valid_events": len(valid_events),
            "manifest_path": str(manifest_path)
        })
        
        return 0

    except Exception as e:
        log_step_error("T020", str(e))
        logger.critical(f"Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
