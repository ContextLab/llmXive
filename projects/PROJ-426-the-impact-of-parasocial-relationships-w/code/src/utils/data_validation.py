"""
Data validation utilities for schema validation and checksum recording.

This module provides functions to:
- Validate data files against YAML schema definitions
- Compute and record file checksums (SHA-256)
- Generate validation reports
"""
import os
import json
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .config import get_config

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

def compute_sha256(filepath: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        filepath: Path to the file to hash
        
    Returns:
        Hex digest of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema definition.
    
    Args:
        schema_path: Path to the schema YAML file
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        yaml.YAMLError: If schema is malformed
    """
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected type.
    
    Args:
        value: The value to check
        expected_type: String representation of expected type
        
    Returns:
        True if type matches, False otherwise
    """
    type_map = {
        'string': str,
        'integer': int,
        'float': float,
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }
    
    expected_py_type = type_map.get(expected_type.lower())
    if expected_py_type is None:
        return True  # Unknown type, skip validation
        
    if expected_type.lower() == 'integer':
        # Allow both int and bool (since bool is subclass of int in Python)
        return isinstance(value, int) and not isinstance(value, bool)
    
    return isinstance(value, expected_py_type)

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against a schema.
    
    Args:
        record: Dictionary representing a data record
        schema: Schema definition dictionary
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])
    
    # Check required fields
    for field in required_fields:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Check field types
    for field, value in record.items():
        if field in properties:
            field_schema = properties[field]
            expected_type = field_schema.get('type')
            if expected_type and value is not None:
                if not validate_field_type(value, expected_type):
                    errors.append(
                        f"Field '{field}' has wrong type: "
                        f"expected {expected_type}, got {type(value).__name__}"
                    )
                
                # Check for null constraint
                if field_schema.get('nullable') is False and value is None:
                    errors.append(f"Field '{field}' cannot be null")
                
                # Check string length constraints
                if expected_type == 'string' and isinstance(value, str):
                    min_len = field_schema.get('minLength')
                    max_len = field_schema.get('maxLength')
                    if min_len is not None and len(value) < min_len:
                        errors.append(
                            f"Field '{field}' length {len(value)} "
                            f"is less than minimum {min_len}"
                        )
                    if max_len is not None and len(value) > max_len:
                        errors.append(
                            f"Field '{field}' length {len(value)} "
                            f"is greater than maximum {max_len}"
                        )
                
                # Check numeric constraints
                if expected_type in ('integer', 'float') and isinstance(value, (int, float)):
                    min_val = field_schema.get('minimum')
                    max_val = field_schema.get('maximum')
                    if min_val is not None and value < min_val:
                        errors.append(
                            f"Field '{field}' value {value} "
                            f"is less than minimum {min_val}"
                        )
                    if max_val is not None and value > max_val:
                        errors.append(
                            f"Field '{field}' value {value} "
                            f"is greater than maximum {max_val}"
                        )
    
    return errors

def validate_parquet_schema(
    filepath: Path,
    schema_path: Path,
    max_records: int = 1000
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a Parquet file against a YAML schema.
    
    Args:
        filepath: Path to the Parquet file
        schema_path: Path to the YAML schema file
        max_records: Maximum number of records to validate
        
    Returns:
        Tuple of (is_valid, report_dict)
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for Parquet validation")
    
    schema = load_schema(schema_path)
    df = pd.read_parquet(filepath)
    
    validation_errors = []
    total_records = len(df)
    validated_records = min(total_records, max_records)
    
    # Validate sample of records
    for i in range(validated_records):
        record = df.iloc[i].to_dict()
        record_errors = validate_record(record, schema)
        if record_errors:
            validation_errors.extend([
                f"Record {i}: {err}" for err in record_errors
            ])
            if len(validation_errors) >= 10:  # Limit error reporting
                break
    
    # Check column presence
    schema_columns = set(schema.get('properties', {}).keys())
    data_columns = set(df.columns)
    missing_columns = schema_columns - data_columns
    
    if missing_columns:
        validation_errors.append(
            f"Missing columns in data: {', '.join(missing_columns)}"
        )
    
    is_valid = len(validation_errors) == 0
    
    report = {
        'file': str(filepath),
        'schema': str(schema_path),
        'is_valid': is_valid,
        'total_records': total_records,
        'validated_records': validated_records,
        'error_count': len(validation_errors),
        'errors': validation_errors[:20],  # Limit reported errors
        'timestamp': datetime.now().isoformat()
    }
    
    return is_valid, report

def validate_csv_schema(
    filepath: Path,
    schema_path: Path,
    max_records: int = 1000
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a CSV file against a YAML schema.
    
    Args:
        filepath: Path to the CSV file
        schema_path: Path to the YAML schema file
        max_records: Maximum number of records to validate
        
    Returns:
        Tuple of (is_valid, report_dict)
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for CSV validation")
    
    schema = load_schema(schema_path)
    df = pd.read_csv(filepath)
    
    validation_errors = []
    total_records = len(df)
    validated_records = min(total_records, max_records)
    
    # Validate sample of records
    for i in range(validated_records):
        record = df.iloc[i].to_dict()
        record_errors = validate_record(record, schema)
        if record_errors:
            validation_errors.extend([
                f"Record {i}: {err}" for err in record_errors
            ])
            if len(validation_errors) >= 10:
                break
    
    # Check column presence
    schema_columns = set(schema.get('properties', {}).keys())
    data_columns = set(df.columns)
    missing_columns = schema_columns - data_columns
    
    if missing_columns:
        validation_errors.append(
            f"Missing columns in data: {', '.join(missing_columns)}"
        )
    
    is_valid = len(validation_errors) == 0
    
    report = {
        'file': str(filepath),
        'schema': str(schema_path),
        'is_valid': is_valid,
        'total_records': total_records,
        'validated_records': validated_records,
        'error_count': len(validation_errors),
        'errors': validation_errors[:20],
        'timestamp': datetime.now().isoformat()
    }
    
    return is_valid, report

def record_checksum(
    filepath: Path,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Compute and record file checksum.
    
    Args:
        filepath: Path to the file to hash
        output_path: Optional path to write checksum report
        
    Returns:
        Dictionary containing checksum information
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    checksum = compute_sha256(filepath)
    file_size = filepath.stat().st_size
    
    record = {
        'file': str(filepath),
        'checksum': checksum,
        'algorithm': 'SHA-256',
        'size_bytes': file_size,
        'timestamp': datetime.now().isoformat()
    }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(record, f, indent=2)
    
    return record

def validate_and_checksum(
    data_path: Path,
    schema_path: Path,
    checksum_output: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Perform full validation and checksum recording for a data file.
    
    Args:
        data_path: Path to the data file (Parquet or CSV)
        schema_path: Path to the YAML schema file
        checksum_output: Optional path to write checksum report
        
    Returns:
        Combined validation and checksum report
    """
    # Determine file type and validate
    if data_path.suffix == '.parquet':
        is_valid, validation_report = validate_parquet_schema(data_path, schema_path)
    elif data_path.suffix == '.csv':
        is_valid, validation_report = validate_csv_schema(data_path, schema_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")
    
    # Compute checksum
    checksum_report = record_checksum(data_path, checksum_output)
    
    # Combine reports
    combined_report = {
        'validation': validation_report,
        'checksum': checksum_report,
        'overall_status': 'passed' if is_valid else 'failed'
    }
    
    return combined_report