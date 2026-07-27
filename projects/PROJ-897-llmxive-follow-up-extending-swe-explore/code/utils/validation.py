"""
Validation module for JSONL/Parquet schema validation against contracts.

This module provides utilities to validate data artifacts against the schemas
defined in the contracts/ directory. It supports both JSONL and Parquet formats.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import yaml

# Import from project utilities
from utils.schemas import get_schema_path, load_schema
from config import get_path, DATA_CURATED, DATA_RAW, DATA_RESULTS
from utils.hash_artifacts import compute_sha256


def validate_field_type(value: Any, expected_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a field value matches the expected type.
    
    Args:
        value: The value to validate
        expected_type: The expected type as a string (e.g., 'string', 'integer', 'number', 'boolean', 'array', 'object')
        
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
    }
    
    if expected_type not in type_mapping:
        return False, f"Unknown type: {expected_type}"
    
    expected = type_mapping[expected_type]
    
    # Special case: integer should not match boolean (bool is subclass of int in Python)
    if expected_type == 'integer' and isinstance(value, bool):
        return False, f"Expected integer, got boolean"
    
    if not isinstance(value, expected):
        return False, f"Expected {expected_type}, got {type(value).__name__}"
    
    return True, None


def validate_record_against_schema(record: Dict[str, Any], schema: Dict[str, Any], record_id: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    Validate a single record against a JSON schema.
    
    Args:
        record: The record to validate
        schema: The JSON schema definition
        record_id: Optional identifier for the record (e.g., issue_id)
        
    Returns:
        Tuple of (is_valid, list of error messages)
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
            # Allow extra fields unless schema specifies strict mode
            if schema.get('additionalProperties') == False:
                errors.append(f"Unexpected field: {field}")
            continue
        
        field_schema = properties[field]
        expected_type = field_schema.get('type')
        
        if expected_type:
            is_valid, error_msg = validate_field_type(value, expected_type)
            if not is_valid:
                field_id = f"{record_id}." if record_id else ""
                errors.append(f"Field '{field_id}{field}': {error_msg}")
        
        # Nested object validation
        if expected_type == 'object' and isinstance(value, dict):
            nested_schema = field_schema.get('properties', {})
            nested_required = field_schema.get('required', [])
            
            for nested_field in nested_required:
                if nested_field not in value:
                    field_id = f"{record_id}." if record_id else ""
                    errors.append(f"Missing required nested field: {field_id}{field}.{nested_field}")
            
            for nested_field, nested_value in value.items():
                if nested_field in nested_schema:
                    nested_type = nested_schema[nested_field].get('type')
                    if nested_type:
                        is_valid, error_msg = validate_field_type(nested_value, nested_type)
                        if not is_valid:
                            field_id = f"{record_id}." if record_id else ""
                            errors.append(f"Field '{field_id}{field}.{nested_field}': {error_msg}")
        
        # Array validation
        if expected_type == 'array' and isinstance(value, list):
            items_schema = field_schema.get('items', {})
            items_type = items_schema.get('type')
            
            for idx, item in enumerate(value):
                if items_type:
                    is_valid, error_msg = validate_field_type(item, items_type)
                    if not is_valid:
                        field_id = f"{record_id}." if record_id else ""
                        errors.append(f"Field '{field_id}{field}[{idx}]': {error_msg}")
    
    return len(errors) == 0, errors


def validate_jsonl_against_schema(file_path: Path, schema_name: str, max_records: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a JSONL file against a schema.
    
    Args:
        file_path: Path to the JSONL file
        schema_name: Name of the schema to validate against (e.g., 'dataset_schema')
        max_records: Maximum number of records to validate (None for all)
        
    Returns:
        Tuple of (all_valid, validation_report)
    """
    schema = load_schema(schema_name)
    if not schema:
        return False, {"error": f"Schema '{schema_name}' not found"}
    
    errors = []
    validated_count = 0
    error_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")
                    error_count += 1
                    continue
                
                # Extract record ID if available
                record_id = record.get('issue_id', record.get('id', f"line_{line_num}"))
                
                is_valid, record_errors = validate_record_against_schema(record, schema, record_id)
                
                if not is_valid:
                    errors.extend(record_errors)
                    error_count += 1
                
                validated_count += 1
                
                if max_records and validated_count >= max_records:
                    break
    
    except FileNotFoundError:
        return False, {"error": f"File not found: {file_path}"}
    except Exception as e:
        return False, {"error": f"Error reading file: {str(e)}"}
    
    report = {
        "file": str(file_path),
        "schema": schema_name,
        "total_records": validated_count,
        "valid_records": validated_count - error_count,
        "invalid_records": error_count,
        "errors": errors[:100],  # Limit error output
        "all_valid": error_count == 0
    }
    
    return error_count == 0, report


