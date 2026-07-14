"""
Contract validation module for loading YAML schemas and validating pandas DataFrames.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import yaml


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema from the specified path.

    Args:
        schema_path: Path to the YAML schema file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_available_schemas(contracts_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load all YAML schemas from the contracts directory.

    Args:
        contracts_dir: Path to the contracts directory. Defaults to 'specs/contracts'.

    Returns:
        List of loaded schema dictionaries.
    """
    if contracts_dir is None:
        # Default to project root relative path
        contracts_dir = "specs/contracts"

    contracts_path = Path(contracts_dir)
    if not contracts_path.exists():
        raise FileNotFoundError(f"Contracts directory not found: {contracts_dir}")

    schemas = []
    for yaml_file in contracts_path.glob("*.yaml"):
        try:
            schema = load_schema(str(yaml_file))
            schemas.append(schema)
        except Exception as e:
            print(f"Warning: Failed to load {yaml_file}: {e}", file=sys.stderr)

    return schemas


def validate_column_exists(df: pd.DataFrame, column_name: str, schema_name: str = "Unknown") -> None:
    """
    Validate that a column exists in the DataFrame.

    Args:
        df: The DataFrame to validate.
        column_name: The column name to check.
        schema_name: Name of the schema for error reporting.

    Raises:
        SchemaValidationError: If the column is missing.
    """
    if column_name not in df.columns:
        raise SchemaValidationError(
            f"Schema '{schema_name}' requires column '{column_name}' but it is missing from the DataFrame."
        )


def validate_column_type(df: pd.DataFrame, column_name: str, expected_type: str, schema_name: str = "Unknown") -> None:
    """
    Validate that a column has the expected pandas dtype.

    Args:
        df: The DataFrame to validate.
        column_name: The column name to check.
        expected_type: The expected type string (e.g., 'str', 'float', 'int').
        schema_name: Name of the schema for error reporting.

    Raises:
        SchemaValidationError: If the type does not match.
    """
    if column_name not in df.columns:
        return  # Handled by validate_column_exists

    actual_dtype = df[column_name].dtype
    # Map expected type strings to numpy/pandas dtypes
    type_map = {
        'str': 'object',
        'string': 'object',
        'float': 'float64',
        'int': 'int64',
        'bool': 'bool',
        'datetime': 'datetime64[ns]',
    }

    expected_pandas_type = type_map.get(expected_type.lower(), expected_type.lower())

    # Handle object types flexibly (e.g., str vs object)
    if expected_pandas_type == 'object':
        if not pd.api.types.is_object_dtype(actual_dtype) and not pd.api.types.is_string_dtype(actual_dtype):
            raise SchemaValidationError(
                f"Schema '{schema_name}' requires column '{column_name}' to be type '{expected_type}', "
                f"but found '{actual_dtype}'."
            )
    else:
        if not str(actual_dtype).startswith(expected_pandas_type):
            raise SchemaValidationError(
                f"Schema '{schema_name}' requires column '{column_name}' to be type '{expected_type}', "
                f"but found '{actual_dtype}'."
            )


def validate_no_nulls(df: pd.DataFrame, column_name: str, schema_name: str = "Unknown") -> None:
    """
    Validate that a column contains no null values.

    Args:
        df: The DataFrame to validate.
        column_name: The column name to check.
        schema_name: Name of the schema for error reporting.

    Raises:
        SchemaValidationError: If null values are found.
    """
    if column_name not in df.columns:
        return

    null_count = df[column_name].isnull().sum()
    if null_count > 0:
        raise SchemaValidationError(
            f"Schema '{schema_name}' requires column '{column_name}' to have no null values, "
            f"but found {null_count} null(s)."
        )


