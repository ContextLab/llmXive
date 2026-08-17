"""
check_pilot_data.py

Checks for the existence and validity of the human pilot dataset at `data/pilot/raw_pilot_data.csv`.

Deliverable:
  - Exit code 0 with JSON status flag `{"has_human_data": true}` if valid (≥50 records per contracts/pilot_data.schema.yaml).
  - Exit code 1 with error message "ERROR: Human pilot data missing (<50 records). Calibration cannot proceed." if missing/invalid.

Requirement: Must NOT exit with code 0 if data is missing; the pipeline MUST halt to enforce FR-010.
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
DEFAULT_SCHEMA_PATH = "contracts/pilot_data.schema.yaml"
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

def validate_schema(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validates that the DataFrame contains the required columns defined in the schema.
    
    The schema implies standard columns for pilot data based on project context:
    student_id, problem_id, is_correct, response_time, comprehension.
    
    This function enforces the presence of critical columns required for calibration (T031).
    """
    required_columns = {'student_id', 'problem_id', 'is_correct', 'response_time'}
    
    # Check if DataFrame is empty (already handled by record count, but double check)
    if df.empty:
        logger.error("Schema validation failed: DataFrame is empty.")
        return False
        
    missing_cols = required_columns - set(df.columns)
    if missing_cols:
        logger.error(f"Schema validation failed: Missing required columns: {missing_cols}")
        return False
    
    # Basic type validation for numeric columns
    if not pd.api.types.is_numeric_dtype(df['is_correct']):
        logger.error("Schema validation failed: 'is_correct' must be numeric (0/1).")
        return False
    
    if not pd.api.types.is_numeric_dtype(df['response_time']):
        logger.error("Schema validation failed: 'response_time' must be numeric.")
        return False

    return True

def check_pilot_data(data_path: str, schema_path: str) -> bool:
    """
    Checks if the pilot data file exists and contains at least MIN_RECORDS_THRESHOLD records.
    Validates against the schema requirements.

    Args:
        data_path: Path to the CSV file.
        schema_path: Path to the schema file (for column validation).

    Returns:
        True if valid (exists, >= 50 records, valid schema), False otherwise.
    """
    if not os.path.exists(data_path):
        logger.error(f"Pilot data file not found at: {data_path}")
        return False

    try:
        # Load schema if available
        schema = load_schema(SCHEMA_PATH)

        # Attempt to load the CSV
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

        # Validate against schema requirements
        if not validate_schema(df, schema_path):
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
    parser.add_argument(
        "--schema-path",
        type=str,
        default=DEFAULT_SCHEMA_PATH,
        help=f"Path to the schema YAML file (default: {DEFAULT_SCHEMA_PATH})"
    )
    args = parser.parse_args()

    is_valid = check_pilot_data(args.data_path, args.schema_path)

    # Construct the result JSON
    result = {
        "has_human_data": is_valid
    }

    # Output JSON to stdout for downstream parsing
    print(json.dumps(result))

    # Exit logic per FR-010: 
    # If valid -> exit 0 (success)
    # If invalid/missing -> exit 1 (halt pipeline) with specific error message
    if is_valid:
        sys.exit(0)
    else:
        # Ensure the exact error message is logged to stderr as per spec
        error_msg = "ERROR: Human pilot data missing (<50 records). Calibration cannot proceed."
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()