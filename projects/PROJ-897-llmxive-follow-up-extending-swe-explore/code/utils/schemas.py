"""
Utility module for loading and managing JSON Schema definitions for validation.
This module provides the contract definitions used by validation.py.
"""
import os
from pathlib import Path
from typing import Dict, Any

# Base directory for contracts
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"

SCHEMA_FILES = {
    "dataset": "dataset_schema.yaml",
    "agent_log": "agent_log_schema.yaml",
    "result": "result_schema.yaml",
}

def get_schema_path(schema_type: str) -> Path:
    """
    Returns the absolute path to the specified schema file.

    Args:
        schema_type: One of 'dataset', 'agent_log', or 'result'.

    Returns:
        Path to the schema file.

    Raises:
        FileNotFoundError: If the schema file does not exist.
    """
    if schema_type not in SCHEMA_FILES:
        raise ValueError(f"Unknown schema type: {schema_type}")

    file_name = SCHEMA_FILES[schema_type]
    path = CONTRACTS_DIR / file_name

    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    return path

def load_schema(schema_type: str) -> Dict[str, Any]:
    """
    Loads a schema definition from a YAML file.

    Args:
        schema_type: One of 'dataset', 'agent_log', or 'result'.

    Returns:
        Dictionary containing the parsed YAML schema.
    """
    import yaml
    path = get_schema_path(schema_type)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
