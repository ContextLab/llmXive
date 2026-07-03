"""
Configuration loader and validator.
Loads config.yaml and validates against the schema in contracts/simulation_config.schema.yaml
using a manual recursive validator to avoid external jsonschema dependency.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Union

def load_config(config_path: str = None) -> dict:
    """
    Load configuration from YAML file and validate against schema.
    
    Args:
        config_path: Path to config file. Defaults to code/config.yaml
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file not found
        yaml.YAMLError: If YAML is invalid
        ValueError: If configuration fails schema validation
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    else:
        config_path = Path(config_path)
        
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate against schema if schema exists
    schema_path = Path(__file__).parent.parent / "contracts" / "simulation_config.schema.yaml"
    if schema_path.exists():
        _validate_config(config, schema_path)
    
    return config

def _validate_config(config: dict, schema_path: Path) -> None:
    """
    Validate configuration dictionary against the YAML schema file.
    Performs a recursive validation based on the schema definition.
    
    Args:
        config: Configuration dictionary
        schema_path: Path to schema file
        
    Raises:
        ValueError: If validation fails
    """
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    _validate_node(config, schema, "root")

def _validate_node(node: Any, schema: dict, path: str) -> None:
    """
    Recursively validate a node against its schema definition.
    
    Args:
        node: The value to validate
        schema: The schema definition for this node
        path: Current path in the config tree (for error messages)
    """
    node_type = schema.get('type')
    
    # Type checking
    if node_type == 'object':
        if not isinstance(node, dict):
            raise ValueError(f"Validation error at '{path}': expected object, got {type(node).__name__}")
        
        # Check required keys
        required = schema.get('required', [])
        for key in required:
            if key not in node:
                raise ValueError(f"Validation error at '{path}': missing required key '{key}'")
        
        # Validate properties
        properties = schema.get('properties', {})
        for key, value in node.items():
            if key in properties:
                _validate_node(value, properties[key], f"{path}.{key}")
            # Extra keys are allowed unless 'additionalProperties' is False (not implemented for simplicity)
    
    elif node_type == 'array':
        if not isinstance(node, list):
            raise ValueError(f"Validation error at '{path}': expected array, got {type(node).__name__}")
        
        # Check minItems
        min_items = schema.get('minItems')
        if min_items is not None and len(node) < min_items:
            raise ValueError(f"Validation error at '{path}': array length {len(node)} is less than minimum {min_items}")
        
        # Validate items
        items_schema = schema.get('items')
        if items_schema:
            for i, item in enumerate(node):
                _validate_node(item, items_schema, f"{path}[{i}]")
    
    elif node_type == 'integer':
        if not isinstance(node, int) or isinstance(node, bool):
            raise ValueError(f"Validation error at '{path}': expected integer, got {type(node).__name__}")
        
        # Check minimum
        if 'minimum' in schema and node < schema['minimum']:
            raise ValueError(f"Validation error at '{path}': value {node} is less than minimum {schema['minimum']}")
        
        # Check maximum
        if 'maximum' in schema and node > schema['maximum']:
            raise ValueError(f"Validation error at '{path}': value {node} is greater than maximum {schema['maximum']}")
    
    elif node_type == 'number':
        if not isinstance(node, (int, float)) or isinstance(node, bool):
            raise ValueError(f"Validation error at '{path}': expected number, got {type(node).__name__}")
        
        # Check minimum/maximum
        if 'minimum' in schema and node < schema['minimum']:
            raise ValueError(f"Validation error at '{path}': value {node} is less than minimum {schema['minimum']}")
        if 'maximum' in schema and node > schema['maximum']:
            raise ValueError(f"Validation error at '{path}': value {node} is greater than maximum {schema['maximum']}")
        
        # Check exclusive bounds
        if schema.get('exclusiveMinimum') and node <= schema['minimum']:
            raise ValueError(f"Validation error at '{path}': value {node} must be strictly greater than {schema['minimum']}")
        if schema.get('exclusiveMaximum') and node >= schema['maximum']:
            raise ValueError(f"Validation error at '{path}': value {node} must be strictly less than {schema['maximum']}")
    
    elif node_type == 'string':
        if not isinstance(node, str):
            raise ValueError(f"Validation error at '{path}': expected string, got {type(node).__name__}")
        
        # Check enum
        if 'enum' in schema and node not in schema['enum']:
            raise ValueError(f"Validation error at '{path}': value '{node}' not in allowed values {schema['enum']}")