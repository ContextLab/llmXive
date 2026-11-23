"""
Schema Loader Utility
Converts YAML schema definitions into Pydantic models dynamically.
"""
import os
import yaml
from typing import Optional, Any, Dict, Type, get_type_hints
from datetime import date
from pathlib import Path
from pydantic import BaseModel, create_model, Field
import logging

logger = logging.getLogger(__name__)

# Base directory for contracts
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "specs" / "001-ecotourism-regeneration" / "contracts"

def load_schema_to_pydantic(schema_name: str, schema_path: Optional[Path] = None) -> Type[BaseModel]:
    """
    Loads a YAML schema definition and creates a corresponding Pydantic model.

    Args:
        schema_name: The key name in the YAML file (e.g., 'FinalReport').
        schema_path: Optional path to the YAML file. Defaults to output.schema.yaml.

    Returns:
        A Pydantic model class.
    """
    if schema_path is None:
        schema_path = CONTRACTS_DIR / "output.schema.yaml"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r') as f:
        schema_data = yaml.safe_load(f)

    if schema_name not in schema_data:
        raise KeyError(f"Schema definition '{schema_name}' not found in {schema_path}")

    definition = schema_data[schema_name]
    fields = definition.get('fields', {})

    # Build field definitions for create_model
    pydantic_fields = {}

    for field_name, field_spec in fields.items():
        field_type = field_spec.get('type', 'Any')
        description = field_spec.get('description', '')
        example = field_spec.get('example', None)

        # Map YAML types to Python types
        type_mapping = {
            'string': str,
            'str': str,
            'float': float,
            'int': int,
            'bool': bool,
            'dict': dict,
            'list': list,
            'Any': Any,
        }

        python_type = type_mapping.get(field_type, Any)

        # Handle nested structures (simplified for this task)
        # If it's a list of objects, we might need to create a nested model,
        # but for the initial implementation, we'll use list of Any or dict.
        if field_type == 'list':
            # Check if items are defined
            items_spec = field_spec.get('items', {})
            if items_spec.get('type') == 'object':
                # For nested objects in lists, we usually define a separate model,
                # but here we accept list[dict] for flexibility in raw data.
                python_type = list
            else:
                python_type = list

        pydantic_fields[field_name] = (python_type, Field(default=..., description=description))

    # Create the dynamic model
    model_name = schema_name
    dynamic_model = create_model(model_name, **pydantic_fields)

    logger.info(f"Successfully created Pydantic model '{model_name}' from schema.")
    return dynamic_model

def get_site_schema() -> Type[BaseModel]:
    """Loads the Site schema (referenced from T006a)."""
    # Assuming site.schema.yaml exists in the same contracts dir
    schema_path = CONTRACTS_DIR / "site.schema.yaml"
    return load_schema_to_pydantic("Site", schema_path)

def get_timeseries_schema() -> Type[BaseModel]:
    """Loads the TimeSeries schema (referenced from T006b)."""
    # Assuming timeseries.schema.yaml exists in the same contracts dir
    schema_path = CONTRACTS_DIR / "timeseries.schema.yaml"
    return load_schema_to_pydantic("TimeSeries", schema_path)

def get_output_schema() -> Dict[str, Type[BaseModel]]:
    """
    Loads both FinalReport and SensitivityArtifact schemas from output.schema.yaml.
    Returns a dictionary mapping schema names to their Pydantic classes.
    """
    schema_path = CONTRACTS_DIR / "output.schema.yaml"
    return {
        "FinalReport": load_schema_to_pydantic("FinalReport", schema_path),
        "SensitivityArtifact": load_schema_to_pydantic("SensitivityArtifact", schema_path)
    }
