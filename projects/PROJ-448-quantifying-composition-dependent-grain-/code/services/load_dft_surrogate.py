import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.config import DATA_RAW_PATH, PROCESSED_PATH, get_logger
from code.errors import DataLoadError, ConfigurationError

logger = get_logger(__name__)

PLACEHOLDER_FLAG_KEY = "MISSING_SOURCE"
PLACEHOLDER_FILE_PATH = DATA_RAW_PATH / "dft_energies.json"
OUTPUT_FILE_PATH = PROCESSED_PATH / "surrogate_energies.json"

def check_placeholder_flag(file_path: Path) -> bool:
    """
    Checks if the DFT energies file contains the MISSING_SOURCE flag.
    Returns True if the flag is present (indicating data is missing/placeholder).
    Returns False if the file exists and is valid data.
    """
    if not file_path.exists():
        logger.warning(f"Placeholder check: File {file_path} does not exist.")
        return False  # No flag present if file missing, though this might be an error elsewhere

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get(PLACEHOLDER_FLAG_KEY, False) is True
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read placeholder check file {file_path}: {e}")
        # If we can't read it, we assume it's not a valid "missing" marker file,
        # but the downstream load will fail anyway.
        return False

def validate_dft_structure(data: Dict[str, Any]) -> bool:
    """
    Validates the structure of the loaded DFT energy data.
    Expects a list of records or a dictionary containing a 'data' list.
    Each record must have: system, element, energy_eV, temperature_K.
    """
    records = data.get("data", []) if isinstance(data, dict) else data
    
    if not isinstance(records, list):
        logger.error("DFT data must be a list of records or a dict with a 'data' key.")
        return False

    if not records:
        logger.warning("DFT data list is empty.")
        return False

    required_keys = {"system", "element", "energy_eV", "temperature_K"}
    
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            logger.error(f"Record {i} is not a dictionary.")
            return False
        
        if not required_keys.issubset(record.keys()):
            missing = required_keys - set(record.keys())
            logger.error(f"Record {i} missing keys: {missing}")
            return False

        # Type checks
        if not isinstance(record["system"], str):
            logger.error(f"Record {i} 'system' must be string.")
            return False
        if not isinstance(record["element"], str):
            logger.error(f"Record {i} 'element' must be string.")
            return False
        if not isinstance(record["energy_eV"], (int, float)):
            logger.error(f"Record {i} 'energy_eV' must be numeric.")
            return False
        if not isinstance(record["temperature_K"], int):
            logger.error(f"Record {i} 'temperature_K' must be integer.")
            return False

    return True

def load_and_validate(file_path: Path) -> Dict[str, Any]:
    """
    Loads the DFT energies JSON file and validates its structure.
    Raises DataLoadError if validation fails.
    """
    if not file_path.exists():
        raise DataLoadError(f"DFT energies file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataLoadError(f"Invalid JSON in DFT energies file: {e}")
    except IOError as e:
        raise DataLoadError(f"IO Error reading DFT energies file: {e}")

    if not validate_dft_structure(data):
        raise DataLoadError("DFT energies data structure validation failed.")

    return data

def save_surrogate_energies(data: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the validated DFT energies to the processed surrogate file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Surrogate energies saved to {output_path}")

def main() -> int:
    """
    Main entry point for T013: Load DFT Surrogate.
    1. Checks for MISSING_SOURCE flag in raw data.
    2. If flag is present, aborts with error.
    3. If flag is absent, loads, validates, and saves to processed.
    """
    logger.info("Starting DFT Surrogate Loader (T013).")

    # Step 1: Check Placeholder Flag
    if check_placeholder_flag(PLACEHOLDER_FILE_PATH):
        error_msg = (
            "CRITICAL: DFT data source is missing (MISSING_SOURCE flag detected). "
            "The scientific pipeline cannot proceed without valid pre-computed DFT energies. "
            "Please ensure a real data source is fetched (T045f-Fetch) and the placeholder "
            "file is replaced."
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return 1

    logger.info("Placeholder check passed. No MISSING_SOURCE flag found.")

    # Step 2: Load and Validate
    try:
        data = load_and_validate(PLACEHOLDER_FILE_PATH)
    except DataLoadError as e:
        logger.critical(f"Failed to load or validate DFT data: {e}")
        return 1

    # Step 3: Save to Processed
    try:
        save_surrogate_energies(data, OUTPUT_FILE_PATH)
    except IOError as e:
        logger.critical(f"Failed to write surrogate energies: {e}")
        return 1

    logger.info("T013 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())