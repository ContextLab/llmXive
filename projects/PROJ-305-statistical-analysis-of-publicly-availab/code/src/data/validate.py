"""
Data validation module for VAERS datasets.
Validates raw CSV files against the schema defined in contracts/dataset.schema.yaml.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Set, Dict, Any

import pandas as pd
import yaml

# Define custom exit code for schema mismatch
E_SCHEMA_MISSING = 101

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    logger.info(f"Loaded schema from {schema_path}")
    return schema


def validate_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Check if the DataFrame contains all required columns.

    Args:
        df: The DataFrame to validate.
        required_columns: List of required column names.

    Returns:
        True if all required columns are present, False otherwise.
    """
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False

    logger.info("All required columns are present.")
    return True


def validate_data(
    data_path: str,
    schema_path: str,
    check_empty: bool = True
) -> bool:
    """
    Validate a CSV data file against a schema.

    Args:
        data_path: Path to the CSV data file.
        schema_path: Path to the schema YAML file.
        check_empty: If True, check that the file is not empty.

    Returns:
        True if validation passes, False otherwise.

    Raises:
        SystemExit: If validation fails with E_SCHEMA_MISSING.
    """
    schema = load_schema(schema_path)
    required_columns = schema.get('required_columns', [])

    logger.info(f"Validating data file: {data_path}")

    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        sys.exit(E_SCHEMA_MISSING)

    try:
        # Read just the header to check columns efficiently
        df_header = pd.read_csv(data_path, nrows=0)
    except Exception as e:
        logger.error(f"Failed to read CSV header: {e}")
        sys.exit(E_SCHEMA_MISSING)

    if not validate_columns(df_header, required_columns):
        logger.error("Schema validation failed: missing columns.")
        sys.exit(E_SCHEMA_MISSING)

    if check_empty:
        try:
            # Check if file has more than just headers
            df_sample = pd.read_csv(data_path, nrows=1)
            if df_sample.empty:
                logger.warning("Data file contains no rows (header only).")
                # Depending on strictness, this might be a warning or error.
                # For now, we allow it but log it.
        except Exception as e:
            logger.error(f"Failed to verify data content: {e}")
            sys.exit(E_SCHEMA_MISSING)

    logger.info("Data validation successful.")
    return True


def main():
    """
    Command-line entry point for data validation.
    Expects two arguments: <data_path> <schema_path>
    """
    if len(sys.argv) != 3:
        logger.error("Usage: python validate.py <data_path> <schema_path>")
        sys.exit(1)

    data_path = sys.argv[1]
    schema_path = sys.argv[2]

    try:
        if validate_data(data_path, schema_path):
            logger.info("Validation PASSED")
            sys.exit(0)
        else:
            # validate_data exits on failure, but if it returns False for some other reason
            logger.error("Validation FAILED")
            sys.exit(E_SCHEMA_MISSING)
    except SystemExit as e:
        # Re-raise the exit code if it's our custom one
        if e.code == E_SCHEMA_MISSING:
            raise
        # Otherwise, it was a success exit
        sys.exit(e.code)
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
