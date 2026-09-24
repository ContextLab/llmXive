import json
import csv
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

class SecurityError(Exception):
    """Base exception for security errors."""
    pass

class PathTraversalError(SecurityError):
    """Exception raised for path traversal attempts."""
    pass

class SchemaValidationError(SecurityError):
    """Exception raised for schema validation errors."""
    pass

def sanitize_path(path: str, base_dir: str) -> str:
    """
    Sanitize a path to prevent directory traversal attacks.
    
    Args:
        path: The path to sanitize.
        base_dir: The base directory to restrict access to.
        
    Returns:
        The sanitized absolute path.
        
    Raises:
        PathTraversalError: If the path attempts to traverse outside base_dir.
    """
    base = Path(base_dir).resolve()
    target = Path(path).resolve()
    
    if not str(target).startswith(str(base)):
        raise PathTraversalError(f"Path traversal attempt detected: {path}")
    
    return str(target)

def safe_load_json(path: str, base_dir: str = ".") -> Dict[str, Any]:
    """
    Safely load a JSON file.
    
    Args:
        path: Path to the JSON file.
        base_dir: Base directory to restrict access to.
        
    Returns:
        Parsed JSON data.
        
    Raises:
        SecurityError: If the file cannot be loaded safely.
    """
    safe_path = sanitize_path(path, base_dir)
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise SecurityError(f"Failed to load JSON: {e}")

def safe_load_csv(path: str, base_dir: str = ".") -> List[Dict[str, Any]]:
    """
    Safely load a CSV file.
    
    Args:
        path: Path to the CSV file.
        base_dir: Base directory to restrict access to.
        
    Returns:
        List of dictionaries representing rows.
        
    Raises:
        SecurityError: If the file cannot be loaded safely.
    """
    safe_path = sanitize_path(path, base_dir)
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        raise SecurityError(f"Failed to load CSV: {e}")

def safe_load_yaml(path: str, base_dir: str = ".") -> Dict[str, Any]:
    """
    Safely load a YAML file.
    
    Args:
        path: Path to the YAML file.
        base_dir: Base directory to restrict access to.
        
    Returns:
        Parsed YAML data.
        
    Raises:
        SecurityError: If the file cannot be loaded safely.
    """
    try:
        import yaml
    except ImportError:
        raise SecurityError("PyYAML is not installed")
    
    safe_path = sanitize_path(path, base_dir)
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise SecurityError(f"Failed to load YAML: {e}")

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate data against a schema.
    
    Args:
        data: The data to validate.
        schema: The schema definition.
        
    Raises:
        SchemaValidationError: If validation fails.
    """
    for key, expected_type in schema.items():
        if key not in data:
            raise SchemaValidationError(f"Missing required key: {key}")
        if not isinstance(data[key], expected_type):
            raise SchemaValidationError(f"Invalid type for {key}: expected {expected_type}, got {type(data[key])}")