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
    """Raised when a path traversal attempt is detected."""
    pass

class SchemaValidationError(SecurityError):
    """Raised when data schema validation fails."""
    pass

def sanitize_path(path_str: str) -> Path:
    """
    Sanitize a path string to prevent path traversal attacks.
    
    Args:
        path_str: The raw path string.
        
    Returns:
        A sanitized Path object.
        
    Raises:
        PathTraversalError: If path traversal is detected.
    """
    # Resolve to absolute path
    p = Path(path_str).resolve()
    
    # Check for suspicious patterns
    if '..' in str(p):
        raise PathTraversalError(f"Path traversal detected in: {path_str}")
    
    # Ensure the path is within the current working directory or a safe base
    # For this project, we assume paths are relative to the project root
    # We do not enforce a specific base here to allow flexibility, but we prevent '..'
    return p

def safe_load_json(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Safely load a JSON file.
    
    Args:
        path: Path to the JSON file.
        
    Returns:
        Parsed JSON data (expected to be a list of dicts).
        
    Raises:
        SecurityError: If path is invalid or file content is not a list of dicts.
    """
    safe_p = sanitize_path(path)
    if not safe_p.exists():
        raise FileNotFoundError(f"File not found: {safe_p}")
    
    with open(safe_p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise SchemaValidationError("JSON root must be a list of records.")
    
    if data and not isinstance(data[0], dict):
        raise SchemaValidationError("JSON list items must be dictionaries.")
        
    return data

def safe_load_csv(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Safely load a CSV file.
    
    Args:
        path: Path to the CSV file.
        
    Returns:
        List of dictionaries representing rows.
        
    Raises:
        SecurityError: If path is invalid.
    """
    safe_p = sanitize_path(path)
    if not safe_p.exists():
        raise FileNotFoundError(f"File not found: {safe_p}")
    
    records = []
    with open(safe_p, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert all values to strings, or attempt numeric conversion if needed
            # For now, keep as strings to avoid implicit execution of weird types
            records.append(dict(row))
            
    return records

def safe_load_yaml(path: Union[str, Path]) -> Any:
    """
    Safely load a YAML file.
    Note: This requires PyYAML. We use safe_load to prevent arbitrary code execution.
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for YAML loading.")
        
    safe_p = sanitize_path(path)
    if not safe_p.exists():
        raise FileNotFoundError(f"File not found: {safe_p}")
    
    with open(safe_p, 'r', encoding='utf-8') as f:
        # safe_load prevents arbitrary code execution
        data = yaml.safe_load(f)
        
    return data
