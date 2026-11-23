"""
Schema validation utilities for project artifacts.

This module provides functions to validate data artifacts against
the JSON schemas defined in the contracts/ directory.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    raise ImportError(
        "jsonschema is required for schema validation. "
        "Add 'jsonschema' to requirements.txt and run pip install."
    )

from utils.logging import get_logger

logger = get_logger(__name__)

# Base path for schema files
SCHEMAS_DIR = Path(__file__).parent.parent.parent / "contracts"

# Cache for loaded schemas
_schema_cache: Dict[str, Draft7Validator] = {}

def load_schema(schema_name: str) -> Draft7Validator:
    """
    Load a JSON schema from the contracts directory.
    
    Args:
        schema_name: Name of the schema file (e.g., 'diffusion_results.schema.yaml')
        
    Returns:
        Compiled JSONSchema validator object
        
    Raises:
        FileNotFoundError: If the schema file doesn't exist
        jsonschema.SchemaError: If the schema is invalid
    """
    if schema_name in _schema_cache:
        return _schema_cache[schema_name]
    
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema_content = yaml.safe_load(f)
    
    validator = Draft7Validator(schema_content)
    _schema_cache[schema_name] = validator
    logger.debug(f"Loaded schema: {schema_name}")
    return validator

def validate_artifact(data: Dict[str, Any], schema_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a data artifact against a JSON schema.
    
    Args:
        data: The data dictionary to validate
        schema_name: Name of the schema file to use
        
    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if validation passes, False otherwise
        error_message: Error description if validation fails, None otherwise
    """
    try:
        validator = load_schema(schema_name)
        errors = list(validator.iter_errors(data))
        
        if errors:
            error_messages = [
                f"{' -> '.join(str(p) for p in e.path)}: {e.message}"
                for e in errors
            ]
            return False, "; ".join(error_messages)
        
        return True, None
        
    except FileNotFoundError as e:
        return False, f"Schema loading error: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_file(file_path: Path, schema_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a JSON/YAML file against a JSON schema.
    
    Args:
        file_path: Path to the file to validate
        schema_name: Name of the schema file to use
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    # Determine file type and load
    try:
        with open(file_path, 'r') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                import yaml
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
    except Exception as e:
        return False, f"Failed to load file: {str(e)}"
    
    return validate_artifact(data, schema_name)

def validate_batch(file_paths: List[Tuple[Path, str]]) -> Dict[str, Tuple[bool, Optional[str]]]:
    """
    Validate multiple files against their respective schemas.
    
    Args:
        file_paths: List of (file_path, schema_name) tuples
        
    Returns:
        Dictionary mapping file paths to (is_valid, error_message) tuples
    """
    results = {}
    for file_path, schema_name in file_paths:
        results[str(file_path)] = validate_file(file_path, schema_name)
    return results

# Lazy import yaml to avoid hard dependency if not needed
def _get_yaml():
    import yaml
    return yaml
yaml = _get_yaml()