"""
T013b: Load pre-computed DFT energies from data/raw/dft_energies.json.

This script validates the schema (keys: system, energy_eV, temperature) and
raises an error if the file is missing or malformed, unless spec-amendment
T018a permits a placeholder.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import DATA_RAW_PATH
from code.errors import DataLoadError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_KEYS = {'system', 'energy_eV', 'temperature'}
DFT_FILE_NAME = "dft_energies.json"
NO_DATA_PLACEHOLDER_NAME = "dft_energies_no_data.json"

def load_dft_energies() -> List[Dict[str, Any]]:
    """
    Load and validate DFT energies from the JSON file.
    
    Returns:
        List[Dict[str, Any]]: Validated list of DFT energy entries.
    
    Raises:
        DataLoadError: If file is missing, malformed, or lacks required keys,
                       and no spec-amendment placeholder is found.
    """
    dft_file_path = DATA_RAW_PATH / DFT_FILE_NAME
    no_data_placeholder_path = DATA_RAW_PATH / NO_DATA_PLACEHOLDER_NAME

    # Check for spec-amendment T018a placeholder first
    if no_data_placeholder_path.exists():
        logger.warning(f"Spec-amendment T018a placeholder found: {no_data_placeholder_path}")
        with open(no_data_placeholder_path, 'r') as f:
            placeholder_data = json.load(f)
        
        if placeholder_data.get('status') == 'no_data':
            reason = placeholder_data.get('reason', 'unknown')
            logger.info(f"No DFT data available (Reason: {reason}). Returning empty list.")
            return []
        else:
            logger.warning("Placeholder found but status is not 'no_data'. Proceeding with validation.")

    # Try to load the real DFT data
    if not dft_file_path.exists():
        error_msg = f"DFT energies file not found: {dft_file_path}"
        logger.error(error_msg)
        raise DataLoadError(error_msg)

    try:
        with open(dft_file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Malformed JSON in DFT energies file: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg)
    except IOError as e:
        error_msg = f"IO Error reading DFT energies file: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg)

    if not isinstance(data, list):
        error_msg = f"DFT energies file must contain a list, got {type(data)}"
        logger.error(error_msg)
        raise DataLoadError(error_msg)

    validated_entries = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            error_msg = f"Entry {i} in DFT energies file is not a dictionary"
            logger.error(error_msg)
            raise DataLoadError(error_msg)

        missing_keys = REQUIRED_KEYS - set(entry.keys())
        if missing_keys:
            error_msg = f"Entry {i} in DFT energies file is missing required keys: {missing_keys}"
            logger.error(error_msg)
            raise DataLoadError(error_msg)

        # Basic type validation
        if not isinstance(entry['system'], str):
            error_msg = f"Entry {i}: 'system' must be a string"
            logger.error(error_msg)
            raise DataLoadError(error_msg)
        
        if not isinstance(entry['energy_eV'], (int, float)):
            error_msg = f"Entry {i}: 'energy_eV' must be a number"
            logger.error(error_msg)
            raise DataLoadError(error_msg)
        
        if not isinstance(entry['temperature'], (int, float)):
            error_msg = f"Entry {i}: 'temperature' must be a number"
            logger.error(error_msg)
            raise DataLoadError(error_msg)

        validated_entries.append(entry)
        logger.debug(f"Validated entry {i}: {entry['system']} at {entry['temperature']}K")

    logger.info(f"Successfully loaded {len(validated_entries)} DFT energy entries.")
    return validated_entries

def main():
    """Main entry point for the script."""
    try:
        data = load_dft_energies()
        logger.info("DFT energy loading completed successfully.")
        # For demonstration/verification, print a summary
        if data:
            logger.info(f"Sample entry: {data[0]}")
        else:
            logger.info("No DFT data loaded (placeholder or empty source).")
    except DataLoadError as e:
        logger.error(f"Failed to load DFT energies: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during DFT energy loading: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()