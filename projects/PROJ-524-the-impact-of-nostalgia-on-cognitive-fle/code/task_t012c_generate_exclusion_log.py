"""
Task T012c: Generate Exclusion Log

Reads exclusion counts from data/processed/exclusion_counts.json (produced by T012a, T012b, T012e)
and writes a consolidated exclusion log to data/processed/exclusion_log.json.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXCLUSION_COUNTS_PATH = PROCESSED_DIR / "exclusion_counts.json"
EXCLUSION_LOG_PATH = PROCESSED_DIR / "exclusion_log.json"
METADATA_PATH = PROJECT_ROOT / "data" / "raw" / "metadata.json"

def load_exclusion_counts() -> Dict[str, int]:
    """Load exclusion counts from the intermediate JSON file."""
    if not EXCLUSION_COUNTS_PATH.exists():
        log_error(f"Exclusion counts file not found: {EXCLUSION_COUNTS_PATH}")
        raise FileNotFoundError(f"Exclusion counts file not found: {EXCLUSION_COUNTS_PATH}")

    with open(EXCLUSION_COUNTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_simulation_fallback() -> bool:
    """
    Check if the pipeline ran in simulation mode by reading data/raw/metadata.json.
    Returns True if simulation_mode is True, False otherwise.
    """
    if not METADATA_PATH.exists():
        log_warning(f"Metadata file not found: {METADATA_PATH}. Assuming no simulation fallback.")
        return False

    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    return metadata.get("simulation_mode", False)

def generate_exclusion_log() -> Dict[str, Any]:
    """
    Generate the final exclusion log combining counts and simulation status.
    """
    counts = load_exclusion_counts()
    is_simulation = check_simulation_fallback()

    log_entry = {
        "timestamp": get_timestamp(),
        "task_id": "T012c",
        "exclusion_counts": {
            "ERR_MISSING_AGE_FIELD": counts.get("ERR_MISSING_AGE_FIELD", 0),
            "ERR_MISSING_SCORE": counts.get("ERR_MISSING_SCORE", 0),
            "ERR_MMSE_IMPAIRED": counts.get("ERR_MMSE_IMPAIRED", 0),
        },
        "SIMULATION_FALLBACK": is_simulation
    }

    return log_entry

def main():
    """Main entry point for Task T012c."""
    setup_logging("T012c_generate_exclusion_log")
    log_info("Starting T012c: Generate Exclusion Log")

    try:
        log_entry = generate_exclusion_log()

        # Ensure directory exists
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        # Write the log
        with open(EXCLUSION_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2)

        log_info(f"Successfully wrote exclusion log to {EXCLUSION_LOG_PATH}")
        log_info(f"Exclusion Counts: {log_entry['exclusion_counts']}")
        log_info(f"Simulation Fallback Active: {log_entry['SIMULATION_FALLBACK']}")

    except FileNotFoundError as e:
        log_error(f"Required file missing: {e}")
        raise
    except json.JSONDecodeError as e:
        log_error(f"JSON parsing error in exclusion counts: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error during exclusion log generation: {e}")
        raise

    log_info("T012c completed successfully.")

if __name__ == "__main__":
    main()
