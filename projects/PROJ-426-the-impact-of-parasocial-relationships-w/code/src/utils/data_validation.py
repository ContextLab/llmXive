"""
Data validation utilities for schema enforcement and checksum recording.

This module provides functions to:
- Load and parse YAML schemas
- Validate data records and Parquet/CSV files against schemas
- Compute and record SHA-256 checksums for data integrity
"""
import os
import json
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import pyarrow as pa
from pyarrow.parquet import ParquetFile

class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML schema definition.
    
    Args:
        schema_path: Path to the YAML schema file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the YAML is malformed.
    """
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected type string.
    
    Supported types: 'string', 'int', 'float', 'boolean', 'date', 'timestamp', 'null', 'any'
    
    Args:
        value: The value to check.
        expected_type: The expected type as a string.
        
    Returns:
        True if the value matches the type, False otherwise.
    """
    if value is None:
        return expected_type.lower() in ('null', 'any')
    
    type_lower = expected_type.lower()
    
    if type_lower == 'any':
        return True
    elif type_lower == 'string':
        return isinstance(value, str)
    elif type_lower == 'int':
        return isinstance(value, int) and not isinstance(value, bool)
    elif type_lower == 'float':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif type_lower == 'boolean':
        return isinstance(value, bool)
    elif type_lower == 'date' or type_lower == 'timestamp':
        # Check for pandas Timestamp, datetime, or ISO string
        from datetime import datetime
        if isinstance(value, (datetime, pd.Timestamp)):
            return True
        if isinstance(value, str):
            try:
                pd.to_datetime(value)
                return True
            except (ValueError, TypeError):
                return False
        return False
    
    return False


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record (dict) against a schema.
    
    Args:
        record: The data record to validate.
        schema: The schema definition (expected to have a 'fields' key).
        
    Returns:
        List of error messages. Empty if valid.
    """
    errors = []
    fields = schema.get('fields', {})
    required_fields = schema.get('required', [])
    
    for field_name, field_spec in fields.items():
        expected_type = field_spec.get('type', 'any')
        is_required = field_name in required_fields
        
        if field_name not in record:
            if is_required:
                errors.append(f"Missing required field: {field_name}")
            continue
        
        value = record[field_name]
        if not validate_field_type(value, expected_type):
            errors.append(
                f"Type mismatch for field '{field_name}': expected {expected_type}, "
                f"got {type(value).__name__} (value: {value})"
            )
    
    return errors


def validate_parquet_schema(file_path: Union[str, Path], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that a Parquet file's schema matches the provided YAML schema.
    
    Args:
        file_path: Path to the Parquet file.
        schema: The expected schema definition.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")
    
    errors = []
    pf = ParquetFile(file_path)
    arrow_schema = pf.schema_arrow
    
    expected_fields = schema.get('fields', {})
    required_fields = schema.get('required', [])
    
    # Check for required columns
    for field_name in required_fields:
        if field_name not in arrow_schema.names:
            errors.append(f"Missing required column: {field_name}")
    
    # Check types for existing columns defined in schema
    for field_name, field_spec in expected_fields.items():
        if field_name not in arrow_schema.names:
            if field_name in required_fields:
                continue # Already reported above
            continue
        
        expected_type_str = field_spec.get('type', 'any')
        pa_type = arrow_schema.field(field_name).type
        
        # Map PyArrow types to our logical types
        type_mapping = {
            pa.string(): 'string',
            pa.int32(): 'int',
            pa.int64(): 'int',
            pa.float32(): 'float',
            pa.float64(): 'float',
            pa.bool_(): 'boolean',
            pa.date32(): 'date',
            pa.date64(): 'date',
            pa.timestamp('ns'): 'timestamp',
            pa.timestamp('us'): 'timestamp',
            pa.timestamp('ms'): 'timestamp',
            pa.timestamp('s'): 'timestamp',
        }
        
        actual_type_str = None
        for pa_t, log_t in type_mapping.items():
            if pa_type.equals(pa_t):
                actual_type_str = log_t
                break
        
        if actual_type_str is None:
            errors.append(f"Unknown PyArrow type for column {field_name}: {pa_type}")
            continue
        
        if actual_type_str != expected_type_str:
            errors.append(
                f"Type mismatch for column '{field_name}': expected {expected_type_str}, "
                f"got {actual_type_str}"
            )
    
    return (len(errors) == 0, errors)


def validate_csv_schema(file_path: Union[str, Path], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that a CSV file's columns and basic types match the schema.
    
    Args:
        file_path: Path to the CSV file.
        schema: The expected schema definition.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    errors = []
    try:
        df = pd.read_csv(file_path, nrows=100) # Sample first 100 rows for type check
    except Exception as e:
        return False, [f"Failed to read CSV: {str(e)}"]
    
    expected_fields = schema.get('fields', {})
    required_fields = schema.get('required', [])
    
    # Check columns
    for field_name in required_fields:
        if field_name not in df.columns:
            errors.append(f"Missing required column: {field_name}")
    
    # Check types
    for field_name, field_spec in expected_fields.items():
        if field_name not in df.columns:
            if field_name in required_fields:
                continue
            continue
        
        expected_type = field_spec.get('type', 'any')
        series = df[field_name]
        
        # Infer type from sample
        non_null = series.dropna()
        if len(non_null) == 0:
            continue
        
        inferred_type = 'string'
        if pd.api.types.is_integer_dtype(non_null):
            inferred_type = 'int'
        elif pd.api.types.is_float_dtype(non_null):
            inferred_type = 'float'
        elif pd.api.types.is_bool_dtype(non_null):
            inferred_type = 'boolean'
        elif pd.api.types.is_datetime64_any_dtype(non_null):
            inferred_type = 'timestamp'
        
        if expected_type != 'any' and inferred_type != expected_type:
            # Allow int to satisfy float requirement
            if not (expected_type == 'float' and inferred_type == 'int'):
                errors.append(
                    f"Type mismatch for column '{field_name}': expected {expected_type}, "
                    f"inferred {inferred_type}"
                )
    
    return (len(errors) == 0, errors)


def record_checksum(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compute checksum for a file and record it to a JSON file.
    
    Args:
        file_path: Path to the source file.
        output_path: Path to write the checksum record.
        metadata: Optional additional metadata to include.
        
    Returns:
        Dictionary containing the checksum record.
    """
    file_path = Path(file_path)
    output_path = Path(output_path)
    
    checksum = compute_sha256(file_path)
    record = {
        "file_path": str(file_path),
        "checksum": checksum,
        "algorithm": "sha256",
        "file_size_bytes": file_path.stat().st_size,
        "recorded_at": pd.Timestamp.now().isoformat()
    }
    
    if metadata:
        record.update(metadata)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(record, f, indent=2)
    
    return record


