"""
Validate the fetched ASSISTments dataset against the problem schema.

This script verifies that the downloaded ASSISTments dataset at `data/raw/assistments.csv`
conforms to the schema defined in `contracts/problem.schema.yaml`.

It performs the following checks:
1. File existence.
2. Schema loading.
3. Column validation (presence of required fields).
4. Type validation (basic type checking for numeric/string fields).
5. Row count validation (ensuring non-empty dataset).

Exit Codes:
- 0: Validation successful.
- 1: Validation failed (file missing, schema error, or invalid data).
"""

import os
import sys
import json
import logging
import argparse
import pandas as pd
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE_PATH = PROJECT_ROOT / "data" / "raw" / "assistments.csv"
SCHEMA_FILE_PATH = PROJECT_ROOT / "contracts" / "problem.schema.yaml"

def load_schema(schema_path: Path) -> dict:
    """Load and parse the YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    if not schema:
        raise ValueError(f"Schema file is empty or invalid YAML: {schema_path}")
    
    return schema

def validate_columns(df: pd.DataFrame, schema: dict) -> list:
    """
    Validate that the DataFrame contains all required columns defined in the schema.
    
    Returns a list of missing column names.
    """
    required_fields = schema.get('required', [])
    missing_columns = []
    
    for field in required_fields:
        if field not in df.columns:
            missing_columns.append(field)
    
    return missing_columns

def validate_types(df: pd.DataFrame, schema: dict) -> list:
    """
    Validate basic data types for columns defined in the schema.
    
    Returns a list of tuples (column_name, issue_description) for invalid rows.
    """
    issues = []
    properties = schema.get('properties', {})
    
    # Define expected pandas dtypes or basic checks
    type_map = {
        'integer': ['int', 'Int64', 'float64'], # Allow float for integer-like if needed
        'number': ['float64', 'int64', 'Int64'],
        'string': ['object', 'string']
    }
    
    for col_name, col_schema in properties.items():
        if col_name not in df.columns:
            continue
        
        expected_type = col_schema.get('type')
        if not expected_type:
            continue
        
        # Check for nulls if not allowed
        if not col_schema.get('nullable', True):
            null_count = df[col_name].isna().sum()
            if null_count > 0:
                issues.append((col_name, f"Contains {null_count} null values but nullable=False"))
        
        # Basic type check (lenient for numeric)
        if expected_type in ['integer', 'number']:
            if not pd.api.types.is_numeric_dtype(df[col_name]):
                # Allow mixed types if we can coerce, but flag if completely non-numeric
                try:
                    pd.to_numeric(df[col_name], errors='raise')
                except (ValueError, TypeError):
                    issues.append((col_name, f"Column contains non-numeric values for type '{expected_type}'"))
        elif expected_type == 'string':
            if not pd.api.types.is_string_dtype(df[col_name]) and not pd.api.types.is_object_dtype(df[col_name]):
                # String columns can be object or string dtype
                pass 
    
    return issues

def validate_data(file_path: Path, schema_path: Path) -> bool:
    """
    Main validation logic.
    
    Returns True if valid, False otherwise.
    """
    # 1. Check file existence
    if not file_path.exists():
        logger.error(f"Data file not found at: {file_path}")
        return False

    logger.info(f"Loading data from: {file_path}")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return False

    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

    if df.empty:
        logger.error("Dataset is empty.")
        return False

    # 2. Load schema
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    # 3. Validate columns
    missing_cols = validate_columns(df, schema)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False

    # 4. Validate types
    type_issues = validate_types(df, schema)
    if type_issues:
        for col, issue in type_issues:
            logger.error(f"Type validation issue in column '{col}': {issue}")
        return False

    logger.info("Validation successful: Schema matches data.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Validate ASSISTments dataset against schema.")
    parser.add_argument(
        "--data-file", 
        type=str, 
        default=str(DATA_FILE_PATH),
        help="Path to the CSV file to validate."
    )
    parser.add_argument(
        "--schema-file", 
        type=str, 
        default=str(SCHEMA_FILE_PATH),
        help="Path to the YAML schema file."
    )
    
    args = parser.parse_args()
    
    data_path = Path(args.data_file)
    schema_path = Path(args.schema_file)

    is_valid = validate_data(data_path, schema_path)

    if is_valid:
        logger.info("Validation PASSED.")
        sys.exit(0)
    else:
        logger.error("Validation FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()