def validate_parquet_against_schema(file_path: Path, schema_name: str, max_records: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a Parquet file against a schema.
    
    Args:
        file_path: Path to the Parquet file
        schema_name: Name of the schema to validate against
        max_records: Maximum number of records to validate
        
    Returns:
        Tuple of (all_valid, validation_report)
    """
    try:
        import pandas as pd
    except ImportError:
        return False, {"error": "pandas is required for Parquet validation. Install with: pip install pandas pyarrow"}
    
    schema = load_schema(schema_name)
    if not schema:
        return False, {"error": f"Schema '{schema_name}' not found"}
    
    errors = []
    validated_count = 0
    error_count = 0
    
    try:
        df = pd.read_parquet(file_path)
        
        # Limit records if specified
        if max_records:
            df = df.head(max_records)
        
        for idx, row in df.iterrows():
            record = row.to_dict()
            record_id = record.get('issue_id', record.get('id', f"row_{idx}"))
            
            is_valid, record_errors = validate_record_against_schema(record, schema, record_id)
            
            if not is_valid:
                errors.extend(record_errors)
                error_count += 1
            
            validated_count += 1
    
    except FileNotFoundError:
        return False, {"error": f"File not found: {file_path}"}
    except Exception as e:
        return False, {"error": f"Error reading Parquet file: {str(e)}"}
    
    report = {
        "file": str(file_path),
        "schema": schema_name,
        "total_records": validated_count,
        "valid_records": validated_count - error_count,
        "invalid_records": error_count,
        "errors": errors[:100],
        "all_valid": error_count == 0
    }
    
    return error_count == 0, report


def validate_dataset_artifact(file_path: Path) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a dataset artifact (JSONL or Parquet) against its corresponding schema.
    
    Args:
        file_path: Path to the artifact file
        
    Returns:
        Tuple of (is_valid, validation_report)
    """
    file_name = file_path.name.lower()
    
    if file_name.endswith('.jsonl'):
        # Determine schema based on file name
        if 'hard_subset' in file_name or 'non_hard_subset' in file_name:
            schema_name = 'dataset_schema'
        elif 'synthetic_issues' in file_name:
            schema_name = 'dataset_schema'
        else:
            schema_name = 'dataset_schema'
        
        return validate_jsonl_against_schema(file_path, schema_name)
    
    elif file_name.endswith('.parquet'):
        schema_name = 'dataset_schema'
        return validate_parquet_against_schema(file_path, schema_name)
    
    else:
        return False, {"error": f"Unsupported file format: {file_path.suffix}"}


def validate_all_curated_artifacts() -> Dict[str, Any]:
    """
    Validate all curated artifacts against their schemas.
    
    Returns:
        Comprehensive validation report for all curated artifacts
    """
    curated_dir = get_path(DATA_CURATED)
    results = {}
    all_valid = True
    
    if not curated_dir.exists():
        return {
            "status": "error",
            "message": f"Curated directory not found: {curated_dir}",
            "all_valid": False
        }
    
    artifact_files = [
        "hard_subset.jsonl",
        "non_hard_subset.jsonl",
        "synthetic_issues.jsonl"
    ]
    
    for file_name in artifact_files:
        file_path = curated_dir / file_name
        
        if not file_path.exists():
            results[file_name] = {
                "status": "missing",
                "message": f"File not found: {file_path}",
                "all_valid": False
            }
            all_valid = False
            continue
        
        is_valid, report = validate_dataset_artifact(file_path)
        
        results[file_name] = {
            "status": "valid" if is_valid else "invalid",
            "report": report,
            "all_valid": is_valid
        }
        
        if not is_valid:
            all_valid = False
    
    return {
        "status": "passed" if all_valid else "failed",
        "all_valid": all_valid,
        "artifacts": results
    }


def generate_validation_report(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report for all data artifacts.
    
    Args:
        output_path: Optional path to write the report as JSON
        
    Returns:
        Validation report dictionary
    """
    report = {
        "timestamp": str(Path.cwd()),
        "curated_artifacts": validate_all_curated_artifacts()
    }
    
    # Check raw artifacts
    raw_dir = get_path(DATA_RAW)
    if raw_dir.exists():
        raw_files = list(raw_dir.glob("*.jsonl"))
        raw_results = {}
        for file_path in raw_files:
            is_valid, file_report = validate_dataset_artifact(file_path)
            raw_results[file_path.name] = {
                "status": "valid" if is_valid else "invalid",
                "report": file_report
            }
        report["raw_artifacts"] = raw_results
    
    # Check results artifacts
    results_dir = get_path(DATA_RESULTS)
    if results_dir.exists():
        result_files = list(results_dir.glob("*.jsonl")) + list(results_dir.glob("*.json"))
        result_results = {}
        for file_path in result_files:
            if file_path.suffix == '.jsonl':
                is_valid, file_report = validate_dataset_artifact(file_path)
                result_results[file_path.name] = {
                    "status": "valid" if is_valid else "invalid",
                    "report": file_report
                }
            elif file_path.suffix == '.json':
                # For JSON files, just check if they're valid JSON
                try:
                    with open(file_path, 'r') as f:
                        json.load(f)
                    result_results[file_path.name] = {"status": "valid", "message": "Valid JSON"}
                except json.JSONDecodeError as e:
                    result_results[file_path.name] = {"status": "invalid", "message": str(e)}
        
        report["result_artifacts"] = result_results
    
    # Write report if output path specified
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
    
    return report


def main():
    """Main entry point for validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate data artifacts against schemas")
    parser.add_argument("--output", type=str, help="Path to write validation report JSON")
    parser.add_argument("--file", type=str, help="Validate a specific file")
    parser.add_argument("--schema", type=str, help="Schema name to use for validation")
    
    args = parser.parse_args()
    
    if args.file:
        file_path = Path(args.file)
        schema_name = args.schema or 'dataset_schema'
        
        if file_path.suffix == '.jsonl':
            is_valid, report = validate_jsonl_against_schema(file_path, schema_name)
        elif file_path.suffix == '.parquet':
            is_valid, report = validate_parquet_against_schema(file_path, schema_name)
        else:
            print(f"Error: Unsupported file format: {file_path.suffix}", file=sys.stderr)
            sys.exit(1)
        
        print(json.dumps(report, indent=2))
        sys.exit(0 if is_valid else 1)
    
    else:
        report = generate_validation_report()
        print(json.dumps(report, indent=2))
        
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"\nReport written to: {output_path}")
        
        sys.exit(0 if report.get("curated_artifacts", {}).get("all_valid", False) else 1)


if __name__ == "__main__":
    main()