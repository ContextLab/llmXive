"""
Schema Validator for Heusler Alloy Data Pipeline.

Validates processed data against canonical YAML schemas defined in
specs/001-predict-heusler-hysteresis/contracts/.

Implements T011: Validate processed data against canonical schemas.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from .logging_config import setup_logging, create_logger

# Initialize logger
logger = create_logger(__name__)


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a canonical schema from a YAML file.

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    if schema is None:
        raise ValueError(f"Schema file is empty: {path}")

    logger.info(f"Loaded schema from {path}")
    return schema


def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected type string.

    Supports: string, number, integer, boolean, array, object, null

    Args:
        value: The value to check.
        expected_type: The expected type name.

    Returns:
        True if the value matches the type, False otherwise.
    """
    type_mapping = {
        'string': str,
        'number': (int, float),
        'integer': int,
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }

    if expected_type not in type_mapping:
        logger.warning(f"Unknown type '{expected_type}', treating as string")
        return isinstance(value, str)

    expected = type_mapping[expected_type]

    # Special case: bool is subclass of int in Python
    if expected_type == 'integer' and isinstance(value, bool):
        return False
    if expected_type == 'boolean' and isinstance(value, int):
        return False

    return isinstance(value, expected)


def validate_pattern(value: str, pattern: str) -> bool:
    """
    Validate that a string matches a regex pattern.

    Args:
        value: The string to check.
        pattern: The regex pattern.

    Returns:
        True if the value matches the pattern, False otherwise.
    """
    if not isinstance(value, str):
        return False
    try:
        return bool(re.fullmatch(pattern, value))
    except re.error:
        logger.error(f"Invalid regex pattern: {pattern}")
        return False


def validate_range(value: Union[int, float], min_val: Optional[float], max_val: Optional[float]) -> bool:
    """
    Validate that a number is within the specified range.

    Args:
        value: The number to check.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).

    Returns:
        True if the value is within range, False otherwise.
    """
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    return True


