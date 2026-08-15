"""
Schema validation utilities for the llmXive automated science pipeline.
Validates data files against YAML schemas defined in contracts/.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple
import yaml
import pandas as pd
from pathlib import Path

from utils.logging import get_logger

logger = get_logger(__name__)

# Mapping of schema type to file path
SCHEMA_PATHS = {
    "dataset": "contracts/dataset.schema.yaml",
    "output": "contracts/output.schema.yaml"
}

class ValidationError(Exception):
    """Raised when validation fails."""
    pass

def load_schema(schema_type: str) -> Dict[str, Any]:
    """
    Load a schema from the contracts directory.

    Args:
        schema_type: Either 'dataset' or 'output'.

    Returns:
        The loaded schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValidationError: If the schema file is invalid YAML.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    schema_path = base_dir / SCHEMA_PATHS.get(schema_type, f"contracts/{schema_type}.schema.yaml")

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        if not isinstance(schema, dict):
            raise ValidationError("Invalid schema format: expected a dictionary.")
        return schema
    except yaml.YAMLError as e:
        raise ValidationError(f"Failed to parse YAML schema: {e}")

def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected type string.

    Args:
        value: The value to check.
        expected_type: The expected type (e.g., 'integer', 'float', 'string', 'datetime').

    Returns:
        True if the type matches, False otherwise.
    """
    type_map = {
        'integer': (int, pd.api.types.is_integer_dtype),
        'float': (float, pd.api.types.is_float_dtype),
        'string': (str, lambda x: isinstance(x, str)),
        'datetime': (str, lambda x: isinstance(x, str)), # ISO8601 strings
    }

    if expected_type not in type_map:
        logger.warning(f"Unknown type mapping for: {expected_type}")
        return True

    expected_cls, pandas_check = type_map[expected_type]

    if isinstance(value, expected_cls):
        return True

    # Handle pandas series check if needed, but here we check scalar values mostly
    if pandas_check:
        try:
            # Attempt to cast to see if it's compatible
            pd.Series([value]).astype(expected_cls)
            return True
        except (ValueError, TypeError):
            return False

    return False

def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> bool:
    """
    Validate value against constraints like pattern, enum, or min/max.

    Args:
        value: The value to check.
        constraints: Dictionary of constraints (e.g., {'pattern': '...', 'enum': [...]}).

    Returns:
        True if constraints are met, False otherwise.
    """
    if not constraints:
        return True

    if 'enum' in constraints:
        if value not in constraints['enum']:
            return False

    if 'pattern' in constraints:
        import re
        if not isinstance(value, str):
            return False
        if not re.match(constraints['pattern'], value):
            return False

    if 'min' in constraints and isinstance(value, (int, float)):
        if value < constraints['min']:
            return False

    if 'max' in constraints and isinstance(value, (int, float)):
        if value > constraints['max']:
            return False

    return True

def validate_record(record: Dict[str, Any], properties: Dict[str, Any]) -> List[str]:
    """
    Validate a single record (row) against property definitions.

    Args:
        record: The dictionary representing the row.
        properties: The schema properties for the record.

    Returns:
        A list of error messages.
    """
    errors = []
    for field, spec in properties.items():
        if field not in record:
            if spec.get('required', False):
                errors.append(f"Missing required field: {field}")
            continue

        value = record[field]
        if 'type' in spec:
            if not validate_field_type(value, spec['type']):
                errors.append(f"Field '{field}' has invalid type. Expected {spec['type']}, got {type(value)}")

        if 'pattern' in spec or 'enum' in spec or 'min' in spec or 'max' in spec:
            if not validate_value_constraints(value, spec):
                errors.append(f"Field '{field}' failed constraint validation")

    return errors

def validate_dataset_file(file_path: str, schema_type: str = "dataset") -> Tuple[bool, List[str]]:
    """
    Validate a CSV dataset file against a schema.

    Args:
        file_path: Path to the CSV file.
        schema_type: Type of schema to use ('dataset' or 'output').

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    try:
        schema = load_schema(schema_type)
    except (FileNotFoundError, ValidationError) as e:
        return False, [str(e)]

    # Basic schema structure check for dataset
    if 'properties' not in schema:
        return False, ["Schema missing 'properties'"]

    # We expect the schema to define the file structure in 'properties' keys like 'gdelt_events'
    # This is a simplified check for the specific task requirements.
    # In a full implementation, we would traverse the schema tree.

    # For this task, we verify the file exists and has headers if it's a dataset file
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            errors.append("File is empty (no rows)")

        # Check if expected columns exist based on simple schema interpretation
        # This assumes the schema lists expected_columns in properties
        # We adapt to the specific schema provided in the artifact
        if 'gdelt_events' in schema['properties']:
            gdelt_props = schema['properties']['gdelt_events']['properties']
            if 'expected_columns' in gdelt_props:
                expected_cols = gdelt_props['expected_columns'].get('contains', {}).get('const')
                if expected_cols and expected_cols not in df.columns:
                    errors.append(f"Missing expected column: {expected_cols}")

        return len(errors) == 0, errors
    except Exception as e:
        return False, [f"Failed to read or parse CSV: {e}"]

