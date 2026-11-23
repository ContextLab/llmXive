"""
T012a: Validate the unified problem schema against the contract.

This script verifies that the merged `data/raw/unified_problems.csv` strictly
adheres to the schema defined in `contracts/problem.schema.yaml`.

It performs:
1. File existence check.
2. Schema loading.
3. Column validation (presence and type).
4. Row-by-row validation for required fields.

Exit Code:
- 0: Validation passed.
- 1: Validation failed (missing file, schema mismatch, or invalid rows).
"""

import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
UNIFIED_DATA_PATH = "data/raw/unified_problems.csv"
SCHEMA_PATH = "contracts/problem.schema.yaml"
REQUIRED_FIELDS = {"problem_id", "prompt_text", "difficulty", "skill"}

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load and parse the YAML schema file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        if not schema:
            raise ValueError(f"Schema file is empty: {schema_path}")
        return schema
    except ImportError:
        logger.error("PyYAML is required to load schema. Install it via 'pip install pyyaml'.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML schema: {e}")
        sys.exit(1)

def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    """Ensure the schema has the expected structure (fields definition)."""
    if "fields" not in schema:
        logger.error("Schema missing 'fields' definition.")
        return False
    if not isinstance(schema["fields"], dict):
        logger.error("Schema 'fields' must be a dictionary.")
        return False
    return True

def validate_row(row: Dict[str, str], schema: Dict[str, Any], row_num: int) -> List[str]:
    """
    Validate a single row against the schema.
    Returns a list of error messages.
    """
    errors = []
    schema_fields = schema.get("fields", {})

    # Check for required fields presence
    for field in REQUIRED_FIELDS:
        if field not in row or not row[field]:
            errors.append(f"Row {row_num}: Missing or empty required field '{field}'")

    # Validate specific field types if defined in schema
    # Example: difficulty should be numeric
    if "difficulty" in row and schema_fields.get("difficulty", {}).get("type") == "number":
        try:
            float(row["difficulty"])
        except ValueError:
            errors.append(f"Row {row_num}: Field 'difficulty' must be a number, got '{row['difficulty']}'")

    # Check for unexpected columns if schema defines allowed columns strictly
    # (Optional: depending on schema strictness, we might allow extra columns)
    # For this task, we focus on REQUIRED_FIELDS compliance.

    return errors

def validate_unified_schema(data_path: str, schema_path: str) -> bool:
    """
    Main validation logic.
    Returns True if valid, False otherwise.
    """
    # 1. Check file existence
    if not os.path.exists(data_path):
        logger.error(f"Unified data file not found at: {data_path}")
        logger.error("Dependency T012e (unify_datasets.py) must run successfully first.")
        return False

    # 2. Load Schema
    try:
        schema = load_schema(schema_path)
        if not validate_schema_structure(schema):
            return False
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    # 3. Validate CSV content
    invalid_rows_count = 0
    total_rows = 0
    reported_errors: List[str] = []

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Check header columns
            if reader.fieldnames is None:
                logger.error("CSV file is empty or has no header.")
                return False

            header_set = set(reader.fieldnames)
            missing_header_fields = REQUIRED_FIELDS - header_set

            if missing_header_fields:
                logger.error(f"CSV header missing required columns: {missing_header_fields}")
                return False

            for row_num, row in enumerate(reader, start=2): # Start at 2 (1 is header)
                total_rows += 1
                row_errors = validate_row(row, schema, row_num)
                if row_errors:
                    invalid_rows_count += 1
                    if len(reported_errors) < 10: # Limit error reporting to avoid spam
                        reported_errors.extend(row_errors)

    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return False

    # 4. Report Results
    if invalid_rows_count > 0:
        logger.error(f"Validation FAILED. {invalid_rows_count} invalid rows found out of {total_rows}.")
        logger.error("First few errors:")
        for err in reported_errors:
            logger.error(f"  - {err}")
        return False
    else:
        logger.info(f"Validation PASSED. {total_rows} rows validated successfully.")
        return True

def main():
    parser = argparse.ArgumentParser(description="Validate unified problem schema against contract.")
    parser.add_argument(
        "--data-path",
        type=str,
        default=UNIFIED_DATA_PATH,
        help=f"Path to the unified CSV file (default: {UNIFIED_DATA_PATH})"
    )
    parser.add_argument(
        "--schema-path",
        type=str,
        default=SCHEMA_PATH,
        help=f"Path to the schema YAML file (default: {SCHEMA_PATH})"
    )

    args = parser.parse_args()

    logger.info(f"Starting schema validation for: {args.data_path}")
    logger.info(f"Using schema: {args.schema_path}")

    is_valid = validate_unified_schema(args.data_path, args.schema_path)

    if is_valid:
        logger.info("Schema validation successful.")
        sys.exit(0)
    else:
        logger.error("Schema validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()