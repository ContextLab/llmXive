"""
Contract tests and schema definitions for the glass formation tendency project.

This module contains JSON/YAML schemas used to validate data integrity
and model artifacts throughout the pipeline.
"""

import os
from pathlib import Path

def get_schema_path(schema_name: str) -> Path:
    """Get the absolute path to a schema file."""
    current_dir = Path(__file__).parent
    return current_dir / f"{schema_name}.schema.yaml"

def load_schema(schema_name: str) -> dict:
    """Load a schema definition from a YAML file."""
    import yaml
    path = get_schema_path(schema_name)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

__all__ = ['get_schema_path', 'load_schema']
