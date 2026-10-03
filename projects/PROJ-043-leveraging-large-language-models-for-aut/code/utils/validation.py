import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import yaml
from pydantic import BaseModel, ValidationError, create_model

logger = logging.getLogger(__name__)

def load_schema_from_yaml(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from a YAML file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def schema_to_pydantic_model(schema: Dict[str, Any]) -> Type[BaseModel]:
    """
    Convert a JSON schema to a Pydantic model.
    Note: This is a simplified converter and may not cover all JSON Schema features.
    """
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    fields = {}
    for prop_name, prop_def in properties.items():
        # Handle nested object definitions (e.g., FunctionSample inside properties)
        if isinstance(prop_def, dict) and prop_def.get('type') == 'object':
            # If it's a nested object definition, we might need to handle it recursively
            # For top-level schema properties that are objects, we treat them as Dict[str, Any]
            # unless they have a specific structure defined in 'properties'
            if 'properties' in prop_def:
                nested_model = schema_to_pydantic_model(prop_def)
                field_type = nested_model
            else:
                field_type = Dict[str, Any]
        else:
            prop_type = prop_def.get('type', 'str')
            if prop_type == 'string':
                field_type = str
            elif prop_type == 'integer':
                field_type = int
            elif prop_type == 'number':
                field_type = float
            elif prop_type == 'boolean':
                field_type = bool
            elif prop_type == 'array':
                field_type = List[Any]
            elif prop_type == 'object':
                field_type = Dict[str, Any]
            else:
                field_type = Any
        
        # Check if required
        if prop_name in required:
            fields[prop_name] = (field_type, ...)
        else:
            fields[prop_name] = (Optional[field_type], None)
    
    return create_model('DynamicSchemaModel', **fields)

def validate_config(config_data: Dict[str, Any], schema_path: str) -> bool:
    """Validate configuration data against a schema."""
    try:
        schema = load_schema_from_yaml(schema_path)
        model = schema_to_pydantic_model(schema)
        model(**config_data)
        logger.info("Configuration validation successful.")
        return True
    except ValidationError as e:
        logger.error(f"Config validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during config validation: {e}")
        raise

def validate_output(output_data: Dict[str, Any], schema_path: str) -> bool:
    """Validate output data against a schema."""
    try:
        schema = load_schema_from_yaml(schema_path)
        model = schema_to_pydantic_model(schema)
        model(**output_data)
        logger.info("Output validation successful.")
        return True
    except ValidationError as e:
        logger.error(f"Output validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during output validation: {e}")
        raise

def validate(data: Dict[str, Any], schema_path: str, data_type: str = "output") -> bool:
    """
    Generic validation wrapper.
    Validates data against a schema.
    
    Args:
        data: The data to validate.
        schema_path: Path to the YAML schema file.
        data_type: 'config' or 'output' (for logging purposes).
    
    Returns:
        True if validation succeeds.
    
    Raises:
        ValidationError: If validation fails.
        FileNotFoundError: If schema file is missing.
    """
    if data_type == "config":
        return validate_config(data, schema_path)
    else:
        return validate_output(data, schema_path)
