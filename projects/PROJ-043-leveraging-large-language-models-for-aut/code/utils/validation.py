import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import yaml
from pydantic import BaseModel, ValidationError, create_model

logger = logging.getLogger(__name__)

def load_schema_from_yaml(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from a YAML file."""
    with open(schema_path, 'r') as f:
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
        return True
    except ValidationError as e:
        logger.error(f"Config validation failed: {e}")
        return False

def validate_output(output_data: Dict[str, Any], schema_path: str) -> bool:
    """Validate output data against a schema."""
    try:
        schema = load_schema_from_yaml(schema_path)
        model = schema_to_pydantic_model(schema)
        model(**output_data)
        return True
    except ValidationError as e:
        logger.error(f"Output validation failed: {e}")
        return False