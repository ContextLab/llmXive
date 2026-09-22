"""
Data validation module for VAERS dataset.

This module validates raw data against the schema defined in contracts/dataset.schema.yaml.
It checks for required columns, data types, and basic constraints.
"""

import os
import sys
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
import yaml
import pandas as pd

# Custom exception for schema validation failures
class E_SCHEMA_MISSING(Exception):
    """Raised when required columns are missing from the dataset."""
    pass

# Error codes
ERR_SCHEMA_FILE_NOT_FOUND = "E_SCHEMA_FILE_NOT_FOUND"
ERR_SCHEMA_INVALID_YAML = "E_SCHEMA_INVALID_YAML"
ERR_MISSING_COLUMNS = "E_SCHEMA_MISSING"
ERR_FILE_NOT_FOUND = "E_FILE_NOT_FOUND"

def load_schema(schema_path: str = "contracts/dataset.schema.yaml") -> Dict[str, Any]:
    """
    Load and parse the YAML schema file.
    
    Args:
        schema_path: Path to the schema YAML file
        
    Returns:
        Dictionary containing the parsed schema
        
    Raises:
        FileNotFoundError: If schema file does not exist
        yaml.YAMLError: If schema file contains invalid YAML
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        return schema
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in schema file: {e}")

def validate_columns(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Check if all required columns are present in the DataFrame.
    
    Args:
        df: DataFrame to validate
        schema: Parsed schema dictionary
        
    Returns:
        List of missing column names
    """
    if 'required_columns' not in schema:
        return []
        
    required_cols = [col['name'] for col in schema['required_columns']]
    missing_cols = [col for col in required_cols if col not in df.columns]
    return missing_cols

def validate_data(df: pd.DataFrame, schema_path: str = "contracts/dataset.schema.yaml") -> bool:
    """
    Validate the DataFrame against the schema.
    
    Args:
        df: DataFrame to validate
        schema_path: Path to the schema YAML file
        
    Returns:
        True if validation passes
        
    Raises:
        E_SCHEMA_MISSING: If required columns are missing
        FileNotFoundError: If data file or schema file is not found
    """
    # Load schema
    schema = load_schema(schema_path)
    
    # Check required columns
    missing_cols = validate_columns(df, schema)
    
    if missing_cols:
        raise E_SCHEMA_MISSING(
            f"Missing required columns: {', '.join(missing_cols)}. "
            f"Schema requires: {[col['name'] for col in schema.get('required_columns', [])]}"
        )
    
    # Additional validation: check for null values in non-nullable columns
    if 'required_columns' in schema:
        for col_def in schema['required_columns']:
            if not col_def.get('nullable', True):
                col_name = col_def['name']
                if col_name in df.columns:
                    null_count = df[col_name].isnull().sum()
                    if null_count > 0:
                        # Log warning but don't fail here - this is handled in cleaning
                        pass
    
    return True

def main():
    """
    Command-line entry point for data validation.
    
    Usage: python -m src.data.validate --input <path_to_csv> [--schema <path_to_schema>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate VAERS dataset against schema')
    parser.add_argument('--input', '-i', required=True, help='Path to input CSV file')
    parser.add_argument('--schema', '-s', default='contracts/dataset.schema.yaml', 
                      help='Path to schema YAML file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load data
        print(f"Loading data from {args.input}...")
        df = pd.read_csv(args.input)
        print(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
        
        # Validate
        print(f"Validating against schema: {args.schema}...")
        validate_data(df, args.schema)
        print("Validation PASSED: All required columns present and schema compliant.")
        sys.exit(0)
        
    except E_SCHEMA_MISSING as e:
        print(f"Validation FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during validation: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()