import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
import re
import yaml
import json
import pandas as pd
from jsonschema import validate, ValidationError as JsonSchemaError, Draft7Validator

# Configure logger for this module
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for schema validation failures."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON Schema from a YAML or JSON file.

    Args:
        schema_path: Relative or absolute path to the schema file.

    Returns:
        The schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse schema YAML: {e}")
            raise

def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected JSON Schema type.

    Args:
        value: The value to check.
        expected_type: The expected type string (e.g., 'string', 'number', 'integer').

    Returns:
        True if valid, False otherwise.
    """
    if expected_type == 'string':
        return isinstance(value, str)
    elif expected_type == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == 'boolean':
        return isinstance(value, bool)
    elif expected_type == 'array':
        return isinstance(value, list)
    elif expected_type == 'object':
        return isinstance(value, dict)
    elif expected_type == 'null':
        return value is None
    return False

def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> bool:
    """
    Validate a value against specific constraints (minimum, maximum, pattern, enum).

    Args:
        value: The value to check.
        constraints: Dictionary of constraints from the schema properties.

    Returns:
        True if valid, False otherwise.
    """
    if 'minimum' in constraints:
        if value < constraints['minimum']:
            return False
    if 'maximum' in constraints:
        if value > constraints['maximum']:
            return False
    if 'pattern' in constraints:
        if not isinstance(value, str) or not re.match(constraints['pattern'], value):
            return False
    if 'enum' in constraints:
        if value not in constraints['enum']:
            return False
    return True

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record (row) against the schema.

    Args:
        record: The dictionary representing the record.
        schema: The loaded schema dictionary.

    Returns:
        A list of error messages. Empty if valid.
    """
    errors = []
    properties = schema.get('properties', {})
    required = schema.get('required', [])

    # Check required fields
    for field in required:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: {field}")

    # Validate each field present in the record
    for key, value in record.items():
        if key in properties:
            prop_schema = properties[key]
            expected_type = prop_schema.get('type')

            # Type check
            if expected_type and not validate_field_type(value, expected_type):
                errors.append(f"Field '{key}' has invalid type. Expected {expected_type}, got {type(value).__name__}")
                continue

            # Constraint check
            if not validate_value_constraints(value, prop_schema):
                errors.append(f"Field '{key}' violates constraints (min/max/pattern/enum).")
        elif not schema.get('additionalProperties', True):
            errors.append(f"Unexpected field in record: {key}")

    return errors

def validate_dataset_file(file_path: str, schema_path: str) -> bool:
    """
    Validate a CSV dataset file against a schema.

    Args:
        file_path: Path to the CSV file.
        schema_path: Path to the schema file.

    Returns:
        True if all records are valid.

    Raises:
        ValidationError: If validation fails.
    """
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        raise ValidationError(f"Failed to load schema: {e}")

    if not os.path.exists(file_path):
        raise ValidationError(f"Data file not found: {file_path}")

    df = pd.read_csv(file_path)
    records = df.to_dict(orient='records')

    all_errors = []
    for idx, record in enumerate(records):
        # Convert numpy types to native python types for validation
        clean_record = {}
        for k, v in record.items():
            if hasattr(v, 'item'): # numpy scalar
                clean_record[k] = v.item()
            else:
                clean_record[k] = v

        errors = validate_record(clean_record, schema)
        if errors:
            all_errors.append(f"Row {idx}: {errors}")

    if all_errors:
        error_msg = f"Validation failed for {len(all_errors)} rows:\n" + "\n".join(all_errors[:10]) # Limit output
        if len(all_errors) > 10:
            error_msg += f"\n... and {len(all_errors) - 10} more errors."
        logger.error(error_msg)
        raise ValidationError(error_msg)

    logger.info(f"Dataset validation passed for {file_path}")
    return True

def validate_output_file_structure(file_path: str, schema_path: str) -> bool:
    """
    Validate an output file (CSV) against the output schema.
    Specifically checks that the columns match the schema properties.

    Args:
        file_path: Path to the CSV file.
        schema_path: Path to the schema file.

    Returns:
        True if valid.

    Raises:
        ValidationError: If validation fails.
    """
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        raise ValidationError(f"Failed to load schema: {e}")

    if not os.path.exists(file_path):
        raise ValidationError(f"Output file not found: {file_path}")

    df = pd.read_csv(file_path)
    required_fields = schema.get('required', [])
    schema_properties = list(schema.get('properties', {}).keys())

    # Check if all required fields are columns
    missing_cols = set(required_fields) - set(df.columns)
    if missing_cols:
        raise ValidationError(f"Output file missing required columns: {missing_cols}")

    # Check if extra columns exist that aren't in schema (if additionalProperties is false)
    if not schema.get('additionalProperties', True):
        extra_cols = set(df.columns) - set(schema_properties)
        if extra_cols:
            raise ValidationError(f"Output file contains unexpected columns: {extra_cols}")

    # Validate row data types and constraints
    records = df.to_dict(orient='records')
    for idx, record in enumerate(records):
        clean_record = {k: (v.item() if hasattr(v, 'item') else v) for k, v in record.items()}
        errors = validate_record(clean_record, schema)
        if errors:
            raise ValidationError(f"Validation failed at row {idx}: {errors}")

    logger.info(f"Output file structure validation passed for {file_path}")
    return True

def validate_against_schema(data: Union[Dict, List[Dict]], schema: Dict[str, Any]) -> bool:
    """
    Generic validation using jsonschema library for a single record or list of records.

    Args:
        data: The data to validate (dict or list of dicts).
        schema: The schema dictionary.

    Returns:
        True if valid.

    Raises:
        ValidationError: If validation fails.
    """
    try:
        if isinstance(data, list):
            for item in data:
                validate(instance=item, schema=schema)
        else:
            validate(instance=data, schema=schema)
        return True
    except JsonSchemaError as e:
        raise ValidationError(f"JSON Schema validation error: {e.message} at path {list(e.path)}")

def main():
    """
    CLI entry point for running schema validation on project artifacts.
    Expects environment variables or arguments to specify paths.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate data against schemas")
    parser.add_argument("--data-file", type=str, help="Path to CSV data file")
    parser.add_argument("--schema-file", type=str, help="Path to schema YAML file")
    parser.add_argument("--type", choices=["dataset", "output"], default="dataset", help="Type of validation to perform")
    args = parser.parse_args()

    if not args.data_file or not args.schema_file:
        print("Usage: python validation.py --data-file <path> --schema-file <path> --type <dataset|output>")
        sys.exit(1)

    try:
        if args.type == "dataset":
            validate_dataset_file(args.data_file, args.schema_file)
        elif args.type == "output":
            validate_output_file_structure(args.data_file, args.schema_file)
        print("Validation successful.")
        sys.exit(0)
    except ValidationError as e:
        print(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()