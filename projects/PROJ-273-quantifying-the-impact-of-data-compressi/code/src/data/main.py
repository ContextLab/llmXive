"""
Main entry point for the Data Acquisition Pipeline (US1).

Orchestrates the download-inject-validate workflow to produce a validated dataset
of gravitational wave events with synthetic injections.

This script implements the logic for T016 and T015:
- Fetches real GW noise from GWOSC.
- Injects synthetic CBC signals using LALSimulation.
- Validates metadata and SNR.
- Stops after finding >= 12 valid events (with max 20 attempts).
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.batch_processor import run_injection_campaign
from src.utils.config import get_config, setup_logging

def main():
    """
    Orchestrates the download-inject-validate pipeline.
    
    This function:
    1. Loads configuration.
    2. Sets up logging.
    3. Calls the batch processor to fetch, inject, and validate events.
    4. Ensures the loop stops after >= 12 valid events or max attempts (20).
    5. Saves the final manifest of valid events.
    """
    # Load configuration
    config = get_config()
    
    # Setup logging
    log_dir = Path(config["paths"]["logs"])
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"data_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    setup_logging(log_file=log_file, level=config.get("logging", {}).get("level", "INFO"))
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Data Acquisition Pipeline (US1) - T016")
    logger.info(f"Configuration loaded: target_events={config['data']['target_events']}, min_valid_events={config['data']['min_valid_events']}")

    try:
        # Execute the injection campaign
        # This function encapsulates the logic from T015:
        # Loop: while valid_count < min_valid_events and attempts < max_attempts
        valid_events, total_attempts, summary = run_injection_campaign(
            target_events=config["data"]["target_events"],
            min_valid_events=config["data"]["min_valid_events"],
            max_attempts=config["data"]["max_attempts"],
            output_dir=Path(config["paths"]["interim"]),
            logger=logger
        )

        logger.info(f"Pipeline completed. Found {len(valid_events)} valid events out of {total_attempts} attempts.")

        # Save the manifest of valid events
        manifest_path = Path(config["paths"]["processed"]) / "valid_events_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        manifest_data = {
            "timestamp": datetime.now().isoformat(),
            "total_attempts": total_attempts,
            "valid_count": len(valid_events),
            "min_required": config["data"]["min_valid_events"],
            "events": valid_events
        }
        
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)
        
        logger.info(f"Valid events manifest saved to: {manifest_path}")

        # Check if we met the minimum requirement
        if len(valid_events) < config["data"]["min_valid_events"]:
            logger.error(f"CRITICAL: Failed to find {config['data']['min_valid_events']} valid events after {total_attempts} attempts.")
            # The run_injection_campaign should have already raised an error if max_attempts was hit,
            # but we double-check here for safety.
            raise RuntimeError(f"Pipeline failed: Only {len(valid_events)} valid events found, required {config['data']['min_valid_events']}.")

        logger.info("Data Acquisition Pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
