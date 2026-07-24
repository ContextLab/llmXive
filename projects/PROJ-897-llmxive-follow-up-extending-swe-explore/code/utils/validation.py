"""
Validation utilities for JSONL/Parquet schema validation against contracts.

This module provides functions to validate data artifacts against defined schemas
in the contracts/ directory. It supports JSONL and Parquet formats.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import yaml

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.schemas import get_schema_path, load_schema
from config import get_path, get_config_summary


def validate_field_type(value: Any, expected_type: str) -> Tuple[bool, str]:
    """
    Validate that a field value matches the expected type.

    Args:
        value: The value to validate
        expected_type: The expected type as a string (e.g., 'string', 'integer', 'number', 'boolean', 'array', 'object')

    Returns:
        Tuple of (is_valid, error_message)
    """
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None),
    }

    if expected_type not in type_mapping:
        return False, f"Unknown type: {expected_type}"

    expected_python_type = type_mapping[expected_type]

    # Special handling for integer vs number
    if expected_type == 'integer' and isinstance(value, bool):
        return False, f"Expected integer, got boolean"

    if expected_type == 'number' and isinstance(value, bool):
        return False, f"Expected number, got boolean"

    if not isinstance(value, expected_python_type):
        return False, f"Expected {expected_type} but got {type(value).__name__}: {value}"

    return True, ""


def validate_record_against_schema(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against a schema.

    Args:
        record: The record to validate
        schema: The schema definition

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])

    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Validate each field in the record
    for field, value in record.items():
        if field not in properties:
            # Schema doesn't define this field - could be an error or allowed
            # For now, we'll just warn if it's not in properties
            continue

        field_schema = properties[field]
        expected_type = field_schema.get('type')

        if expected_type:
            is_valid, error_msg = validate_field_type(value, expected_type)
            if not is_valid:
                errors.append(f"Field '{field}': {error_msg}")

        # Handle nested objects
        if expected_type == 'object' and isinstance(value, dict):
            nested_schema = field_schema.get('properties', {})
            if nested_schema:
                nested_errors = validate_record_against_schema(value, {'properties': nested_schema})
                errors.extend([f"{field}.{e}" for e in nested_errors])

        # Handle arrays
        if expected_type == 'array' and isinstance(value, list):
            items_schema = field_schema.get('items', {})
            items_type = items_schema.get('type')
            if items_type:
                for idx, item in enumerate(value):
                    is_valid, error_msg = validate_field_type(item, items_type)
                    if not is_valid:
                        errors.append(f"Field '{field}[{idx}]': {error_msg}")

    return errors


def validate_jsonl_against_schema(file_path: Path, schema_name: str) -> Tuple[bool, List[str], int]:
    """
    Validate a JSONL file against a schema.

    Args:
        file_path: Path to the JSONL file
        schema_name: Name of the schema (without extension)

    Returns:
        Tuple of (all_valid, error_messages, record_count)
    """
    schema = load_schema(schema_name)
    if not schema:
        return False, [f"Schema not found: {schema_name}"], 0

    errors = []
    record_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                    record_count += 1
                    record_errors = validate_record_against_schema(record, schema)
                    if record_errors:
                        for err in record_errors:
                            errors.append(f"Line {line_num}: {err}")
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")

    except FileNotFoundError:
        return False, [f"File not found: {file_path}"], 0
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"], 0

    return len(errors) == 0, errors, record_count


def validate_parquet_against_schema(file_path: Path, schema_name: str) -> Tuple[bool, List[str], int]:
    """
    Validate a Parquet file against a schema.

    Args:
        file_path: Path to the Parquet file
        schema_name: Name of the schema (without extension)

    Returns:
        Tuple of (all_valid, error_messages, record_count)
    """
    try:
        import pandas as pd
        import pyarrow as pa
    except ImportError:
        return False, ["PyArrow or pandas not installed"], 0

    schema = load_schema(schema_name)
    if not schema:
        return False, [f"Schema not found: {schema_name}"], 0

    errors = []
    record_count = 0

    try:
        table = pq.read_table(str(file_path))
        df = table.to_pandas()
        record_count = len(df)

        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])

        # Check required columns
        for field in required_fields:
            if field not in df.columns:
                errors.append(f"Missing required column: {field}")

        # Validate column types
        for col in df.columns:
            if col in properties:
                field_schema = properties[col]
                expected_type = field_schema.get('type')

                if expected_type:
                    # Map schema types to pandas dtypes
                    dtype_map = {
                        'string': 'object',
                        'integer': 'int64',
                        'number': 'float64',
                        'boolean': 'bool',
                    }

                    expected_dtype = dtype_map.get(expected_type)
                    if expected_dtype:
                        actual_dtype = str(df[col].dtype)
                        if expected_dtype not in actual_dtype:
                            errors.append(f"Column '{col}': Expected {expected_dtype}, got {actual_dtype}")

        # Check for null values in required fields
        for field in required_fields:
            if field in df.columns and df[field].isnull().any():
                errors.append(f"Column '{field}' contains null values")

    except FileNotFoundError:
        return False, [f"File not found: {file_path}"], 0
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"], 0

    return len(errors) == 0, errors, record_count


def validate_dataset_artifact(file_path: Path, schema_name: str) -> Dict[str, Any]:
    """
    Validate a dataset artifact (JSONL or Parquet) against a schema.

    Args:
        file_path: Path to the artifact file
        schema_name: Name of the schema

    Returns:
        Validation result dictionary
    """
    result = {
        'file': str(file_path),
        'schema': schema_name,
        'valid': False,
        'errors': [],
        'record_count': 0,
        'format': None,
    }

    if not file_path.exists():
        result['errors'].append(f"File not found: {file_path}")
        return result

    file_ext = file_path.suffix.lower()

    if file_ext == '.jsonl':
        result['format'] = 'jsonl'
        valid, errors, count = validate_jsonl_against_schema(file_path, schema_name)
        result['valid'] = valid
        result['errors'] = errors
        result['record_count'] = count

    elif file_ext == '.parquet':
        result['format'] = 'parquet'
        valid, errors, count = validate_parquet_against_schema(file_path, schema_name)
        result['valid'] = valid
        result['errors'] = errors
        result['record_count'] = count

    else:
        result['errors'].append(f"Unsupported file format: {file_ext}")

    return result


def validate_all_curated_artifacts() -> Dict[str, Any]:
    """
    Validate all curated artifacts against their respective schemas.

    Returns:
        Comprehensive validation report
    """
    config_summary = get_config_summary()
    curated_dir = get_path('curated')

    # Define mapping of files to schemas
    file_schema_map = {
        'hard_subset.jsonl': 'dataset_schema',
        'non_hard_subset.jsonl': 'dataset_schema',
        'synthetic_issues.jsonl': 'dataset_schema',
        'ground_truth.jsonl': 'dataset_schema',
        'bench.final.public.jsonl': 'dataset_schema',
        'swe_explore_with_gt.jsonl': 'dataset_schema',
        'swe_explore_raw.jsonl': 'dataset_schema',
    }

    results = {
        'timestamp': config_summary.get('timestamp', ''),
        'curated_directory': str(curated_dir),
        'artifacts': {},
        'summary': {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'missing': 0,
        }
    }

    for file_name, schema_name in file_schema_map.items():
        file_path = curated_dir / file_name
        result = validate_dataset_artifact(file_path, schema_name)
        results['artifacts'][file_name] = result
        results['summary']['total'] += 1

        if not file_path.exists():
            results['summary']['missing'] += 1
        elif result['valid']:
            results['summary']['valid'] += 1
        else:
            results['summary']['invalid'] += 1

    return results


def generate_validation_report(report_data: Dict[str, Any]) -> str:
    """
    Generate a human-readable validation report.

    Args:
        report_data: The validation report data

    Returns:
        Markdown formatted report
    """
    lines = [
        "# Data Validation Report",
        "",
        f"**Timestamp:** {report_data.get('timestamp', 'N/A')}",
        f"**Curated Directory:** {report_data.get('curated_directory', 'N/A')}",
        "",
        "## Summary",
        "",
        f"- Total artifacts checked: {report_data['summary']['total']}",
        f"- Valid: {report_data['summary']['valid']}",
        f"- Invalid: {report_data['summary']['invalid']}",
        f"- Missing: {report_data['summary']['missing']}",
        "",
        "## Artifact Details",
        "",
    ]

    for file_name, result in report_data['artifacts'].items():
        status = "✅ PASS" if result['valid'] else "❌ FAIL"
        lines.append(f"### {file_name}")
        lines.append(f"- **Status:** {status}")
        lines.append(f"- **Format:** {result.get('format', 'N/A')}")
        lines.append(f"- **Records:** {result.get('record_count', 0)}")

        if result['errors']:
            lines.append("- **Errors:**")
            for error in result['errors']:
                lines.append(f"  - {error}")
        else:
            lines.append("- **Errors:** None")

        lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point for validation script."""
    config_summary = get_config_summary()
    print(f"Running validation with config: {config_summary}")

    # Validate all curated artifacts
    report_data = validate_all_curated_artifacts()

    # Generate and print report
    report = generate_validation_report(report_data)
    print(report)

    # Save report to file
    results_dir = get_path('results')
    report_path = results_dir / 'validation_report.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nValidation report saved to: {report_path}")

    # Exit with error code if any validations failed
    if report_data['summary']['invalid'] > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