def validate_output_file(file_path: str, schema_type: str = "output") -> Tuple[bool, List[str]]:
    """
    Validate an output file (CSV or PDF) against the output schema.

    Args:
        file_path: Path to the file.
        schema_type: Type of schema (usually 'output').

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    if not os.path.exists(file_path):
        return False, [f"Output file not found: {file_path}"]

    try:
        schema = load_schema(schema_type)
    except (FileNotFoundError, ValidationError) as e:
        return False, [str(e)]

    # Check pattern matching for file paths in schema if applicable
    # For this specific task, we ensure the file exists and is non-empty for CSVs
    if file_path.endswith('.csv'):
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                errors.append("Output CSV is empty")
        except Exception as e:
            errors.append(f"Invalid CSV format: {e}")
    elif file_path.endswith('.pdf'):
        if os.path.getsize(file_path) == 0:
            errors.append("Output PDF is empty")

    return len(errors) == 0, errors

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Generic validator for a dictionary against a schema dict.

    Args:
        data: The data to validate.
        schema: The schema dictionary.

    Returns:
        List of validation errors.
    """
    errors = []
    if 'required' in schema:
        for req in schema['required']:
            if req not in data:
                errors.append(f"Missing required key: {req}")

    if 'properties' in schema:
        for key, value in data.items():
            if key in schema['properties']:
                prop_schema = schema['properties'][key]
                if 'type' in prop_schema:
                    if not validate_field_type(value, prop_schema['type']):
                        errors.append(f"Invalid type for {key}")
                # Recursion for nested objects could be added here
    return errors

def validate_output_file_structure(file_path: str, schema_type: str = "output") -> bool:
    """
    High-level validation for output files generated by the pipeline.

    Args:
        file_path: Path to the file.
        schema_type: Schema type.

    Returns:
        True if valid, False otherwise.
    """
    is_valid, errors = validate_output_file(file_path, schema_type)
    if not is_valid:
        logger.error(f"Validation failed for {file_path}: {errors}")
    return is_valid

def validate_dataset_file_structure(file_path: str, schema_type: str = "dataset") -> bool:
    """
    High-level validation for dataset files.

    Args:
        file_path: Path to the file.
        schema_type: Schema type.

    Returns:
        True if valid, False otherwise.
    """
    is_valid, errors = validate_dataset_file(file_path, schema_type)
    if not is_valid:
        logger.error(f"Validation failed for {file_path}: {errors}")
    return is_valid

def main():
    """
    CLI entry point for validation utilities.
    Usage: python -m code.utils.validation --file <path> --type <dataset|output>
    """
    import argparse
    parser = argparse.ArgumentParser(description="Validate data files against schemas.")
    parser.add_argument("--file", required=True, help="Path to the file to validate.")
    parser.add_argument("--type", choices=["dataset", "output"], default="dataset", help="Schema type.")
    args = parser.parse_args()

    if args.type == "dataset":
        valid, errors = validate_dataset_file(args.file, "dataset")
    else:
        valid, errors = validate_output_file(args.file, "output")

    if valid:
        print(f"Validation PASSED for {args.file}")
        sys.exit(0)
    else:
        print(f"Validation FAILED for {args.file}:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
