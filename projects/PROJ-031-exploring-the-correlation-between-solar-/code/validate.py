"""
Validation module for checking data artifacts against schema definitions.

This module implements the blocking validation gate (T017) to ensure
that data files (like aligned_events.csv) strictly adhere to the
contract defined in contracts/aligned_event.schema.yaml.
"""

import os
import json
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import yaml
import pandas as pd
from jsonschema import validate, ValidationError, Draft7Validator
from jsonschema.exceptions import best_match

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SCHEMA_PATH = "contracts/aligned_event.schema.yaml"

def load_schema(schema_path: str = SCHEMA_PATH) -> Dict[str, Any]:
    """
    Load the JSON/YAML schema from the file system.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the schema cannot be parsed.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        return schema
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing schema file: {e}")

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a single record (dictionary) against the schema.
    
    Args:
        record: The data record to validate.
        schema: The schema definition.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        validate(instance=record, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Record validation failed: {e.message} at path: {list(e.path)}"

def validate_aligned_events(csv_path: str, schema_path: str = SCHEMA_PATH) -> Tuple[bool, List[str]]:
    """
    Validate an entire CSV file against the aligned event schema.
    
    Args:
        csv_path: Path to the CSV file to validate.
        schema_path: Path to the schema file.
        
    Returns:
        Tuple of (all_valid, list_of_errors).
        
    Raises:
        FileNotFoundError: If the CSV or schema file is missing.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    try:
        schema = load_schema(schema_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Schema loading failed: {e}")
        raise
    
    errors = []
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")
    
    # Convert DataFrame to list of dicts for validation
    records = df.to_dict('records')
    
    logger.info(f"Validating {len(records)} records against schema...")
    
    for i, record in enumerate(records):
        is_valid, error_msg = validate_record(record, schema)
        if not is_valid:
            errors.append(f"Row {i}: {error_msg}")
            # Fail fast on first error for blocking gate
            # But we collect a few to report context
            if len(errors) >= 5:
                errors.append("... (stopping after 5 errors)")
                break
    
    if errors:
        logger.error(f"Validation failed with {len(errors)} errors.")
        return False, errors
    
    logger.info("Validation passed: All records conform to the schema.")
    return True, []

def block_write_if_invalid(csv_path: str, schema_path: str = SCHEMA_PATH) -> bool:
    """
    Blocking validation gate. Returns True if valid, raises exception if invalid.
    
    This function is intended to be called before finalizing a write operation.
    If validation fails, it raises a ValueError to prevent writing invalid data.
    
    Args:
        csv_path: Path to the file to validate.
        schema_path: Path to the schema.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError: If validation fails.
    """
    is_valid, errors = validate_aligned_events(csv_path, schema_path)
    if not is_valid:
        error_details = "\n".join(errors[:10])
        raise ValueError(
            f"Validation Gate Failed: Data at {csv_path} does not conform to schema.\n"
            f"First few errors:\n{error_details}"
        )
    return True

def main():
    """
    Command-line entry point for validation.
    Usage: python code/validate.py <csv_path> [schema_path]
    """
    if len(sys.argv) < 2:
        print("Usage: python code/validate.py <csv_path> [schema_path]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    schema_path = sys.argv[2] if len(sys.argv) > 2 else SCHEMA_PATH
    
    try:
        is_valid, errors = validate_aligned_events(csv_path, schema_path)
        if is_valid:
            print(f"SUCCESS: {csv_path} is valid according to {schema_path}")
            sys.exit(0)
        else:
            print(f"FAILED: Validation errors found in {csv_path}")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
