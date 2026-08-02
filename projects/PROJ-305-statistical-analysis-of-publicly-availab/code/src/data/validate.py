"""
Data validation module for VAERS datasets.
Validates raw data against the dataset schema defined in contracts/dataset.schema.yaml.
"""
import os
import sys
from pathlib import Path
from typing import List, Set, Dict, Any

import yaml
import pandas as pd

# Define custom error code constant
E_SCHEMA_MISSING = "E_SCHEMA_MISSING"

# Path configuration relative to project root
# Assuming the project root is the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"


def load_schema(schema_path: Path = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.

    Args:
        schema_path: Path to the schema file. Defaults to CONTRACTS_DIR/dataset.schema.yaml.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file contains invalid YAML.
    """
    if schema_path is None:
        schema_path = SCHEMA_PATH

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    if not isinstance(schema, dict):
        raise ValueError("Schema file must contain a valid YAML dictionary.")

    return schema


def validate_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
    """
    Check if the DataFrame contains all required columns.

    Args:
        df: The pandas DataFrame to validate.
        required_columns: List of column names required by the schema.

    Returns:
        List of missing column names. Empty if all required columns are present.
    """
    df_columns = set(df.columns)
    required_set = set(required_columns)
    missing = list(required_set - df_columns)
    return missing


def validate_data(df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a DataFrame against a loaded schema.

    Args:
        df: The pandas DataFrame to validate.
        schema: The loaded schema dictionary.

    Returns:
        A dictionary with validation results:
            - 'valid': bool, True if validation passes.
            - 'missing_columns': List[str], columns missing from the data.
            - 'error_code': str or None, E_SCHEMA_MISSING if columns are missing.
    """
    required_columns = schema.get("required_columns", [])
    
    if not required_columns:
        # If schema doesn't define required columns, consider it valid but warn?
        # For this task, we assume schema must define columns.
        return {
            "valid": True,
            "missing_columns": [],
            "error_code": None
        }

    missing = validate_columns(df, required_columns)

    if missing:
        return {
            "valid": False,
            "missing_columns": missing,
            "error_code": E_SCHEMA_MISSING
        }

    return {
        "valid": True,
        "missing_columns": [],
        "error_code": None
    }


def main():
    """
    Command-line entry point for data validation.
    Expects a path to a CSV file as the first argument.
    Validates the CSV against the schema and exits with code 1 if validation fails.
    """
    if len(sys.argv) < 2:
        print("Usage: python -m src.data.validate <path_to_csv_file>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])

    if not csv_path.exists():
        print(f"Error: Input file not found: {csv_path}")
        sys.exit(1)

    try:
        schema = load_schema()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid schema YAML: {e}")
        sys.exit(1)

    try:
        # Read CSV efficiently
        df = pd.read_csv(csv_path, nrows=1000) # Validate header structure first
        # If header is valid, we could read full data, but for validation of columns,
        # reading a small chunk is sufficient to check schema compliance.
    except Exception as e:
        print(f"Error: Failed to read CSV file: {e}")
        sys.exit(1)

    result = validate_data(df, schema)

    if result["valid"]:
        print("Validation successful: All required columns present.")
        sys.exit(0)
    else:
        missing = ", ".join(result["missing_columns"])
        print(f"Validation failed: {result['error_code']}")
        print(f"Missing columns: {missing}")
        sys.exit(1)


if __name__ == "__main__":
    main()