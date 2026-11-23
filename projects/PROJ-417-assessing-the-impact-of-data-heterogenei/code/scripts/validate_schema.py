import json
import sys
import yaml
import argparse
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

def load_schema(schema_path: str) -> dict:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_data(data_path: str) -> dict:
    """Load a JSON data file."""
    with open(data_path, 'r') as f:
        return json.load(f)

def validate_against_schema(schema: dict, data: dict) -> bool:
    """Validate data against a JSON schema."""
    try:
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        if errors:
            for error in errors:
                print(f"Validation Error: {error.message} at {'.'.join(map(str, error.path))}")
            return False
        return True
    except Exception as e:
        print(f"Schema validation error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate JSON data against a YAML schema.")
    parser.add_argument('--schema', required=True, help="Path to the YAML schema file.")
    parser.add_argument('--input', required=True, help="Path to the JSON data file.")
    args = parser.parse_args()

    schema_path = Path(args.schema)
    data_path = Path(args.input)

    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        sys.exit(1)

    schema = load_schema(str(schema_path))
    data = load_data(str(data_path))

    if validate_against_schema(schema, data):
        print("Validation successful.")
        sys.exit(0)
    else:
        print("Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
