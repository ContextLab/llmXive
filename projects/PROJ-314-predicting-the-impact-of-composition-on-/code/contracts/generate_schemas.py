"""
Script to generate YAML schemas from Pydantic definitions.
"""
import yaml
import sys
from pathlib import Path
import json
import jsonschema
from typing import Dict, Any, List

# Import the schemas module to trigger generation
try:
    from .schemas import CeramicEntry, ModelResult, export_schemas_to_yaml
except ImportError:
    from schemas import CeramicEntry, ModelResult, export_schemas_to_yaml

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from a file."""
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_schemas(schema_dir: str = "code/contracts") -> bool:
    """Validate that generated schema files exist and are valid JSON/YAML."""
    import os
    ceramic_path = os.path.join(schema_dir, "ceramic_entry.schema.yaml")
    model_path = os.path.join(schema_dir, "model_result.schema.yaml")

    if not os.path.exists(ceramic_path):
        print(f"Error: {ceramic_path} not found.")
        return False
    
    if not os.path.exists(model_path):
        print(f"Error: {model_path} not found.")
        return False

    # Try to load as JSON to ensure it's valid
    try:
        with open(ceramic_path, 'r') as f:
            json.load(f)
        with open(model_path, 'r') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema files: {e}")
        return False

def validate_data_against_schema(data: Dict[str, Any], schema_path: str) -> bool:
    """Validate a data dictionary against a JSON schema."""
    schema = load_schema(schema_path)
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        print(f"Validation Error: {e.message}")
        return False

if __name__ == "__main__":
    # Generate schemas if called directly
    print("Generating schemas...")
    cer_path, mod_path = export_schemas_to_yaml()
    print(f"Generated: {cer_path}")
    print(f"Generated: {mod_path}")
    
    # Validate
    if validate_schemas():
        print("Schemas validated successfully.")
    else:
        print("Schema validation failed.")
        sys.exit(1)