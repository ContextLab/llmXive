"""
T012: Mode Check Task

Reads verified_source_manifest.json. If mode flag is 'Data Insufficient',
terminates pipeline gracefully (exit code 0) after writing the manifest.
No further tasks are executed.

Dependencies: T011 (Source Verification)
"""
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_setup import get_logger, log_mode_switch

# Setup logging
logger = get_logger(__name__)

MANIFEST_PATH = project_root / "data" / "verified_source_manifest.json"

def main():
    """
    Main entry point for T012 Mode Check.
    """
    if not MANIFEST_PATH.exists():
        logger.error(f"Manifest file not found: {MANIFEST_PATH}")
        logger.error("T011 (Source Verification) must complete successfully before T012.")
        sys.exit(1)

    try:
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse manifest JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error reading manifest: {e}")
        sys.exit(1)

    # Extract mode flag
    # The manifest structure from T011 is expected to have a 'mode' or 'status' field
    # based on the description: "If none found, log 'Data Insufficient'... and set mode flag"
    mode = manifest.get("mode", manifest.get("status", "Unknown"))
    
    logger.info(f"Read manifest from {MANIFEST_PATH}")
    logger.info(f"Current pipeline mode: {mode}")

    if mode == "Data Insufficient":
        logger.warning("Data Insufficient Mode detected. No single-source paired dataset found.")
        log_mode_switch("Data Insufficient", "Terminating pipeline as per protocol.")
        logger.info("Pipeline terminated gracefully (exit code 0) as no further tasks can be executed.")
        sys.exit(0)
    
    elif mode == "Primary":
        logger.info("Primary Mode detected. Data exists. Proceeding to next tasks.")
        # If we are here, we do not terminate. The script exits successfully (0)
        # allowing the pipeline to continue to T009 or T013.
        sys.exit(0)
    
    else:
        logger.error(f"Unknown mode flag found in manifest: {mode}")
        logger.error("Cannot determine pipeline flow. Halting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
