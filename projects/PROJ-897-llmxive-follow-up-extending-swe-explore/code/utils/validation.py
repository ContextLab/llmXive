"""
Validation utilities for JSONL/Parquet schema validation against contracts.

This module provides functions to validate data artifacts against the
schemas defined in the contracts/ directory. It ensures data integrity
and consistency across the pipeline.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import yaml

from config import get_path, get_config_summary
from utils.schemas import get_schema_path, load_schema


def validate_field_type(value: Any, expected_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a value matches the expected type.

    Args:
        value: The value to validate
        expected_type: The expected type as a string ('string', 'integer', 'number', 'boolean', 'array', 'object', 'null')

    Returns:
        Tuple of (is_valid, error_message)
    """
    type_mapping = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }

    if expected_type not in type_mapping:
        return False, f"Unknown type: {expected_type}"

    expected_python_type = type_mapping[expected_type]

    # Special handling for integer vs number
    if expected_type == 'integer' and isinstance(value, bool):
        return False, f"Expected integer but got boolean: {value}"

    if not isinstance(value, expected_python_type):
        return False, f"Expected {expected_type} but got {type(value).__name__}: {value}"

    return True, None


def validate_record_against_schema(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against a schema.

    Args:
        record: The record to validate
        schema: The schema definition

    Returns:
        List of validation error messages
    """
    errors = []
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])

    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Validate field types
    for field, value in record.items():
        if field in properties:
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
                    for nested_error in nested_errors:
                        errors.append(f"Field '{field}': {nested_error}")

            # Handle arrays
            if expected_type == 'array' and isinstance(value, list):
                items_schema = field_schema.get('items', {})
                items_type = items_schema.get('type')
                if items_type:
                    for idx, item in enumerate(value):
                        is_valid, error_msg = validate_field_type(item, items_type)
                        if not is_valid:
                            errors.append(f"Field '{field}[{idx}]': {error_msg}")

    # Check for unexpected fields (strict mode)
    strict_mode = schema.get('strict', False)
    if strict_mode:
        allowed_fields = set(properties.keys())
        for field in record.keys():
            if field not in allowed_fields:
                errors.append(f"Unexpected field: {field}")

    return errors


def validate_jsonl_against_schema(file_path: Path, schema_name: str) -> Tuple[int, int, List[str]]:
    """
    Validate a JSONL file against a schema.

    Args:
        file_path: Path to the JSONL file
        schema_name: Name of the schema to validate against

    Returns:
        Tuple of (total_records, valid_records, list of error messages)
    """
    schema_path = get_schema_path(schema_name)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    schema = load_schema(schema_path)
    errors = []
    valid_count = 0
    total_count = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            total_count += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_num}: Invalid JSON - {e}")
                continue

            record_errors = validate_record_against_schema(record, schema)
            if record_errors:
                for err in record_errors:
                    errors.append(f"Line {line_num}: {err}")
            else:
                valid_count += 1

    return total_count, valid_count, errors


def validate_parquet_against_schema(file_path: Path, schema_name: str) -> Tuple[int, int, List[str]]:
    """
    Validate a Parquet file against a schema.

    Args:
        file_path: Path to the Parquet file
        schema_name: Name of the schema to validate against

    Returns:
        Tuple of (total_records, valid_records, list of error messages)
    """
    try:
        import pandas as pd
        import pyarrow as pa
    except ImportError:
        raise ImportError("pandas and pyarrow are required for Parquet validation")

    schema_path = get_schema_path(schema_name)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    schema = load_schema(schema_path)
    errors = []

    df = pd.read_parquet(file_path)
    total_count = len(df)
    valid_count = 0

    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])

    # Check required fields
    for field in required_fields:
        if field not in df.columns:
            errors.append(f"Missing required column: {field}")

    # Validate column types
    type_mapping = {
        'string': 'object',
        'integer': 'int64',
        'number': 'float64',
        'boolean': 'bool',
        'null': 'object'
    }

    for col in df.columns:
        if col in properties:
            expected_type = properties[col].get('type')
            if expected_type and expected_type in type_mapping:
                expected_dtype = type_mapping[expected_type]
                if df[col].dtype != expected_dtype:
                    errors.append(f"Column '{col}': Expected {expected_dtype} but got {df[col].dtype}")

    # Validate each row
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        record_errors = validate_record_against_schema(row_dict, schema)
        if record_errors:
            for err in record_errors:
                errors.append(f"Row {idx}: {err}")
        else:
            valid_count += 1

    return total_count, valid_count, errors


def validate_dataset_artifact(artifact_path: Path, schema_name: str) -> Dict[str, Any]:
    """
    Validate a dataset artifact (JSONL or Parquet) against a schema.

    Args:
        artifact_path: Path to the artifact file
        schema_name: Name of the schema to validate against

    Returns:
        Dictionary with validation results
    """
    result = {
        'path': str(artifact_path),
        'schema': schema_name,
        'exists': artifact_path.exists(),
        'valid': False,
        'total_records': 0,
        'valid_records': 0,
        'errors': []
    }

    if not result['exists']:
        result['errors'].append(f"File not found: {artifact_path}")
        return result

    try:
        if artifact_path.suffix == '.jsonl':
            total, valid, errors = validate_jsonl_against_schema(artifact_path, schema_name)
        elif artifact_path.suffix in ['.parquet', '.pq']:
            total, valid, errors = validate_parquet_against_schema(artifact_path, schema_name)
        else:
            result['errors'].append(f"Unsupported file format: {artifact_path.suffix}")
            return result

        result['total_records'] = total
        result['valid_records'] = valid
        result['errors'] = errors
        result['valid'] = len(errors) == 0

    except Exception as e:
        result['errors'].append(f"Validation error: {str(e)}")

    return result


def validate_all_curated_artifacts() -> Dict[str, Any]:
    """
    Validate all curated data artifacts against their schemas.

    Returns:
        Dictionary with validation results for all artifacts
    """
    curated_dir = get_path('curated')
    results = {
        'artifacts': {},
        'summary': {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'missing': 0
        }
    }

    # Define artifact-schema mappings
    artifact_mappings = [
        ('hard_subset.jsonl', 'dataset_schema'),
        ('non_hard_subset.jsonl', 'dataset_schema'),
        ('synthetic_issues.jsonl', 'dataset_schema'),
        ('bench.final.public.gt.jsonl', 'dataset_schema'),
    ]

    for filename, schema_name in artifact_mappings:
        artifact_path = curated_dir / filename
        result = validate_dataset_artifact(artifact_path, schema_name)
        results['artifacts'][filename] = result
        results['summary']['total'] += 1

        if result['valid']:
            results['summary']['valid'] += 1
        elif not result['exists']:
            results['summary']['missing'] += 1
        else:
            results['summary']['invalid'] += 1

    return results


def generate_validation_report(validation_results: Dict[str, Any]) -> str:
    """
    Generate a human-readable validation report.

    Args:
        validation_results: Results from validate_all_curated_artifacts

    Returns:
        Markdown-formatted validation report
    """
    lines = [
        "# Validation Report",
        "",
        f"Generated: {get_config_summary()['timestamp']}",
        "",
        "## Summary",
        "",
        f"- Total artifacts: {validation_results['summary']['total']}",
        f"- Valid: {validation_results['summary']['valid']}",
        f"- Invalid: {validation_results['summary']['invalid']}",
        f"- Missing: {validation_results['summary']['missing']}",
        "",
        "## Artifact Details",
        ""
    ]

    for artifact_name, result in validation_results['artifacts'].items():
        status = "✓ Valid" if result['valid'] else "✗ Invalid"
        lines.append(f"### {artifact_name}")
        lines.append(f"- Status: {status}")
        lines.append(f"- Exists: {result['exists']}")
        lines.append(f"- Total records: {result['total_records']}")
        lines.append(f"- Valid records: {result['valid_records']}")

        if result['errors']:
            lines.append("- Errors:")
            for error in result['errors'][:10]:  # Limit to first 10 errors
                lines.append(f"  - {error}")
            if len(result['errors']) > 10:
                lines.append(f"  ... and {len(result['errors']) - 10} more errors")

        lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point for validation script."""
    print("Starting validation of curated artifacts...")

    config = get_config_summary()
    print(f"Config: {config}")

    results = validate_all_curated_artifacts()

    # Print summary
    print(f"\nValidation Summary:")
    print(f"  Total: {results['summary']['total']}")
    print(f"  Valid: {results['summary']['valid']}")
    print(f"  Invalid: {results['summary']['invalid']}")
    print(f"  Missing: {results['summary']['missing']}")

    # Generate and save report
    report = generate_validation_report(results)
    report_path = get_path('curated') / 'validation_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\nValidation report saved to: {report_path}")

    # Exit with error if any artifacts are invalid
    if results['summary']['invalid'] > 0 or results['summary']['missing'] > 0:
        print("\n⚠️  Validation failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n✓ All artifacts validated successfully.")
        sys.exit(0)


if __name__ == '__main__':
    main()