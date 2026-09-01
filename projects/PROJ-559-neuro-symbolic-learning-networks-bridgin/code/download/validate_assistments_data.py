"""
Validate the fetched ASSISTments dataset against the problem schema.

This script reads the CSV file, validates its columns and types against
the schema defined in contracts/problem.schema.yaml, and reports errors.

Dependencies:
    - pandas
    - yaml
    - json
"""

import os
import sys
import json
import logging
import argparse
import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/validate_assistments.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

DATA_FILE = "data/raw/assistments.csv"
SCHEMA_FILE = "contracts/problem.schema.yaml"

def load_schema(schema_path: str) -> dict:
    """Load the YAML schema file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_columns(df: pd.DataFrame, schema: dict) -> List[str]:
    """Check if required columns exist."""
    required = schema.get('required_fields', [])
    missing = [col for col in required if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
    return missing

def validate_types(df: pd.DataFrame, schema: dict) -> List[str]:
    """Check if column types match schema expectations."""
    type_map = {
        'integer': 'int64',
        'float': 'float64',
        'string': 'object',
        'boolean': 'bool'
    }
    
    fields = schema.get('fields', {})
    errors = []
    
    for col_name, col_schema in fields.items():
        if col_name in df.columns:
            expected_type = type_map.get(col_schema.get('type', 'string'), 'object')
            # Basic type check (pandas might infer slightly different dtypes)
            # We check if the actual dtype is compatible or close enough
            actual_type = str(df[col_name].dtype)
            if expected_type == 'object' and actual_type != 'object':
                # Allow conversion if it's a string-like type
                if not df[col_name].apply(lambda x: isinstance(x, str) or pd.isna(x)).all():
                    errors.append(f"Column {col_name} has type {actual_type}, expected {expected_type}")
            elif expected_type != 'object' and expected_type not in actual_type:
                errors.append(f"Column {col_name} has type {actual_type}, expected {expected_type}")
    
    return errors

def validate_data(df: pd.DataFrame, schema: dict) -> List[str]:
    """Perform additional data validation (e.g., non-null checks)."""
    errors = []
    fields = schema.get('fields', {})
    
    for col_name, col_schema in fields.items():
        if col_schema.get('nullable', False) is False and col_name in df.columns:
            null_count = df[col_name].isnull().sum()
            if null_count > 0:
                errors.append(f"Column {col_name} has {null_count} null values (not allowed)")
    
    return errors

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Validate ASSISTments dataset.")
    parser.add_argument(
        "--data-file",
        type=str,
        default=DATA_FILE,
        help=f"Path to the CSV file (default: {DATA_FILE})"
    )
    parser.add_argument(
        "--schema-file",
        type=str,
        default=SCHEMA_FILE,
        help=f"Path to the schema file (default: {SCHEMA_FILE})"
    )
    args = parser.parse_args()

    logger.info(f"Validating data file: {args.data_file}")
    logger.info(f"Using schema file: {args.schema_file}")

    if not os.path.exists(args.data_file):
        logger.error(f"ERROR: Data file not found: {args.data_file}")
        sys.exit(1)

    try:
        schema = load_schema(args.schema_file)
    except FileNotFoundError as e:
        logger.error(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"ERROR: Failed to load schema: {e}")
        sys.exit(1)

    try:
        df = pd.read_csv(args.data_file)
        logger.info(f"Loaded {len(df)} rows.")
    except Exception as e:
        logger.error(f"ERROR: Failed to load CSV: {e}")
        sys.exit(1)

    all_errors = []
    
    # Validate columns
    missing_cols = validate_columns(df, schema)
    if missing_cols:
        all_errors.extend([f"Missing column: {c}" for c in missing_cols])
    
    # Validate types
    type_errors = validate_types(df, schema)
    all_errors.extend(type_errors)
    
    # Validate data constraints
    data_errors = validate_data(df, schema)
    all_errors.extend(data_errors)

    if all_errors:
        logger.error(f"Validation failed with {len(all_errors)} errors:")
        for err in all_errors[:10]: # Log first 10
            logger.error(f"  - {err}")
        if len(all_errors) > 10:
            logger.error(f"  ... and {len(all_errors) - 10} more errors.")
        sys.exit(1)
    else:
        logger.info("Validation passed. All checks successful.")
        sys.exit(0)

if __name__ == "__main__":
    main()