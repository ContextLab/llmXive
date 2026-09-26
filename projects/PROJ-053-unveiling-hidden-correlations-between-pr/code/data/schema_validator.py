import os
import sys
import csv
import yaml
import logging
import pandas as pd
from pathlib import Path

from config import get_contracts_dir, get_raw_data_dir, get_logs_dir, ensure_directories
from utils.logger import setup_logging


def setup_logger(name: str) -> logging.Logger:
    """Setup a logger specific to schema validation."""
    log_dir = get_logs_dir()
    ensure_directories()
    log_file = os.path.join(log_dir, f"{name}.log")
    return setup_logging(name, log_file)


def load_schema(schema_path: str) -> dict:
    """Load the YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_csv_schema(csv_path: str, schema: dict) -> bool:
    """
    Validate that the CSV file matches the schema.
    Checks for required columns and numeric data types.
    """
    logger = logging.getLogger("schema_validator")
    logger.info(f"Validating CSV: {csv_path} against schema")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Load schema
    required_columns = schema.get('required', [])
    properties = schema.get('properties', {})

    # Read CSV header
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)

    missing_required = [col for col in required_columns if col not in header]
    if missing_required:
        raise ValueError(f"Missing required columns: {missing_required}")

    # Check for numeric types in data
    df = pd.read_csv(csv_path)

    for col, prop in properties.items():
        if col in df.columns:
            if prop.get('type') == 'number':
                # Attempt to parse as float, handle scientific notation
                try:
                    pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    raise ValueError(f"Column '{col}' contains non-numeric data")

    logger.info("Schema validation passed")
    return True


def validate_and_report(csv_path: str, schema_path: str) -> None:
    """Main validation entry point."""
    logger = setup_logger("schema_validation")
    ensure_directories()

    try:
        schema = load_schema(schema_path)
        if validate_csv_schema(csv_path, schema):
            logger.info("Validation successful: CSV conforms to schema.")
        else:
            logger.error("Validation failed: Schema mismatch detected.")
            sys.exit(1)
    except FileNotFoundError as fnf:
        logger.error(f"File not found: {fnf}")
        raise
    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        raise


def main():
    """CLI entry point."""
    contracts_dir = get_contracts_dir()
    raw_dir = get_raw_data_dir()
    schema_path = os.path.join(contracts_dir, 'dataset.schema.yaml')
    csv_path = os.path.join(raw_dir, 'am_raw_data.csv')

    if not os.path.exists(csv_path):
        # If file doesn't exist, we might be in a setup phase, but for T005/T006
        # we just ensure the validator logic is sound.
        # However, the task implies we must be able to run it.
        # We will attempt to run it; if the file is missing, it fails loudly.
        pass

    validate_and_report(csv_path, schema_path)


if __name__ == '__main__':
    main()