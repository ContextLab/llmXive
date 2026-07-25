"""
Script to inject specific random seeds used during a run into data/run_log.json
and verify them against code/config.yaml.

This implements task T004b.
"""
import argparse
import json
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from code.src.utils.config import load_config
from code.src.utils.reproducibility import generate_run_id, ensure_data_directory

def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_existing_log(log_path: Path) -> dict:
    """Load existing log if it exists, otherwise return empty structure."""
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not read existing log file: {e}. Starting fresh.")
    return {}

def verify_seeds(config: dict, seeds: dict) -> str:
    """
    Verify that the seeds in the log match the configuration.
    Returns "PASS" or "FAIL".
    """
    expected_seeds = {
        "global": config.get("global_seed"),
        "generator": config.get("generator_seed"),
        "simulation": config.get("simulation_seed")
    }

    if not expected_seeds:
        logging.error("Configuration missing required seed keys.")
        return "FAIL"

    for key, expected_value in expected_seeds.items():
        if key not in seeds:
            logging.error(f"Seed '{key}' missing from injected seeds.")
            return "FAIL"
        if seeds[key] != expected_value:
            logging.error(f"Seed mismatch for '{key}': expected {expected_value}, got {seeds[key]}")
            return "FAIL"

    return "PASS"

def main():
    parser = argparse.ArgumentParser(
        description="Inject and verify random seeds in run_log.json"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to the configuration file (default: code/config.yaml)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/run_log.json",
        help="Path to the output log file (default: data/run_log.json)"
    )
    args = parser.parse_args()

    logger = setup_logging()
    logger.info(f"Starting seed injection and verification process.")

    # Load configuration
    try:
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = project_root / config_path
        
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)

        config = load_config(str(config_path))
        logger.info(f"Configuration loaded from {config_path}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Extract seeds from config
    seeds = {
        "global": config.get("global_seed"),
        "generator": config.get("generator_seed"),
        "simulation": config.get("simulation_seed")
    }

    # Validate seeds exist in config
    if any(v is None for v in seeds.values()):
        logger.error("Configuration is missing required seed values (global_seed, generator_seed, simulation_seed).")
        sys.exit(1)

    # Generate run ID
    run_id = generate_run_id()
    logger.info(f"Generated run ID: {run_id}")

    # Verify seeds against config
    verification_status = verify_seeds(config, seeds)
    logger.info(f"Verification status: {verification_status}")

    # Prepare log entry
    log_entry = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seeds": seeds,
        "verification_status": verification_status
    }

    # Handle existing log (append or create)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    ensure_data_directory(output_path)

    existing_log = load_existing_log(output_path)
    
    # If it's a list, append; if dict, we might need to convert or wrap
    if isinstance(existing_log, list):
        existing_log.append(log_entry)
    elif isinstance(existing_log, dict) and "runs" in existing_log:
        existing_log["runs"].append(log_entry)
    else:
        # Start fresh list
        existing_log = [log_entry]

    # Write updated log
    try:
        with open(output_path, 'w') as f:
            json.dump(existing_log, f, indent=2)
        logger.info(f"Successfully wrote run log to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write run log: {e}")
        sys.exit(1)

    # Exit with error if verification failed
    if verification_status == "FAIL":
        logger.error("Seed verification failed. Exiting with error code.")
        sys.exit(1)

    logger.info("Seed injection and verification completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
