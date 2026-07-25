"""
Schema validation utilities for the text-tone project.
Loads YAML schemas and validates JSON data against them.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Attempt to import jsonschema, but allow graceful failure if not installed
try:
    import jsonschema
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("Warning: jsonschema library not found. Validation will be basic type checking only.")

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against a JSON Schema.
    Returns a list of error messages. Empty list if valid.
    """
    errors = []
    
    if not HAS_JSONSCHEMA:
        # Fallback basic validation if jsonschema is missing
        # This is not sufficient for production but prevents crash
        if schema.get('type') == 'object' and not isinstance(data, dict):
            errors.append("Data is not an object as expected by schema.")
        return errors

    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        errors.append(f"Validation Error: {e.message} at path: {' -> '.join(map(str, e.path))}")
    
    return errors

def main():
    """
    CLI entry point to validate data files against schemas.
    Usage: python code/validate_schemas.py <data_file> <schema_file>
    """
    if len(sys.argv) != 3:
        print("Usage: python code/validate_schemas.py <data_file.json> <schema_file.yaml>")
        sys.exit(1)
    
    data_path = Path(sys.argv[1])
    schema_path = Path(sys.argv[2])
    
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        sys.exit(1)
    
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in data file: {e}")
        sys.exit(1)
    
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        print(f"Error loading schema: {e}")
        sys.exit(1)
    
    # Handle CSV/JSONL if needed, but schema expects single object or array of objects
    # For this project, we assume the input is a list of records (rows)
    records = data if isinstance(data, list) else [data]
    
    all_valid = True
    for i, record in enumerate(records):
        errors = validate_json_against_schema(record, schema)
        if errors:
            all_valid = False
            for err in errors:
                print(f"Record {i}: {err}")
        else:
            print(f"Record {i}: Valid")
    
    if all_valid:
        print("\nAll records passed validation.")
        sys.exit(0)
    else:
        print("\nValidation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()