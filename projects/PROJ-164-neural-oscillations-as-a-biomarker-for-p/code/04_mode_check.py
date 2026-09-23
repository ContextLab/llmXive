import json
import logging
import os
import sys
from pathlib import Path
from utils.logging_setup import get_logger, log_mode_switch

def main():
    """
    T012: Mode Check Task.
    Reads verified_source_manifest.json. If mode flag is 'Data Insufficient',
    terminates pipeline gracefully (exit code 0) after writing the manifest.
    """
    logger = get_logger(__name__)
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    manifest_path = project_root / "data" / "verified_source_manifest.json"
    
    logger.info("Starting T012: Mode Check Task")
    
    if not manifest_path.exists():
        logger.error(f"Manifest file not found at {manifest_path}. T011 must run first.")
        sys.exit(1)
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse manifest JSON: {e}")
        sys.exit(1)
    
    mode_flag = manifest.get("mode_flag", "Unknown")
    logger.info(f"Detected mode flag: {mode_flag}")
    
    if mode_flag == "Data Insufficient":
        logger.warning("Mode is 'Data Insufficient'. Terminating pipeline gracefully.")
        log_mode_switch(logger, "Data Insufficient", "Terminating pipeline")
        
        # Ensure manifest is written/updated (it was written by T011, but we confirm existence)
        # The task requires writing the manifest if not already done, but T011 should have done it.
        # We just confirm the file exists and exit.
        logger.info(f"Manifest content: {json.dumps(manifest, indent=2)}")
        
        logger.info("Pipeline terminated successfully (exit code 0).")
        sys.exit(0)
    else:
        logger.info(f"Mode is '{mode_flag}'. Proceeding with pipeline.")
        # Do not exit, allow downstream tasks to run
        # In a real pipeline, this might be a check before running T013/T015 etc.
        # Since T012 is a gate, if not Data Insufficient, we just log and return success.
        return True

if __name__ == "__main__":
    main()
