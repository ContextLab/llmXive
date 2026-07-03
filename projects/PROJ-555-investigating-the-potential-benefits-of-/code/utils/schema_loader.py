import os
import yaml
from typing import Optional, Any, Dict, Type
from datetime import date
from pydantic import BaseModel, create_model, Field
from pathlib import Path

# Import existing schemas if they exist (T006a, T006b)
# We assume they are defined in the same module or imported from elsewhere
# For this task, we focus on the output schema which is the new requirement.

def load_schema_to_pydantic(schema_path: str) -> Type[BaseModel]:
    """
    Load a YAML schema definition and convert it to a Pydantic model.
    
    Args:
        schema_path: Path to the YAML schema file
        
    Returns:
        A Pydantic model class
    """
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # This is a simplified loader that handles basic nested structures.
    # For complex recursive schemas, a more robust parser would be needed.
    # For this project, we assume the schemas are relatively flat or have known structures.
    
    def build_model(name: str, props: Dict[str, Any], required: Optional[list] = None) -> Type[BaseModel]:
        fields = {}
        req_set = set(required) if required else set()
        
        for prop_name, prop_def in props.items():
            field_type = Any
            field_info = {}
            
            if 'type' in prop_def:
                ptype = prop_def['type']
                if ptype == 'string':
                    if prop_def.get('format') == 'date-time':
                        field_type = str # Pydantic handles ISO strings
                    elif prop_def.get('format') == 'date':
                        field_type = str # Pydantic handles date strings
                    else:
                        field_type = str
                elif ptype == 'number':
                    field_type = float
                elif ptype == 'integer':
                    field_type = int
                elif ptype == 'boolean':
                    field_type = bool
                elif ptype == 'object':
                    # Recursively build nested model
                    nested_name = f"{name}_{prop_name.title()}"
                    if 'properties' in prop_def:
                        field_type = build_model(nested_name, prop_def['properties'], prop_def.get('required'))
                    else:
                        field_type = Dict[str, Any]
                elif ptype == 'array':
                    if 'items' in prop_def:
                        items = prop_def['items']
                        if items.get('type') == 'object' and 'properties' in items:
                            nested_name = f"{name}_{prop_name.title()}Item"
                            field_type = list[build_model(nested_name, items['properties'], items.get('required'))]
                        elif items.get('type') == 'string':
                            field_type = list[str]
                        elif items.get('type') == 'number':
                            field_type = list[float]
                        elif items.get('type') == 'integer':
                            field_type = list[int]
                        else:
                            field_type = list[Any]
                    else:
                        field_type = list[Any]
                else:
                    field_type = Any
            
            # Handle nullable
            if prop_def.get('nullable', False):
                from typing import Union
                field_type = Union[field_type, None]
            
            # Handle const
            if 'const' in prop_def:
                field_type = type(prop_def['const'])
                field_info['const'] = prop_def['const']
            
            # Handle enum
            if 'enum' in prop_def:
                from enum import Enum
                enum_name = f"{name}_{prop_name.title()}Enum"
                # Create a dynamic Enum if needed, but for simplicity we often just use str/int
                # Pydantic will validate against the enum values if we pass them as a Literal
                # For now, we'll just let it be the base type and rely on validation later if needed.
                pass
            
            # Handle default
            if 'default' in prop_def:
                field_info['default'] = prop_def['default']
            else:
                field_info['default'] = ... # Required field
            
            # Description
            if 'description' in prop_def:
                field_info['description'] = prop_def['description']
            
            # Min/Max constraints
            if 'minimum' in prop_def:
                field_info['ge'] = prop_def['minimum']
            if 'maximum' in prop_def:
                field_info['le'] = prop_def['maximum']
            if 'minLength' in prop_def:
                field_info['min_length'] = prop_def['minLength']
            if 'maxLength' in prop_def:
                field_info['max_length'] = prop_def['maxLength']
            
            fields[prop_name] = (field_type, Field(**field_info))
        
        return create_model(name, **fields)
    
    return build_model(schema.get('title', 'DynamicModel'), schema['properties'], schema.get('required'))

def get_site_schema() -> Type[BaseModel]:
    """
    Load and return the Site schema.
    Assumes the file exists at the expected path.
    """
    schema_path = Path(__file__).parent.parent.parent / "specs" / "001-ecotourism-regeneration" / "contracts" / "site.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Site schema not found at {schema_path}")
    return load_schema_to_pydantic(str(schema_path))

def get_timeseries_schema() -> Type[BaseModel]:
    """
    Load and return the Timeseries schema.
    Assumes the file exists at the expected path.
    """
    schema_path = Path(__file__).parent.parent.parent / "specs" / "001-ecotourism-regeneration" / "contracts" / "timeseries.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Timeseries schema not found at {schema_path}")
    return load_schema_to_pydantic(str(schema_path))

def get_output_schema() -> Type[BaseModel]:
    """
    Load and return the Output schema defined in output.schema.yaml.
    This schema defines the structure of the final analysis outputs.
    """
    schema_path = Path(__file__).parent.parent.parent / "specs" / "001-ecotourism-regeneration" / "contracts" / "output.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Output schema not found at {schema_path}")
    return load_schema_to_pydantic(str(schema_path))
