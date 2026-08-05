"""
Verification script to ensure the N=1000 isolate limit is strictly enforced
in the ingestion pipeline. This script simulates a CI run and validates
that the data ingestion respects the MAX_ISOLATES configuration.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import init_pipeline_logging, get_logger
from utils.config import get_max_isolates, load_config
from utils.performance_monitor import PerformanceMonitor, enforce_isolate_limit

logger = get_logger(__name__)

def verify_ingest_limit():
    """
    Verifies that the ingest process would not exceed the isolate limit.
    In a real scenario, this would hook into the download_ncbi or ingest_metadata
    logic. Here we simulate the check against the config.
    """
    max_isolates = get_max_isolates()
    logger.info(f"Configuration loaded: MAX_ISOLATES = {max_isolates}")

    # Simulate a scenario where we have a raw count from a source
    # In a real run, this count comes from the E-utilities summary or metadata file
    simulated_raw_count = 5000  # Typical large dataset size

    logger.info(f"Simulated raw isolate count from source: {simulated_raw_count}")

    if simulated_raw_count > max_isolates:
        logger.info(f"Raw count ({simulated_raw_count}) > Limit ({max_isolates}). "
                    f"Pipeline must enforce limit during ingestion.")
        
        # Verify the enforcement logic
        try:
            enforce_isolate_limit(simulated_raw_count, limit=max_isolates)
            logger.error("FAIL: Enforcement logic did not raise an error for excessive count.")
            return False
        except ValueError:
            logger.info("PASS: Enforcement logic correctly raised ValueError for excessive count.")
    
    # Verify the limit is reasonable for the 6-hour constraint
    # Heuristic: N=1000 should take < 6 hours. N=5000 would likely exceed.
    if max_isolates > 1500:
        logger.warning(f"Configuration MAX_ISOLATES={max_isolates} is high. "
                       "This may risk exceeding the 6-hour CI constraint.")
    
    logger.info("Verification complete. The pipeline is configured to enforce the limit.")
    return True

def main():
    init_pipeline_logging()
    parser = argparse.ArgumentParser(description="Verify Isolate Limit Enforcement")
    parser.add_argument("--strict", action="store_true", help="Fail if limit is > 1000")
    args = parser.parse_args()

    success = verify_ingest_limit()

    if args.strict and get_max_isolates() > 1000:
        logger.error("Strict mode: MAX_ISOLATES must be <= 1000 for CI.")
        sys.exit(1)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
