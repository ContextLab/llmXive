"""
Schema loading utilities for the ecotourism regeneration pipeline.

Provides functions to load YAML schema definitions from the contracts directory
and convert them into Pydantic models for runtime validation.
"""
import os
import yaml
from typing import Optional, Any, Dict, Type
from datetime import date
from pydantic import BaseModel, create_model, Field
from pathlib import Path

# Define the base directory for contracts
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "specs" / "001-ecotourism-regeneration" / "contracts"

def load_schema_to_pydantic(schema_name: str, schema_file: Path) -> Type[BaseModel]:
    """
    Load a YAML schema definition and convert it into a Pydantic model.
    
    Args:
        schema_name: The name of the model to create (e.g., 'FinalReport').
        schema_file: Path to the YAML file containing the schema definition.
        
    Returns:
        A Pydantic model class.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the schema definition is invalid.
    """
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    with open(schema_file, 'r') as f:
        schema_def = yaml.safe_load(f)
    
    if schema_name not in schema_def:
        raise ValueError(f"Model '{schema_name}' not found in {schema_file}")
    
    model_config = schema_def[schema_name]
    
    # Helper to map YAML types to Python types
    def get_python_type(type_str: str, format_str: Optional[str] = None) -> Any:
        if type_str == 'string':
            if format_str == 'date-time':
                return str # Pydantic handles ISO format automatically
            return str
        elif type_str == 'number':
            return float
        elif type_str == 'integer':
            return int
        elif type_str == 'boolean':
            return bool
        elif type_str == 'array':
            return list
        elif type_str == 'object':
            return dict
        else:
            return Any # Fallback for unknown types
    
    # Recursive function to build field definitions
    def build_fields(config: Dict[str, Any]) -> Dict[str, tuple]:
        fields = {}
        if 'properties' not in config:
            return fields
        
        for prop_name, prop_config in config['properties'].items():
            prop_type = get_python_type(prop_config.get('type', 'any'))
            
            # Handle nested objects recursively
            if prop_config.get('type') == 'object' and 'properties' in prop_config:
                # For nested objects, we create a dynamic model or just use dict for simplicity
                # depending on strictness requirements. Here we use dict for nested structures
                # unless a specific nested model is defined in the same file.
                fields[prop_name] = (prop_type, ...) if prop_name in config.get('required', []) else (Optional[prop_type], None)
            elif prop_config.get('type') == 'array':
                fields[prop_name] = (prop_type, ...) if prop_name in config.get('required', []) else (Optional[prop_type], None)
            else:
                # Simple fields
                fields[prop_name] = (prop_type, ...) if prop_name in config.get('required', []) else (Optional[prop_type], None)
                
                # Add description if available
                if 'description' in prop_config:
                    # We can't easily set description in create_model fields without a custom Field,
                    # but we can store it if needed. For now, basic creation.
                    pass
        
        return fields
    
    # Build the top-level fields
    fields = build_fields(model_config)
    
    # Create the model
    try:
        model = create_model(schema_name, **fields)
        return model
    except Exception as e:
        raise ValueError(f"Failed to create model {schema_name}: {e}")

def get_site_schema() -> Type[BaseModel]:
    """Load the Site schema from site.schema.yaml."""
    return load_schema_to_pydantic("Site", CONTRACTS_DIR / "site.schema.yaml")

def get_timeseries_schema() -> Type[BaseModel]:
    """Load the TimeSeries schema from timeseries.schema.yaml."""
    return load_schema_to_pydantic("TimeSeries", CONTRACTS_DIR / "timeseries.schema.yaml")

def get_output_schema() -> Dict[str, Type[BaseModel]]:
    """
    Load both FinalReport and SensitivityArtifact schemas from output.schema.yaml.
    
    Returns:
        A dictionary mapping schema names to their Pydantic model classes.
    """
    schema_file = CONTRACTS_DIR / "output.schema.yaml"
    return {
        "FinalReport": load_schema_to_pydantic("FinalReport", schema_file),
        "SensitivityArtifact": load_schema_to_pydantic("SensitivityArtifact", schema_file)
    }
