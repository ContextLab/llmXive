"""
T012c: Generate Exclusion Log

Reads exclusion counts from data/processed/exclusion_counts.json (accumulated from T012a, T012b, T012e)
and writes a consolidated exclusion log to data/processed/exclusion_log.json.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Import shared utilities from the project structure
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Constants
EXCLUSION_COUNTS_PATH = "data/processed/exclusion_counts.json"
EXCLUSION_LOG_PATH = "data/processed/exclusion_log.json"
METADATA_PATH = "data/raw/metadata.json"

def load_exclusion_counts(path: str) -> Dict[str, Any]:
    """Load exclusion counts from the JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Exclusion counts file not found: {p.absolute()}")
    
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    log_info(f"Loaded exclusion counts from {p.absolute()}")
    return data

def check_simulation_fallback() -> bool:
    """
    Check if simulation fallback was triggered by reading metadata.
    Returns True if simulation_mode is True in data/raw/metadata.json.
    """
    p = Path(METADATA_PATH)
    if not p.exists():
        log_warning(f"Metadata file not found at {p.absolute()}. Assuming no simulation fallback.")
        return False
    
    with open(p, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    is_simulation = metadata.get("simulation_mode", False)
    if is_simulation:
        log_info("Simulation fallback detected in metadata.")
    return is_simulation

def generate_exclusion_log(counts: Dict[str, Any], is_simulation: bool) -> Dict[str, Any]:
    """
    Generate the final exclusion log structure.
    Ensures all required keys are present.
    """
    log_entry = {
        "timestamp": get_timestamp(),
        "counts": {
            "ERR_MISSING_AGE_FIELD": counts.get("ERR_MISSING_AGE_FIELD", 0),
            "ERR_MISSING_SCORE": counts.get("ERR_MISSING_SCORE", 0),
            "ERR_MMSE_IMPAIRED": counts.get("ERR_MMSE_IMPAIRED", 0),
            "SIMULATION_FALLBACK": 1 if is_simulation else 0
        },
        "total_excluded": (
            counts.get("ERR_MISSING_AGE_FIELD", 0) + 
            counts.get("ERR_MISSING_SCORE", 0) + 
            counts.get("ERR_MMSE_IMPAIRED", 0)
        )
    }
    return log_entry

def save_exclusion_log(log_data: Dict[str, Any], path: str) -> None:
    """Write the exclusion log to disk."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    
    log_info(f"Exclusion log saved to {p.absolute()}")

def main():
    """Main entry point for T012c."""
    setup_logging()
    log_info("Starting T012c: Generate Exclusion Log")
    
    try:
        # 1. Load accumulated exclusion counts
        counts = load_exclusion_counts(EXCLUSION_COUNTS_PATH)
        
        # 2. Check for simulation fallback flag
        is_simulation = check_simulation_fallback()
        
        # 3. Generate the log structure
        log_data = generate_exclusion_log(counts, is_simulation)
        
        # 4. Save the log
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
        log_error(f"Unexpected error in T012c: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
