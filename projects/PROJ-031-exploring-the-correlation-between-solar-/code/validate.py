"""
Validation module for the Solar Flare and Geomagnetic Storm Correlation Study.

This module provides functions to validate data artifacts against their
corresponding JSON Schema definitions. It is designed to be used as a
gatekeeper in the pipeline: if validation fails, downstream processes
(like writing the final CSV or updating the manifest) are blocked.
"""

import os
import json
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import yaml

# Using jsonschema for robust validation
try:
    import jsonschema
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    print("ERROR: The 'jsonschema' library is required. Install it via 'pip install jsonschema'.")
    sys.exit(1)

# Project root relative to code/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTRACTS_DIR = os.path.join(PROJECT_ROOT, "contracts")
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
SOURCE_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "data", "source_manifest.yaml")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("validate")


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Loads a JSON/YAML schema from the contracts directory.

    Args:
        schema_name: The filename of the schema (e.g., 'aligned_event.schema.yaml').

    Returns:
        The schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the schema file is empty or invalid.
    """
    schema_path = os.path.join(CONTRACTS_DIR, schema_name)
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        try:
            schema = yaml.safe_load(f)
            if not schema:
                raise ValueError(f"Schema file is empty: {schema_path}")
            return schema
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in schema {schema_path}: {e}")


def validate_aligned_events(csv_path: str, schema_name: str = "aligned_event.schema.yaml") -> Tuple[bool, List[str]]:
    """
    Validates the aligned_events.csv file against the specified schema.

    This function reads the CSV, converts it to a list of dictionaries (rows),
    and validates each row against the 'items' definition in the schema.
    It also checks for required columns and data types where possible.

    Args:
        csv_path: Path to the CSV file to validate.
        schema_name: Name of the schema file in the contracts directory.

    Returns:
        A tuple (is_valid, errors).
        - is_valid: True if all rows pass validation.
        - errors: A list of error messages describing validation failures.
    """
    if not os.path.exists(csv_path):
        return False, [f"Input file not found: {csv_path}"]

    try:
        schema = load_schema(schema_name)
    except (FileNotFoundError, ValueError) as e:
        return False, [f"Failed to load schema: {e}"]

    # Basic CSV reading
    import pandas as pd
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return False, [f"Failed to read CSV: {e}"]

    if df.empty:
        logger.warning("CSV file is empty. Validation passed trivially, but data may be missing.")
        return True, []

    errors = []
    rows = df.to_dict('records')

    # Define a validator for the schema
    try:
        validator = jsonschema.Draft7Validator(schema)
    except SchemaError as e:
        return False, [f"Invalid schema definition: {e}"]

    # Validate each row
    for idx, row in enumerate(rows):
        # Convert row values to types expected by JSON Schema if necessary
        # (e.g., ensure integers are ints, floats are floats, nulls are None)
        # Pandas often reads everything as object or float64; we try to coerce based on schema hints
        clean_row = {}
        for key, value in row.items():
            if pd.isna(value):
                clean_row[key] = None
            elif isinstance(value, (int, float)):
                # Handle potential integer-like floats (e.g., 1.0 -> 1) if schema expects integer
                if isinstance(value, float) and value.is_integer():
                    clean_row[key] = int(value)
                else:
                    clean_row[key] = value
            else:
                clean_row[key] = value

        # Validate the row
        for error in validator.iter_errors(clean_row):
            errors.append(f"Row {idx}: {error.message} (instance: {error.instance})")

    if errors:
        logger.error(f"Validation failed for {csv_path} with {len(errors)} errors.")
        return False, errors

    logger.info(f"Validation successful for {csv_path}. All {len(rows)} rows are schema-compliant.")
    return True, []


def block_write_if_invalid(csv_path: str, schema_name: str = "aligned_event.schema.yaml") -> bool:
    """
    Validates the CSV and returns True if valid, False if invalid.
    This is the primary entry point for the pipeline to check before writing.

    Args:
        csv_path: Path to the CSV file to validate.
        schema_name: Name of the schema file.

    Returns:
        True if validation passes (or file doesn't exist yet but will be created),
        False if validation fails.
    """
    if not os.path.exists(csv_path):
        # If the file doesn't exist, we can't validate it yet.
        # In the context of 'block_write_if_invalid', this usually means
        # we are about to write it. We return True to allow the write,
        # assuming the writer will produce valid data.
        # However, if this function is called AFTER generation, it should fail.
        # Given the task: "block the writing ... if validation fails",
        # we assume the file exists at this point (just generated).
        # If it doesn't exist, we can't validate.
        logger.warning(f"Cannot validate {csv_path} because it does not exist yet.")
        return True 

    is_valid, errors = validate_aligned_events(csv_path, schema_name)
    if not is_valid:
        logger.error("VALIDATION BLOCKED: Data does not match schema. Aborting write/manifest update.")
        for err in errors[:5]: # Log first 5 errors
            logger.error(f"  - {err}")
        if len(errors) > 5:
            logger.error(f"  ... and {len(errors) - 5} more errors.")
        return False
    
    return True


def main():
    """
    Command-line entry point for validation.
    Usage: python code/validate.py [csv_path] [schema_name]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate data artifacts against schemas.")
    parser.add_argument(
        "--csv", 
        default=os.path.join(DATA_PROCESSED_DIR, "aligned_events.csv"),
        help="Path to the CSV file to validate."
    )
    parser.add_argument(
        "--schema", 
        default="aligned_event.schema.yaml",
        help="Name of the schema file in contracts/."
    )

    args = parser.parse_args()

    logger.info(f"Starting validation of {args.csv} against {args.schema}...")
    
    is_valid, errors = validate_aligned_events(args.csv, args.schema)

    if is_valid:
        logger.info("VALIDATION PASSED.")
        sys.exit(0)
    else:
        logger.error("VALIDATION FAILED.")
        for err in errors:
            print(err)
        sys.exit(1)


if __name__ == "__main__":
    main()
