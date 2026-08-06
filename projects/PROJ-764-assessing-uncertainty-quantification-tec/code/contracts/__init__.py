"""
Contracts module for schema validation and definition.

This module contains YAML schema definitions for:
- material_sample.schema.yaml: Input material data structure
- uq_prediction.schema.yaml: Output UQ prediction structure

These schemas are used for:
- Validating data integrity during pipeline execution
- Ensuring consistency across different UQ methods
- Contract testing in the test suite
"""

from pathlib import Path
from typing import Dict, Any
import yaml

CONTRACTS_DIR = Path(__file__).parent

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema definition from the contracts directory.

    Args:
        schema_name: Name of the schema file (e.g., 'material_sample.schema.yaml')

    Returns:
        Dictionary containing the loaded schema

    Raises:
        FileNotFoundError: If the schema file does not exist
        yaml.YAMLError: If the schema file is invalid YAML
    """
    schema_path = CONTRACTS_DIR / schema_name
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def get_material_sample_schema() -> Dict[str, Any]:
    """Load the material sample schema."""
    return load_schema('material_sample.schema.yaml')

def get_uq_prediction_schema() -> Dict[str, Any]:
    """Load the UQ prediction schema."""
    return load_schema('uq_prediction.schema.yaml')

__all__ = [
    'load_schema',
    'get_material_sample_schema',
    'get_uq_prediction_schema',
    'CONTRACTS_DIR'
]