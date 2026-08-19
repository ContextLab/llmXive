"""
Main orchestration script for the Download-Inject-Validate pipeline (User Story 1).

This script implements the logic to fetch real GW noise segments from GWOSC,
inject synthetic CBC signals with known ground truth, and validate the resulting
datasets until a target number of valid events (>=12) is reached or max attempts (20)
is exhausted, as per Amended FR-001.

Output:
    - data/processed/validated_events.json: List of validated event metadata.
    - data/processed/validated_events/: Directory containing individual event files.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.data.fetch_loop import run_fetch_loop
from src.utils.logging import setup_logging, get_logger, log_step_start, log_step_complete, log_step_error
from src.utils.config import get_project_root, ensure_dir, get_path

def main():
    """
    Orchestrates the download-inject-validate pipeline.
    
    Steps:
    1. Initialize logging and configuration.
    2. Ensure output directories exist.
    3. Run the fetch loop (T019.1 logic) to gather >=12 valid events.
    4. Aggregate results into a final manifest.
    5. Save the manifest to disk.
    """
    # Setup logging
    setup_logging(level=logging.INFO)
    logger = get_logger("T020-main")
    
    log_step_start(logger, "Pipeline Orchestration", "T020")
    
    try:
        # 1. Configuration & Paths
        project_root = get_project_root()
        data_processed_dir = project_root / "data" / "processed"
        ensure_dir(data_processed_dir)
        
        output_manifest_path = data_processed_dir / "validated_events.json"
        output_events_dir = data_processed_dir / "validated_events"
        ensure_dir(output_events_dir)
        
        logger.info(f"Output manifest will be written to: {output_manifest_path}")
        logger.info(f"Output events directory: {output_events_dir}")
        
        # 2. Execute the Fetch Loop (T019.1)
        # Parameters per Amended FR-001:
        # - Target valid events: >= 12 (minimum)
        # - Max attempts: 20
        # - Batch size: 1 (fetch one by one)
        # - Timeout: 300s per attempt (handled inside fetch_loop)
        
        target_valid_count = 12
        max_attempts = 20
        batch_size = 1
        
        logger.info(f"Starting fetch loop: target={target_valid_count}, max_attempts={max_attempts}, batch_size={batch_size}")
        
        # run_fetch_loop returns a tuple: (list_of_valid_events, stats_dict)
        # It handles the logic of fetching, injecting, validating, and looping.
        valid_events, stats = run_fetch_loop(
            target_valid_count=target_valid_count,
            max_attempts=max_attempts,
            batch_size=batch_size,
            output_dir=output_events_dir,
            logger=logger
        )
        
        logger.info(f"Fetch loop completed. Found {len(valid_events)} valid events.")
        
        # 3. Final Validation & Reporting
        if len(valid_events) < 1:
            error_msg = "Pipeline failed: No valid events were generated."
            logger.error(error_msg)
            log_step_error(logger, "Pipeline Orchestration", error_msg)
            raise RuntimeError(error_msg)
        
        if len(valid_events) < target_valid_count:
            warning_msg = (
                f"Pipeline completed with reduced sample size: {len(valid_events)} valid events "
                f"(target was {target_valid_count}). Proceeding with available data as per FR-001 fallback."
            )
            logger.warning(warning_msg)
        
        # 4. Save Manifest
        manifest = {
            "pipeline_version": "1.0.0",
            "execution_timestamp": datetime.utcnow().isoformat(),
            "parameters": {
                "target_valid_count": target_valid_count,
                "max_attempts": max_attempts,
                "batch_size": batch_size
            },
            "statistics": stats,
            "valid_events_count": len(valid_events),
            "events": valid_events
        }
        
        with open(output_manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Successfully wrote manifest to {output_manifest_path}")
        log_step_complete(logger, "Pipeline Orchestration", "T020")
        
        return 0

    except Exception as e:
        log_step_error(logger, "Pipeline Orchestration", str(e))
        logger.exception("Unhandled exception in main pipeline")
        return 1

if __name__ == "__main__":
    sys.exit(main())