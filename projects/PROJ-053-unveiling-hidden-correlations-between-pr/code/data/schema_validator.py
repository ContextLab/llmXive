import os
import sys
import csv
import yaml
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_logger():
    logging.basicConfig(level=logging.INFO)

def load_schema(schema_path: str) -> dict:
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_schema(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validate that the dataframe matches the schema defined in the YAML file.
    """
    schema = load_schema(schema_path)
    required_cols = schema.get('required_columns', [])
    optional_cols = schema.get('optional_columns', [])
    
    all_allowed = set(required_cols + optional_cols)
    actual_cols = set(df.columns)
    
    missing_required = set(required_cols) - actual_cols
    if missing_required:
        logger.error(f"Missing required columns: {missing_required}")
        return False
    
    # Check for unexpected columns (optional)
    extra_cols = actual_cols - all_allowed
    if extra_cols:
        logger.warning(f"Found extra columns not in schema: {extra_cols}")
    
    logger.info("Schema validation passed.")
    return True

def validate_and_report(df: pd.DataFrame, schema_path: str) -> bool:
    return validate_csv_schema(df, schema_path)

def main():
    setup_logger()
    # Example usage
    logger.info("Schema validator module loaded.")

if __name__ == "__main__":
    main()
