"""
Schema validation module for AM alloy datasets.
Validates CSV files against a YAML schema definition.
"""
import os
import sys
import csv
import yaml
import logging
import pandas as pd
from pathlib import Path

from config import get_contracts_dir, ensure_directories

def setup_logger():
    logger = logging.getLogger("schema_validator")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def load_schema(schema_path: str = None) -> dict:
    """Load the YAML schema definition."""
    if schema_path is None:
        schema_path = os.path.join(get_contracts_dir(), "dataset.schema.yaml")
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_schema(df: pd.DataFrame, schema: dict) -> bool:
    """
    Validate a DataFrame against the schema.
    Checks for required columns and numeric types.
    """
    required_cols = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check types for numeric columns
    for col_name, col_def in properties.items():
        if col_name in df.columns:
            if col_def.get('type') == 'number':
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    # Attempt to coerce
                    try:
                        df[col_name] = pd.to_numeric(df[col_name], errors='raise')
                    except (ValueError, TypeError):
                        raise ValueError(f"Column '{col_name}' is not numeric and cannot be coerced.")
    
    return True

def validate_and_report(csv_path: str, schema_path: str = None, logger: logging.Logger = None) -> bool:
    """
    Main validation function.
    Returns True if valid, raises ValueError otherwise.
    """
    if logger is None:
        logger = setup_logger()
    
    logger.info(f"Validating CSV: {csv_path} against schema: {schema_path}")
    
    try:
        schema = load_schema(schema_path)
        df = pd.read_csv(csv_path)
        
        validate_csv_schema(df, schema)
        
        logger.info("Validation successful.")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate CSV against schema")
    parser.add_argument("--input", type=str, required=True, help="Path to CSV")
    parser.add_argument("--schema", type=str, default=None, help="Path to schema YAML")
    args = parser.parse_args()
    
    logger = setup_logger()
    try:
        validate_and_report(args.input, args.schema, logger)
        print("Validation Passed")
    except Exception as e:
        print(f"Validation Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
