"""
Task T012c: Generate Exclusion Log
Reads exclusion counts from data/processed/exclusion_counts.json and writes
a formatted exclusion log to data/processed/exclusion_log.json.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Import shared utilities from the project's utils module
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Project root relative to this file (assuming code/ is in root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXCLUSION_COUNTS_PATH = PROCESSED_DIR / "exclusion_counts.json"
EXCLUSION_LOG_PATH = PROCESSED_DIR / "exclusion_log.json"

def load_exclusion_counts(path: Path) -> Dict[str, int]:
    """Load exclusion counts from JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Exclusion counts file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_simulation_fallback() -> bool:
    """
    Check if simulation fallback was used.
    This checks for the presence of 'SIMULATION_MODE' in metadata or environment.
    For this task, we check a flag in the exclusion counts or a metadata file.
    """
    metadata_path = PROJECT_ROOT / "data" / "raw" / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            return metadata.get("simulation_mode", False)
    
    # Fallback: check environment variable if metadata is missing
    import os
    return os.getenv("SIMULATION_MODE", "false").lower() == "true"

def generate_exclusion_log(counts: Dict[str, int], is_simulation: bool) -> Dict[str, Any]:
    """
    Generate the exclusion log dictionary.
    Keys: ERR_MISSING_AGE_FIELD, ERR_MISSING_SCORE, ERR_MMSE_IMPAIRED, SIMULATION_FALLBACK
    """
    log_entry = {
        "timestamp": get_timestamp(),
        "source": str(EXCLUSION_COUNTS_PATH),
        "counts": {
            "ERR_MISSING_AGE_FIELD": counts.get("ERR_MISSING_AGE_FIELD", 0),
            "ERR_MISSING_SCORE": counts.get("ERR_MISSING_SCORE", 0),
            "ERR_MMSE_IMPAIRED": counts.get("ERR_MMSE_IMPAIRED", 0),
        },
        "SIMULATION_FALLBACK": is_simulation,
        "total_excluded": sum(counts.values()),
        "notes": "Exclusion log generated from aggregation of T012a, T012b, T012e."
    }
    return log_entry

def save_exclusion_log(log_data: Dict[str, Any], path: Path) -> None:
    """Save the exclusion log to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)
    log_info(f"Exclusion log saved to {path}")

def main() -> int:
    """Main entry point for T012c."""
    setup_logging()
    log_info("Starting T012c: Generate Exclusion Log")

    try:
        # Load existing counts
        counts = load_exclusion_counts(EXCLUSION_COUNTS_PATH)
        log_info(f"Loaded exclusion counts: {counts}")

        # Check for simulation fallback
        is_simulation = check_simulation_fallback()
        if is_simulation:
            log_warning("SIMULATION_FALLBACK detected. Logging accordingly.")
        else:
            log_info("Real data mode detected.")

        # Generate log
        log_data = generate_exclusion_log(counts, is_simulation)

        # Save log
        save_exclusion_log(log_data, EXCLUSION_LOG_PATH)

        log_info("T012c completed successfully.")
        return 0

    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        log_error(f"JSON decode error: {e}")
        return 1
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