def validate_and_checksum(
    data_path: Union[str, Path],
    schema_path: Union[str, Path],
    checksum_output_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Main entry point to validate a file against a schema and optionally record checksum.
    
    Args:
        data_path: Path to the data file (Parquet or CSV).
        schema_path: Path to the YAML schema.
        checksum_output_path: Optional path to write checksum record.
        
    Returns:
        Dictionary with validation status and details.
        
    Raises:
        ValidationError: If validation fails.
    """
    data_path = Path(data_path)
    schema_path = Path(schema_path)
    
    schema = load_schema(schema_path)
    errors = []
    
    if data_path.suffix == '.parquet':
        is_valid, errors = validate_parquet_schema(data_path, schema)
    elif data_path.suffix == '.csv':
        is_valid, errors = validate_csv_schema(data_path, schema)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}. Use .parquet or .csv")
    
    result = {
        "file_path": str(data_path),
        "schema_path": str(schema_path),
        "is_valid": is_valid,
        "errors": errors,
        "validated_at": pd.Timestamp.now().isoformat()
    }
    
    if checksum_output_path:
        checksum_result = record_checksum(data_path, checksum_output_path, {"validated": is_valid})
        result["checksum_record"] = checksum_result
    
    if not is_valid:
        raise ValidationError(f"Validation failed for {data_path}: {errors}")
    
    return result
