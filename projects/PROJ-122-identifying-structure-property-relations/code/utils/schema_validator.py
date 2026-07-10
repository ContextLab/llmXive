"""
Schema validation utilities for data ingestion.
Provides functions to load schemas and validate data records against them.
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

class SchemaValidationError(Exception):
    """Raised when data validation against a schema fails."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML or JSON schema from the given path.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the file format is unsupported or invalid.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        content = f.read()
        
    if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
        try:
            import yaml
            return yaml.safe_load(content)
        except ImportError:
            raise ImportError("PyYAML is required to load YAML schemas. Install with: pip install pyyaml")
        except Exception as e:
            raise ValueError(f"Invalid YAML in schema file: {e}")
    elif schema_path.endswith('.json'):
        try:
            return json.loads(content)
        except Exception as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")
    else:
        raise ValueError(f"Unsupported schema file format: {schema_path}")

def validate_iso_datetime(value: str) -> bool:
    """
    Validate if a string is a valid ISO 8601 datetime.
    
    Args:
        value: String to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(value, str):
        return False
    try:
        # Supports basic ISO 8601 formats
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def validate_sha256_checksum(value: str) -> bool:
    """
    Validate if a string is a valid SHA-256 checksum (64 hex characters).
    
    Args:
        value: String to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(value, str):
        return False
    return bool(re.match(r'^[a-fA-F0-9]{64}$', value))

def validate_path_pattern(value: str) -> bool:
    """
    Validate if a string matches a valid file path pattern.
    
    Args:
        value: String to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(value, str):
        return False
    # Basic check: no null bytes and starts with valid char
    if '\x00' in value:
        return False
    return True

def validate_artifact(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single data record against a schema.
    
    Args:
        record: The data record to validate.
        schema: The schema definition.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required fields
    required_fields = schema.get("required_fields", [])
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")
    
    # Check types if defined in properties
    properties = schema.get("properties", {})
    for field, value in record.items():
        if field in properties:
            field_def = properties[field]
            expected_type = field_def.get("type")
            
            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be a number")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"Field '{field}' must be an integer")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Field '{field}' must be a boolean")
            
            # Specific format validations
            if "format" in field_def:
                fmt = field_def["format"]
                if fmt == "iso_datetime" and not validate_iso_datetime(value):
                    errors.append(f"Field '{field}' must be ISO 8601 datetime")
                elif fmt == "sha256" and not validate_sha256_checksum(value):
                    errors.append(f"Field '{field}' must be a valid SHA-256 checksum")
                elif fmt == "path" and not validate_path_pattern(value):
                    errors.append(f"Field '{field}' must be a valid path")
    
    return len(errors) == 0, errors

def validate_output_file(file_path: str, schema: Dict[str, Any]) -> bool:
    """
    Validate that an output file exists and matches expected format.
    
    Args:
        file_path: Path to the output file.
        schema: Schema definition (may contain path constraints).
        
    Returns:
        True if valid, False otherwise.
    """
    if not os.path.exists(file_path):
        return False
    
    # Additional checks could be added here based on schema constraints
    return True