def validate_field(value: Any, field_schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single field value against its schema definition.

    Args:
        value: The value to validate.
        field_schema: The schema definition for this field.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    field_name = field_schema.get('name', 'unknown')
    field_type = field_schema.get('type', 'string')
    required = field_schema.get('required', True)
    pattern = field_schema.get('pattern')
    min_val = field_schema.get('min')
    max_val = field_schema.get('max')
    enum_values = field_schema.get('enum')

    # Check required
    if value is None:
        if required:
            errors.append(f"Field '{field_name}' is required but missing or null")
            return False, errors
        else:
            return True, []

    # Type check
    if not validate_type(value, field_type):
        errors.append(f"Field '{field_name}' has wrong type: expected {field_type}, got {type(value).__name__}")
        return False, errors

    # Pattern check (strings only)
    if pattern is not None and isinstance(value, str):
        if not validate_pattern(value, pattern):
            errors.append(f"Field '{field_name}' value '{value}' does not match pattern '{pattern}'")
            return False, errors

    # Range check (numbers only)
    if (min_val is not None or max_val is not None) and isinstance(value, (int, float)):
        if not validate_range(value, min_val, max_val):
            errors.append(f"Field '{field_name}' value {value} is out of range [{min_val}, {max_val}]")
            return False, errors

    # Enum check
    if enum_values is not None:
        if value not in enum_values:
            errors.append(f"Field '{field_name}' value '{value}' not in allowed values: {enum_values}")
            return False, errors

    return True, []


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single record (row) against a schema.

    Args:
        record: The dictionary representing a single record.
        schema: The schema definition containing 'fields' list.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    fields = schema.get('fields', [])

    # Check each field defined in schema
    for field_def in fields:
        field_name = field_def.get('name')
        if not field_name:
            continue

        value = record.get(field_name)
        is_valid, field_errors = validate_field(value, field_def)
        if not is_valid:
            errors.extend(field_errors)

    # Check for required fields that might not be in schema but are required
    # (Handled by schema definition, but good to double-check)
    for field_def in fields:
        if field_def.get('required', True):
            field_name = field_def.get('name')
            if field_name and field_name not in record:
                # Already caught by validate_field with None value
                pass

    return len(errors) == 0, errors


def validate_dataset(
    data: List[Dict[str, Any]],
    schema: Dict[str, Any],
    max_errors: int = 10
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate an entire dataset (list of records) against a schema.

    Args:
        data: List of dictionaries, each representing a record.
        schema: The schema definition.
        max_errors: Maximum number of errors to collect before stopping.

    Returns:
        Tuple of (is_valid, report_dict).
        report_dict contains: total_records, valid_records, invalid_records, errors (list)
    """
    if not isinstance(data, list):
        return False, {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'errors': ['Data must be a list of records'],
            'is_valid': False
        }

    total = len(data)
    valid_count = 0
    invalid_count = 0
    all_errors = []

    for idx, record in enumerate(data):
        if not isinstance(record, dict):
            all_errors.append(f"Record {idx} is not a dictionary")
            invalid_count += 1
            continue

        is_valid, errors = validate_record(record, schema)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            for err in errors:
                all_errors.append(f"Record {idx}: {err}")
                if len(all_errors) >= max_errors:
                    break
        if len(all_errors) >= max_errors:
            break

    is_valid = invalid_count == 0
    report = {
        'total_records': total,
        'valid_records': valid_count,
        'invalid_records': invalid_count,
        'errors': all_errors,
        'is_valid': is_valid
    }

    if is_valid:
        logger.info(f"Validation passed: {valid_count}/{total} records valid")
    else:
        logger.warning(f"Validation failed: {invalid_count}/{total} records invalid")
        logger.warning(f"Sample errors: {all_errors[:3]}")

    return is_valid, report


def validate_json_file(
    file_path: Union[str, Path],
    schema_path: Union[str, Path]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a JSON file against a schema.

    Args:
        file_path: Path to the JSON file to validate.
        schema_path: Path to the schema YAML file.

    Returns:
        Tuple of (is_valid, report_dict).
    """
    path = Path(file_path)
    if not path.exists():
        return False, {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'errors': [f"Data file not found: {path}"],
            'is_valid': False
        }

    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            return False, {
                'total_records': 0,
                'valid_records': 0,
                'invalid_records': 0,
                'errors': [f"Invalid JSON: {str(e)}"],
                'is_valid': False
            }

    schema = load_schema(schema_path)
    return validate_dataset(data, schema)


def validate_csv_file(
    file_path: Union[str, Path],
    schema_path: Union[str, Path]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a CSV file against a schema.

    Args:
        file_path: Path to the CSV file to validate.
        schema_path: Path to the schema YAML file.

    Returns:
        Tuple of (is_valid, report_dict).
    """
    import csv

    path = Path(file_path)
    if not path.exists():
        return False, {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'errors': [f"Data file not found: {path}"],
            'is_valid': False
        }

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Convert numeric strings to numbers if schema expects numbers
    schema = load_schema(schema_path)
    fields = schema.get('fields', [])
    type_map = {f['name']: f['type'] for f in fields}

    for record in data:
        for key, value in record.items():
            if key in type_map:
                if type_map[key] == 'integer' and value not in (None, ''):
                    try:
                        record[key] = int(value)
                    except ValueError:
                        pass  # Let validation catch the type error
                elif type_map[key] == 'number' and value not in (None, ''):
                    try:
                        record[key] = float(value)
                    except ValueError:
                        pass  # Let validation catch the type error
                elif type_map[key] == 'boolean':
                    if value in ('true', 'True', '1'):
                        record[key] = True
                    elif value in ('false', 'False', '0'):
                        record[key] = False
                    else:
                        record[key] = None  # Will be caught by required check

    return validate_dataset(data, schema)


def main():
    """
    Main entry point for command-line usage.

    Usage:
        python -m src.utils.schema_validator --data <path> --schema <path> [--format <csv|json>]
    """
    import argparse

    parser = argparse.ArgumentParser(description='Validate data against schema')
    parser.add_argument('--data', required=True, help='Path to data file (CSV or JSON)')
    parser.add_argument('--schema', required=True, help='Path to schema YAML file')
    parser.add_argument('--format', choices=['csv', 'json'], default=None,
                        help='Data format (auto-detected if not specified)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        setup_logging(level=logging.DEBUG)

    data_path = Path(args.data)
    schema_path = Path(args.schema)

    if args.format is None:
        if data_path.suffix.lower() == '.json':
          fmt = 'json'
        elif data_path.suffix.lower() in ['.csv']:
            fmt = 'csv'
        else:
            fmt = 'csv'  # Default assumption
    else:
        fmt = args.format

    logger.info(f"Validating {data_path} against {schema_path} (format: {fmt})")

    if fmt == 'json':
        is_valid, report = validate_json_file(data_path, schema_path)
    else:
        is_valid, report = validate_csv_file(data_path, schema_path)

    print(json.dumps(report, indent=2))

    if is_valid:
        logger.info("Validation successful")
        return 0
    else:
        logger.error("Validation failed")
        return 1


if __name__ == '__main__':
    exit(main())