def validate_column_range(df: pd.DataFrame, column_name: str, min_val: Optional[float] = None, max_val: Optional[float] = None, schema_name: str = "Unknown") -> None:
    """
    Validate that numeric column values fall within a specified range.

    Args:
        df: The DataFrame to validate.
        column_name: The column name to check.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        schema_name: Name of the schema for error reporting.

    Raises:
        SchemaValidationError: If values are out of range.
    """
    if column_name not in df.columns:
        return

    if not pd.api.types.is_numeric_dtype(df[column_name]):
        raise SchemaValidationError(
            f"Schema '{schema_name}' range check requires column '{column_name}' to be numeric, but found '{df[column_name].dtype}'."
        )

    if min_val is not None:
        below_min = (df[column_name] < min_val).sum()
        if below_min > 0:
            raise SchemaValidationError(
                f"Schema '{schema_name}' requires column '{column_name}' values >= {min_val}, but found {below_min} value(s) below."
            )

    if max_val is not None:
        above_max = (df[column_name] > max_val).sum()
        if above_max > 0:
            raise SchemaValidationError(
                f"Schema '{schema_name}' requires column '{column_name}' values <= {max_val}, but found {above_max} value(s) above."
            )


def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> None:
    """
    Validate a DataFrame against a full schema definition.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary loaded from YAML.

    Raises:
        SchemaValidationError: If any validation rule fails.
    """
    schema_name = schema.get('name', 'Unknown')

    # Check all required columns exist
    for col_def in schema.get('columns', []):
        col_name = col_def['name']
        validate_column_exists(df, col_name, schema_name)

        # Check type
        if 'type' in col_def:
            validate_column_type(df, col_name, col_def['type'], schema_name)

        # Check nulls
        nullable = col_def.get('nullable', True)
        if not nullable:
            validate_no_nulls(df, col_name, schema_name)

        # Check range if specified
        if 'min' in col_def or 'max' in col_def:
            validate_column_range(
                df, col_name,
                min_val=col_def.get('min'),
                max_val=col_def.get('max'),
                schema_name=schema_name
            )


def validate_dataframe_against_contract(df: pd.DataFrame, contract_name: str, contracts_dir: Optional[str] = None) -> bool:
    """
    Validate a DataFrame against a specific named contract.

    Args:
        df: The DataFrame to validate.
        contract_name: The 'name' field of the schema to validate against.
        contracts_dir: Path to the contracts directory.

    Returns:
        True if validation passes.

    Raises:
        SchemaValidationError: If validation fails.
        ValueError: If the contract name is not found.
    """
    schemas = get_available_schemas(contracts_dir)
    target_schema = None

    for schema in schemas:
        if schema.get('name') == contract_name:
            target_schema = schema
            break

    if target_schema is None:
        raise ValueError(f"Contract '{contract_name}' not found in {contracts_dir or 'specs/contracts'}.")

    validate_schema(df, target_schema)
    return True


def validate_all_contracts(df: pd.DataFrame, contracts_dir: Optional[str] = None) -> List[str]:
    """
    Validate a DataFrame against all available contracts.

    Args:
        df: The DataFrame to validate.
        contracts_dir: Path to the contracts directory.

    Returns:
        List of contract names that passed validation.

    Raises:
        SchemaValidationError: If the DataFrame fails validation for any contract.
    """
    schemas = get_available_schemas(contracts_dir)
    passed_contracts = []

    for schema in schemas:
        try:
            validate_schema(df, schema)
            passed_contracts.append(schema.get('name'))
        except SchemaValidationError:
            # Re-raise immediately on first failure to stop execution
            raise

    return passed_contracts


def main():
    """
    CLI entry point for validating a CSV file against a specific contract.
    Usage: python -m src.validation.validate_contracts --file path/to/data.csv --contract contract_name
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate a CSV file against a YAML contract schema.")
    parser.add_argument('--file', required=True, help="Path to the CSV file to validate.")
    parser.add_argument('--contract', required=True, help="Name of the contract schema to validate against.")
    parser.add_argument('--contracts-dir', default='specs/contracts', help="Path to the contracts directory.")

    args = parser.parse_args()

    try:
        df = pd.read_csv(args.file)
        print(f"Loaded {len(df)} rows from {args.file}")
        validate_dataframe_against_contract(df, args.contract, args.contracts_dir)
        print(f"SUCCESS: DataFrame validated against contract '{args.contract}'.")
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except SchemaValidationError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
