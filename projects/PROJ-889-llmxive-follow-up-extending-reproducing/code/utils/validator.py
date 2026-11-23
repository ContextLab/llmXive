import json
import sys
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from code.config import get_project_root
from code.utils.io_utils import read_yaml

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the contracts directory.
    
    Args:
        schema_name: Name of the schema file (e.g., 'trajectory.schema.yaml', 'metrics.schema.yaml')
        
    Returns:
        The loaded schema as a dictionary.
    """
    project_root = get_project_root()
    schema_path = project_root / "contracts" / schema_name
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    # Load YAML schema
    schema = read_yaml(schema_path)
    return schema

def validate_trajectory_data(data: List[Dict[str, Any]]) -> bool:
    """
    Validate trajectory data against the trajectory schema.
    
    Args:
        data: List of trajectory records.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    schema = load_schema("trajectory.schema.yaml")
    return validate_file_against_schema(data, schema, "trajectory")

def validate_metrics_data(data: List[Dict[str, Any]]) -> bool:
    """
    Validate metrics data against the metrics schema.
    
    Args:
        data: List of metrics records.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    schema = load_schema("metrics.schema.yaml")
    return validate_file_against_schema(data, schema, "metrics")

def validate_file_against_schema(data: List[Dict[str, Any]], schema: Dict[str, Any], data_type: str) -> bool:
    """
    Validate data against a JSON schema.
    
    Args:
        data: The data to validate.
        schema: The JSON schema to validate against.
        data_type: Type name for error messages.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError: If validation fails.
    """
    try:
        import jsonschema
    except ImportError:
        raise ImportError("jsonschema package is required for validation. Install with: pip install jsonschema")
    
    # If data is a list, validate each item
    if isinstance(data, list):
        for i, item in enumerate(data):
            try:
                jsonschema.validate(instance=item, schema=schema)
            except jsonschema.exceptions.ValidationError as e:
                raise ValueError(f"Validation failed for {data_type} item {i}: {e.message}")
    else:
        # Single item
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(f"Validation failed for {data_type}: {e.message}")
    
    return True

def validate_cherrl_source(url: str) -> bool:
    """
    Validate that the CHERRL source URL is accessible and matches expected patterns.
    
    Args:
        url: The URL to validate.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError: If validation fails.
    """
    # Check if URL matches expected pattern (HuggingFace or arXiv)
    allowed_patterns = [
        r"https://huggingface\.co/.*",
        r"https://arxiv\.org/.*"
    ]
    
    is_valid_pattern = any(re.match(pattern, url) for pattern in allowed_patterns)
    if not is_valid_pattern:
        raise ValueError(f"Invalid CHERRL source URL pattern: {url}")
    
    # Check if URL is accessible
    try:
        response = requests.head(url, timeout=10)
        if response.status_code != 200:
            raise ValueError(f"CHERRL source URL returned status {response.status_code}: {url}")
    except requests.RequestException as e:
        raise ValueError(f"Failed to access CHERRL source URL: {e}")
    
    return True