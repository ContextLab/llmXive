"""
Contract testing framework for validating JSON schemas against simulation outputs.
This module provides utilities to load schemas and validate data files.
"""

from pathlib import Path
import json
from typing import Any, Dict, List

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    # jsonschema is a standard dependency for schema validation in research pipelines
    raise ImportError("The 'jsonschema' package is required for contract testing. "
                      "Install it via: pip install jsonschema")

SCHEMAS_DIR = Path(__file__).parent.parent.parent / "code" / "contracts"

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the contracts directory.

    Args:
        schema_name: The filename of the schema (e.g., 'simulation_run.json').

    Returns:
        The parsed schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the schema file is not valid JSON.
    """
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_against_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """
    Validate a data dictionary against a named JSON schema.

    Args:
        data: The data to validate.
        schema_name: The filename of the schema to use.

    Returns:
        True if valid.

    Raises:
        ValidationError: If the data does not conform to the schema.
    """
    schema = load_schema(schema_name)
    validate(instance=data, schema=schema)
    return True

def validate_file_against_schema(file_path: Path, schema_name: str) -> bool:
    """
    Load a JSON file and validate it against a named schema.

    Args:
        file_path: Path to the JSON data file.
        schema_name: The filename of the schema to use.

    Returns:
        True if valid.

    Raises:
        FileNotFoundError: If the data file or schema file is missing.
        json.JSONDecodeError: If the data file is not valid JSON.
        ValidationError: If the data does not conform to the schema.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return validate_against_schema(data, schema_name)
