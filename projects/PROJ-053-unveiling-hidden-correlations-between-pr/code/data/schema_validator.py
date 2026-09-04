import os
import sys
import csv
import yaml
import logging
import pandas as pd
from typing import Dict, List, Any, Optional

from config import get_contracts_dir, ensure_directories, get_logger

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Setup a dedicated logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            logger.addHandler(fh)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
    return logger

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the YAML schema file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_schema(df: pd.DataFrame, schema: Dict[str, Any], logger: logging.Logger) -> bool:
    """Validate DataFrame against the schema.
    
    Checks:
    1. All required columns exist.
    2. Columns defined as 'number' in the schema are numeric.
    
    Raises ValueError if validation fails.
    """
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    # Check required columns
    missing_cols = [col for col in required if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing required columns: {missing_cols}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check types for all defined properties
    for col, spec in properties.items():
        if col in df.columns:
            if spec.get('type') == 'number':
                if not pd.api.types.is_numeric_dtype(df[col]):
                    logger.warning(f"Column '{col}' is not numeric. Attempting conversion.")
                    try:
                        df[col] = pd.to_numeric(df[col], errors='raise')
                    except (ValueError, TypeError) as e:
                        error_msg = f"Column '{col}' cannot be converted to numeric: {e}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)
    
    return True

def validate_and_report(csv_path: str, schema_path: str, log_path: Optional[str] = None) -> bool:
    """Validate a CSV file against a schema and log results.
    
    Returns True if validation passes, False otherwise.
    """
    logger = setup_logger("schema_validator", log_path)
    
    try:
        schema = load_schema(schema_path)
        df = pd.read_csv(csv_path)
        validate_csv_schema(df, schema, logger)
        logger.info("Schema validation successful.")
        return True
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False

def main():
    """Entry point for schema validation."""
    import argparse
    parser = argparse.ArgumentParser(description="Validate CSV against schema")
    parser.add_argument("--csv", type=str, required=True, help="Path to CSV file")
    parser.add_argument("--schema", type=str, default=None, help="Path to schema YAML")
    parser.add_argument("--log", type=str, default=None, help="Path to log file")
    args = parser.parse_args()

    if args.schema is None:
        args.schema = os.path.join(get_contracts_dir(), 'dataset.schema.yaml')

    success = validate_and_report(args.csv, args.schema, args.log)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()