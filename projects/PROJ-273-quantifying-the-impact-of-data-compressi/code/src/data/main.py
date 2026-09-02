"""
Main orchestration script for the Download-Inject-Validate pipeline (User Story 1).

This script orchestrates the loop to:
1. Fetch real GW noise segments from GWOSC.
2. Inject synthetic CBC signals using LALSimulation with known ground truth.
3. Validate metadata completeness (specifically spin/tilt angles).

It repeats this process until >= 5 valid events are found or max_attempts is reached.

Per Amended FR-001: If < 5 valid events are found after max_attempts, raises RuntimeError.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.fetch_loop import run_fetch_loop
from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error
from src.utils.config import get_project_root, ensure_dir

logger = get_logger(__name__)

def main():
    """
    Orchestrates the full download-inject-validate pipeline.
    
    Target: >= 5 valid events with complete spin metadata.
    Max Attempts: 50 (per Amended FR-001).
    """
    log_step_start("T020: Orchestrate Download-Inject-Validate Pipeline")
    
    project_root = get_project_root()
    output_dir = project_root / "data" / "processed" / "valid_injections"
    ensure_dir(output_dir)
    
    # Configuration
    target_valid_events = 5
    max_attempts = 50
    batch_size = 1  # Process one by one to validate immediately
    
    logger.info(f"Starting pipeline: target={target_valid_events}, max_attempts={max_attempts}")
    
    try:
        # Run the fetch-inject-validate loop
        # This function handles fetching, injecting, validating, and looping
        results = run_fetch_loop(
            target_valid_events=target_valid_events,
            max_attempts=max_attempts,
            batch_size=batch_size,
            output_dir=output_dir
        )
        
        valid_count = results.get("valid_count", 0)
        total_attempts = results.get("total_attempts", 0)
        event_ids = results.get("event_ids", [])
        
        logger.info(f"Pipeline completed. Total attempts: {total_attempts}, Valid events found: {valid_count}")
        
        # Save summary report
        summary_path = output_dir / "pipeline_summary.json"
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "target_valid_events": target_valid_events,
            "max_attempts": max_attempts,
            "total_attempts": total_attempts,
            "valid_count": valid_count,
            "event_ids": event_ids,
            "status": "success" if valid_count >= target_valid_events else "failed"
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"Summary saved to {summary_path}")
        
        if valid_count < target_valid_events:
            error_msg = f"Pipeline failed to find {target_valid_events} valid events. Found {valid_count} after {max_attempts} attempts."
            log_step_error("T020", error_msg)
            raise RuntimeError(error_msg)
        
        log_step_complete("T020: Pipeline completed successfully")
        return 0

    except Exception as e:
        log_step_error("T020", str(e))
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main() if main() is None else main())
