"""
check_pilot_data.py

Checks for the existence and validity of the human pilot dataset at `data/pilot/raw_pilot_data.csv`.

This script enforces FR-010: Calibration cannot proceed without valid human pilot data.

Deliverable:
  - If the file exists and contains >= 50 valid records:
    * Exit code 0
    * Prints JSON to stdout: {"has_human_data": true}
  - If the file is missing, invalid, or has < 50 records:
    * Exit code 1
    * Prints error message to stderr: "ERROR: Human pilot data missing (<50 records). Calibration cannot proceed."
"""
import os
import sys
import json
import logging
import argparse
import yaml

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

DEFAULT_DATA_PATH = "data/pilot/raw_pilot_data.csv"
MIN_RECORDS_THRESHOLD = 50
SCHEMA_PATH = "contracts/pilot_data.schema.yaml"

def load_schema(schema_path: str) -> dict:
    """Load the YAML schema file to validate structure."""
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}. Skipping schema validation.")
        return None
    
    try:
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load schema {schema_path}: {e}. Skipping schema validation.")
        return None

def validate_schema(df, schema: dict) -> bool:
    """
    Perform basic validation against the schema.
    Checks for required columns if 'required' fields are defined in the schema.
    """
    if schema is None:
        return True

    required_fields = schema.get('required', [])
    if not required_fields:
        # If schema has no 'required' list, check for 'properties' keys
        properties = schema.get('properties', {})
        required_fields = [k for k, v in properties.items() if v.get('required', False)]

    if not required_fields:
        return True

    missing_cols = [col for col in required_fields if col not in df.columns]
    if missing_cols:
        logger.error(f"Schema validation failed. Missing required columns: {missing_cols}")
        return False
    
    return True

def check_pilot_data(data_path: str) -> bool:
    """
    Checks if the pilot data file exists and contains at least MIN_RECORDS_THRESHOLD records.
    
    This function validates against the schema defined in `contracts/pilot_data.schema.yaml`
    by ensuring the file is readable, has sufficient rows, and matches required columns.
    
    Args:
        data_path: Path to the CSV file.
    
    Returns:
        True if valid (exists and >= 50 records), False otherwise.
    """
    if not os.path.exists(data_path):
        logger.warning(f"Pilot data file not found at: {data_path}")
        return False

    try:
        # Load schema if available
        schema = load_schema(SCHEMA_PATH)

        # Attempt to load the CSV
        import pandas as pd
        df = pd.read_csv(data_path)
        
        record_count = len(df)
        logger.info(f"Loaded pilot data: {record_count} records found.")

        if record_count < MIN_RECORDS_THRESHOLD:
            logger.warning(
                f"Pilot data has {record_count} records, which is less than the "
                f"minimum required threshold of {MIN_RECORDS_THRESHOLD}."
            )
            return False

        # Basic validation: check if it's not just a header with no data
        if df.empty:
            logger.warning("Pilot data file is empty or contains only headers.")
            return False

        # Validate against schema if loaded
        if not validate_schema(df, schema):
            logger.error("Pilot data failed schema validation.")
            return False

        return True

    except pd.errors.EmptyDataError:
        logger.error(f"Pilot data file at {data_path} is empty.")
        return False
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse pilot data file at {data_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while validating pilot data: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Check for existence and validity of the human pilot dataset."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=DEFAULT_DATA_PATH,
        help=f"Path to the pilot data CSV file (default: {DEFAULT_DATA_PATH})"
    )
    args = parser.parse_args()

    is_valid = check_pilot_data(args.data_path)

    if is_valid:
        # Success: Exit 0, print JSON true
        result = {"has_human_data": True}
        print(json.dumps(result))
        sys.exit(0)
    else:
        # Failure: Exit 1, print error message
        error_msg = "ERROR: Human pilot data missing (<50 records). Calibration cannot proceed."
        logger.error(error_msg)
        print(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()