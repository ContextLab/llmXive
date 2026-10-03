"""
Data validation utilities for schema validation and checksum recording.

Provides functions for:
- Loading and validating YAML schemas
- Validating field types and records
- Validating Parquet and CSV files against schemas
- Computing SHA256 checksums
- Recording checksums for data integrity verification
"""
import os
import json
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass

def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of SHA256 hash
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return sha256_hash.hexdigest()
        
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML schema definition.
    
    Args:
        schema_path: Path to the YAML schema file
        
    Returns:
        Schema dictionary
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        yaml.YAMLError: If schema is invalid YAML
        ValidationError: If schema is missing required fields
    """
    schema_path = Path(schema_path)
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
            
        if not isinstance(schema, dict):
            raise ValidationError("Schema must be a YAML dictionary")
            
        if 'fields' not in schema:
            raise ValidationError("Schema must contain 'fields' key")
            
        return schema
        
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML in schema file: {e}")

def validate_field_type(value: Any, field_type: str) -> bool:
    """
    Validate that a value matches the expected field type.
    
    Args:
        value: Value to validate
        field_type: Expected type as string (e.g., 'string', 'integer', 'float', 'boolean', 'datetime')
        
    Returns:
        True if valid, False otherwise
    """
    type_mapping = {
        'string': (str, type(None)),
        'integer': (int, np.integer, type(None)),
        'float': (float, np.floating, type(None)),
        'boolean': (bool, np.bool_, type(None)),
        'datetime': (str, type(None)),  # Assuming datetime stored as string or ISO format
        'object': (dict, type(None)),
        'array': (list, type(None)),
    }
    
    expected_types = type_mapping.get(field_type.lower())
    
    if expected_types is None:
        logger.warning(f"Unknown field type: {field_type}, assuming any type is valid")
        return True
        
    if value is None:
        # Allow None for all types (can be extended to require non-null)
        return True
        
    return isinstance(value, expected_types)

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against a schema.
    
    Args:
        record: Dictionary representing a single record
        schema: Schema dictionary with 'fields' key
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    fields = schema.get('fields', {})
    
    # Check required fields
    for field_name, field_def in fields.items():
        if field_name not in record:
            if field_def.get('required', False):
                errors.append(f"Missing required field: {field_name}")
            continue
            
        # Validate field type
        value = record[field_name]
        field_type = field_def.get('type', 'string')
        
        if not validate_field_type(value, field_type):
            errors.append(
                f"Field '{field_name}' has invalid type. "
                f"Expected: {field_type}, Got: {type(value).__name__}"
            )
            
        # Validate constraints if present
        if 'min' in field_def and value is not None:
            if value < field_def['min']:
                errors.append(
                    f"Field '{field_name}' value {value} is below minimum {field_def['min']}"
                )
                
        if 'max' in field_def and value is not None:
            if value > field_def['max']:
                errors.append(
                    f"Field '{field_name}' value {value} is above maximum {field_def['max']}"
                )
                
        if 'pattern' in field_def and value is not None:
            import re
            pattern = field_def['pattern']
            if not re.match(pattern, str(value)):
                errors.append(
                    f"Field '{field_name}' value '{value}' does not match pattern '{pattern}'"
                )
                
    return errors

def validate_parquet_schema(
    df: pd.DataFrame,
    schema: Dict[str, Any],
    strict: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validate a Parquet DataFrame against a schema.
    
    Args:
        df: Pandas DataFrame to validate
        schema: Schema dictionary with 'fields' key
        strict: If True, fail on extra columns not in schema
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    fields = schema.get('fields', {})
    
    # Check for missing required columns
    for field_name, field_def in fields.items():
        if field_name not in df.columns:
            if field_def.get('required', False):
                errors.append(f"Missing required column: {field_name}")
                
    # Check for extra columns if strict mode
    if strict:
        extra_cols = set(df.columns) - set(fields.keys())
        if extra_cols:
            errors.append(f"Extra columns not in schema: {extra_cols}")
            
    # Validate each row
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_errors = validate_record(row_dict, schema)
        
        if row_errors:
            errors.append(f"Row {idx}: {'; '.join(row_errors)}")
            
    is_valid = len(errors) == 0
    return is_valid, errors

def validate_csv_schema(
    df: pd.DataFrame,
    schema: Dict[str, Any],
    strict: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validate a CSV DataFrame against a schema.
    
    Args:
        df: Pandas DataFrame to validate
        schema: Schema dictionary with 'fields' key
        strict: If True, fail on extra columns not in schema
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    return validate_parquet_schema(df, schema, strict)

def record_checksum(
    file_path: Union[str, Path],
    checksum_path: Union[str, Path],
    algorithm: str = 'sha256'
) -> str:
    """
    Compute and record a checksum for a file.
    
    Args:
        file_path: Path to the file to checksum
        checksum_path: Path to write the checksum file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        The computed checksum
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If checksum file cannot be written
    """
    file_path = Path(file_path)
    checksum_path = Path(checksum_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    # Compute checksum
    if algorithm.lower() == 'sha256':
        checksum = compute_sha256(file_path)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
        
    # Ensure checksum directory exists
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write checksum file
    try:
        with open(checksum_path, 'w') as f:
            f.write(f"{checksum}  {file_path.name}\n")
            f.write(f"algorithm: {algorithm}\n")
            f.write(f"file_size: {file_path.stat().st_size}\n")
            f.write(f"timestamp: {pd.Timestamp.now().isoformat()}\n")
            
        logger.info(f"Checksum recorded for {file_path.name} at {checksum_path}")
        
    except IOError as e:
        raise IOError(f"Failed to write checksum file {checksum_path}: {e}")
        
    return checksum

def validate_and_checksum(
    file_path: Union[str, Path],
    schema_path: Optional[Union[str, Path]] = None,
    checksum_path: Optional[Union[str, Path]] = None,
    file_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate a file against a schema and record its checksum.
    
    Args:
        file_path: Path to the file to validate
        schema_path: Optional path to schema file
        checksum_path: Optional path to write checksum file
        file_type: Optional file type hint ('parquet', 'csv', 'json')
        
    Returns:
        Dictionary with validation results and checksum info
        
    Raises:
        ValidationError: If validation fails
        FileNotFoundError: If files don't exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    result = {
        'file_path': str(file_path),
        'file_exists': True,
        'file_size': file_path.stat().st_size,
        'validation_errors': [],
        'is_valid': True,
        'checksum': None,
        'checksum_path': None
    }
    
    # Compute checksum if requested
    if checksum_path:
        try:
            result['checksum'] = record_checksum(file_path, checksum_path)
            result['checksum_path'] = str(checksum_path)
        except Exception as e:
            logger.warning(f"Failed to record checksum: {e}")
            
    # Validate against schema if provided
    if schema_path:
        try:
            schema = load_schema(schema_path)
            
            # Determine file type if not provided
            if file_type is None:
                suffix = file_path.suffix.lower()
                if suffix == '.parquet':
                    file_type = 'parquet'
                elif suffix == '.csv':
                    file_type = 'csv'
                elif suffix == '.json':
                    file_type = 'json'
                else:
                    file_type = 'unknown'
                    
            # Load and validate data
            if file_type == 'parquet':
                df = pd.read_parquet(file_path)
                is_valid, errors = validate_parquet_schema(df, schema)
            elif file_type == 'csv':
                df = pd.read_csv(file_path)
                is_valid, errors = validate_csv_schema(df, schema)
            else:
                logger.warning(f"Unsupported file type for validation: {file_type}")
                is_valid = True
                errors = []
                
            result['is_valid'] = is_valid
            result['validation_errors'] = errors
            
            if not is_valid:
                raise ValidationError(f"Validation failed: {'; '.join(errors)}")
                
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            result['validation_errors'].append(str(e))
            result['is_valid'] = False
            raise ValidationError(f"Schema validation failed: {e}")
            
    return result
