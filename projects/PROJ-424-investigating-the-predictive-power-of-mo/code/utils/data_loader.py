"""
Data loader for experimental diffusion coefficients.
Loads and validates the curated NIST references JSON file.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Import from project config
try:
    from config import NIST_REFS_PATH
except ImportError:
    # Fallback for direct execution or different import context
    from pathlib import Path
    NIST_REFS_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "nist_refs.json"


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


def validate_nist_refs_schema(data: List[Dict[str, Any]]) -> None:
    """
    Validates the schema of the NIST references data.
    
    Args:
        data: List of dictionaries containing diffusion coefficient data.
        
    Raises:
        DataValidationError: If the schema is invalid.
    """
    if not isinstance(data, list):
        raise DataValidationError("NIST references data must be a list.")
    
    required_fields = {"solvent", "temperature", "value"}
    
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise DataValidationError(f"Entry {i} must be a dictionary.")
        
        missing_fields = required_fields - set(entry.keys())
        if missing_fields:
            raise DataValidationError(
                f"Entry {i} is missing required fields: {missing_fields}"
            )
        
        # Validate types
        if not isinstance(entry["solvent"], str):
            raise DataValidationError(f"Entry {i}: 'solvent' must be a string.")
        
        if not isinstance(entry["temperature"], (int, float)):
            raise DataValidationError(f"Entry {i}: 'temperature' must be a number.")
        
        if not isinstance(entry["value"], (int, float)):
            raise DataValidationError(f"Entry {i}: 'value' must be a number.")
        
        # Validate ranges
        if entry["value"] <= 0:
            raise DataValidationError(
                f"Entry {i}: 'value' must be positive (got {entry['value']})."
            )
        
        if entry["temperature"] <= 0:
            raise DataValidationError(
                f"Entry {i}: 'temperature' must be positive (got {entry['temperature']})."
            )


def load_nist_references() -> List[Dict[str, Any]]:
    """
    Loads experimental diffusion coefficients from the curated NIST JSON file.
    
    This function implements the 'manual curation' strategy. It reads the 
    pre-curated file `data/raw/nist_refs.json`. It does NOT attempt network fetches.
    
    Returns:
        List[Dict[str, Any]]: Validated list of diffusion coefficient records.
        
    Raises:
        FileNotFoundError: If the NIST references file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        DataValidationError: If the data schema is invalid.
    """
    if not isinstance(NIST_REFS_PATH, Path):
        NIST_REFS_PATH = Path(NIST_REFS_PATH)
        
    if not NIST_REFS_PATH.exists():
        raise FileNotFoundError(
            f"NIST references file not found at: {NIST_REFS_PATH}. "
            "Please ensure the file exists and contains valid experimental data."
        )
    
    try:
        with open(NIST_REFS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in NIST references file: {e.msg}", e.doc, e.pos
        )
    
    # Validate schema
    validate_nist_refs_schema(data)
    
    return data


def main():
    """
    Entry point for script execution.
    Loads the data and prints a summary to stdout.
    """
    try:
        data = load_nist_references()
        print(f"Successfully loaded {len(data)} experimental diffusion coefficient records.")
        
        # Print a sample
        if data:
            print("\nSample record:")
            print(json.dumps(data[0], indent=2))
            
        return data
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except DataValidationError as e:
        print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
