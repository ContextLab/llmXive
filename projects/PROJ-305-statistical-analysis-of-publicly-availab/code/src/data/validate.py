"""
Data validation module for VAERS datasets.
Validates raw data against the defined schema and exits with E_SCHEMA_MISSING if validation fails.
"""
import os
import sys
from pathlib import Path
from typing import List, Set, Dict, Any

import yaml
import pandas as pd

# Project root relative to this file (assuming code/src/data/validate.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Exit codes
E_SUCCESS = 0
E_SCHEMA_MISSING = 1
E_FILE_NOT_FOUND = 2
E_INVALID_SCHEMA = 3
E_VALIDATION_ERROR = 4


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and parse the YAML schema file."""
    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}", file=sys.stderr)
        sys.exit(E_FILE_NOT_FOUND)
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        return schema
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in schema file: {e}", file=sys.stderr)
        sys.exit(E_INVALID_SCHEMA)


def validate_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
    """
    Check if all required columns exist in the DataFrame.
    Returns a list of missing columns.
    """
    existing_columns = set(df.columns)
    required_set = set(required_columns)
    missing = required_set - existing_columns
    return list(missing)


def validate_data(file_path: str, schema_path: str = None) -> bool:
    """
    Validate a CSV file against the dataset schema.
    
    Args:
        file_path: Path to the CSV file to validate
        schema_path: Path to the schema YAML file (defaults to contracts/dataset.schema.yaml)
        
    Returns:
        True if validation passes, False otherwise
        
    Exits:
        E_SUCCESS if validation passes
        E_SCHEMA_MISSING if required columns are missing
        E_FILE_NOT_FOUND if input file or schema file is missing
        E_VALIDATION_ERROR if other validation fails
    """
    if schema_path is None:
        schema_path = str(CONTRACTS_DIR / "dataset.schema.yaml")
    
    schema_path_obj = Path(schema_path)
    schema = load_schema(schema_path_obj)
    
    # Extract required columns from schema
    # Expected schema format: { "required_columns": ["col1", "col2", ...] }
    if "required_columns" not in schema:
        print("Error: Schema missing 'required_columns' key", file=sys.stderr)
        sys.exit(E_INVALID_SCHEMA)
    
    required_columns = schema["required_columns"]
    
    # Load the CSV file
    input_path = Path(file_path)
    if not input_path.exists():
        print(f"Error: Input file not found at {file_path}", file=sys.stderr)
        sys.exit(E_FILE_NOT_FOUND)
    
    try:
        df = pd.read_csv(input_path, nrows=100)  # Read first 100 rows for column check
    except Exception as e:
        print(f"Error: Failed to read CSV file: {e}", file=sys.stderr)
        sys.exit(E_VALIDATION_ERROR)
    
    # Validate columns
    missing_columns = validate_columns(df, required_columns)
    
    if missing_columns:
        missing_str = ", ".join(missing_columns)
        print(f"Error: Missing required columns: {missing_str}", file=sys.stderr)
        sys.exit(E_SCHEMA_MISSING)
    
    # Optional: Validate data types and non-empty constraints if specified in schema
    if "column_constraints" in schema:
        constraints = schema["column_constraints"]
        for col, constraints_dict in constraints.items():
            if col in df.columns:
                if constraints_dict.get("non_empty", False):
                    empty_count = df[col].isna().sum() + (df[col] == "").sum()
                    if empty_count > 0:
                        print(f"Warning: Column '{col}' has {empty_count} empty values", file=sys.stderr)
                        # Note: We warn but don't exit for empty values in initial validation
                        # unless explicitly required to fail
    
    print(f"Validation passed: {file_path}")
    return True


def main():
    """Main entry point for command-line validation."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.data.validate <csv_file> [schema_file]", file=sys.stderr)
        sys.exit(E_VALIDATION_ERROR)
    
    csv_file = sys.argv[1]
    schema_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        validate_data(csv_file, schema_file)
        sys.exit(E_SUCCESS)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Unexpected error during validation: {e}", file=sys.stderr)
        sys.exit(E_VALIDATION_ERROR)


if __name__ == "__main__":
    main()
