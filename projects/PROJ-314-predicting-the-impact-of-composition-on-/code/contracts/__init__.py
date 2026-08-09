"""
Contract schemas and validation utilities for the llmXive science pipeline.

This module provides JSON Schema definitions for data validation
and functions to load/validate data against these schemas.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import jsonschema
from jsonschema.exceptions import ValidationError

SCHEMAS_DIR = Path(__file__).parent

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON/YAML schema from the contracts directory.
    
    Args:
        schema_name: Name of the schema file (e.g., 'ceramic_entry.schema.yaml')
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is invalid YAML/JSON.
    """
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
        
    with open(schema_path, 'r') as f:
        if schema_path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif schema_path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {schema_path.suffix}")
            
def validate_data_against_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """
    Validate a data record against a specific schema.
    
    Args:
        data: The data record to validate.
        schema_name: Name of the schema file to validate against.
        
    Returns:
        True if valid.
        
    Raises:
        ValidationError: If data does not conform to the schema.
        FileNotFoundError: If schema not found.
    """
    schema = load_schema(schema_name)
    jsonschema.validate(instance=data, schema=schema)
    return True
    
def validate_schemas() -> Dict[str, bool]:
    """
    Validate all schema files in the contracts directory for syntax errors.
    
    Returns:
        Dictionary mapping schema names to validation status (True = valid).
    """
    results = {}
    for schema_file in SCHEMAS_DIR.glob('*.schema.yaml'):
        try:
            load_schema(schema_file.name)
            results[schema_file.name] = True
        except Exception as e:
            results[schema_file.name] = False
            # Log error if logger is available
            try:
                from code import logger
                logger.error(f"Schema validation failed for {schema_file.name}: {e}")
            except ImportError:
                pass
    return results