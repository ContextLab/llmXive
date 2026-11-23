"""
Main orchestration script for the Data Acquisition Pipeline.

This script implements the download-inject-validate pipeline to produce
a validated dataset of >=5 synthetic CBC injections with complete metadata.

Per Amended FR-001 and FR-009:
- Fetches real GW noise from GWOSC.
- Injects synthetic signals using LALSimulation (via src.data.inject).
- Validates metadata completeness (specifically tilt_angle).
- Stops when >=5 valid events are found or max_attempts (50) is reached.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error
from src.utils.config import get_project_root, ensure_dir, set_seed
from src.data.fetch_loop import run_fetch_loop

logger = get_logger(__name__)

def main():
    """
    Orchestrate the download-inject-validate pipeline.
    
    1. Initialize environment and logging.
    2. Run the fetch loop (T019.1 logic) to acquire >=5 valid events.
    3. Save the list of valid event IDs to data/interim/valid_events.json.
    4. Exit with appropriate status code.
    """
    # Setup
    set_seed(42) # Pinning random seed as per T004
    project_root = get_project_root()
    interim_dir = project_root / "data" / "interim"
    ensure_dir(interim_dir)
    
    output_file = interim_dir / "valid_events.json"
    
    log_step_start("Data Pipeline Orchestration", {"target_events": 5, "max_attempts": 50})

    try:
        # Execute the core logic from T019.1
        # This function handles the loop: fetch -> inject -> validate -> check count
        valid_events = run_fetch_loop(
            target_count=5,
            max_attempts=50,
            output_dir=interim_dir
        )
        
        if not valid_events:
            # This should technically raise RuntimeError inside run_fetch_loop if count < 5
            # but we handle the empty case here for safety.
            raise RuntimeError("Pipeline completed but no valid events were found.")
        
        # Save results
        result_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_ids": [evt["event_id"] for evt in valid_events],
            "count": len(valid_events),
            "details": valid_events
        }
        
        with open(output_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        logger.info(f"Pipeline successful. Found {len(valid_events)} valid events.")
        logger.info(f"Results saved to {output_file}")
        
        log_step_complete("Data Pipeline Orchestration", {"valid_events_count": len(valid_events)})
        
        return 0

    except RuntimeError as e:
        log_step_error("Data Pipeline Orchestration", str(e))
        logger.error(f"Pipeline failed: {e}")
        return 1
    except Exception as e:
        log_step_error("Data Pipeline Orchestration", str(e), exc_info=True)
        logger.critical(f"Unexpected error in pipeline: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
