"""
Schema validators and loaders for project data artifacts.

Implements validation for AtomicGraph, ThermalSample, and GNNOutput
using JSON Schema against files in the contracts/ directory.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

try:
    import jsonschema
except ImportError:
    raise ImportError(
        "The 'jsonschema' package is required for validation. "
        "Install it via: pip install jsonschema"
    )

logger = logging.getLogger(__name__)

# Paths to schema files relative to project root
SCHEMAS = {
    "atomic_graph": Path("contracts/atomic_graph.schema.yaml"),
    "thermal_sample": Path("contracts/thermal_sample.schema.yaml"),
    "gnn_output": Path("contracts/gnn_output.schema.yaml"),
}

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the contracts directory.
    
    Args:
        schema_name: One of 'atomic_graph', 'thermal_sample', 'gnn_output'.
        
    Returns:
        The schema dictionary.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        KeyError: If the schema_name is not recognized.
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    if schema_name not in SCHEMAS:
        raise KeyError(f"Unknown schema name: {schema_name}. Valid: {list(SCHEMAS.keys())}")
    
    schema_path = SCHEMAS[schema_name]
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_data(data: Dict[str, Any], schema_name: str) -> bool:
    """
    Validate data against a named schema.
    
    Args:
        data: The data dictionary to validate.
        schema_name: The name of the schema to validate against.
        
    Returns:
        True if valid.
        
    Raises:
        jsonschema.exceptions.ValidationError: If validation fails.
        KeyError: If schema_name is unknown.
    """
    schema = load_schema(schema_name)
    jsonschema.validate(instance=data, schema=schema)
    return True

def load_and_validate(data_path: Path, schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON/YAML file and validate it against a schema.
    
    Args:
        data_path: Path to the data file.
        schema_name: Name of the schema to validate against.
        
    Returns:
        The loaded data dictionary.
        
    Raises:
        FileNotFoundError: If data file missing.
        json.JSONDecodeError / yaml.YAMLError: If file parsing fails.
        jsonschema.exceptions.ValidationError: If validation fails.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        if data_path.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        else:
            data = json.load(f)
    
    validate_data(data, schema_name)
    logger.info(f"Successfully validated {data_path} against {schema_name}")
    return data

def main():
    """Run basic schema loading tests."""
    logger.info("Running schema validator self-test...")
    for name in SCHEMAS.keys():
        try:
            schema = load_schema(name)
            logger.info(f"Loaded schema '{name}': {list(schema.keys())}")
        except Exception as e:
            logger.error(f"Failed to load schema '{name}': {e}")
            raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()