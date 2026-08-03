import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

def load_json_file(path: Path) -> Any:
    """Load and parse a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

def load_schema_file(path: Path) -> Dict[str, Any]:
    """Load and parse a JSON schema file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Schema file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in schema {path}: {e}")

def validate_against_schema(data: Any, schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against a JSON schema (draft-07 compatible subset).
    Returns a list of error messages. If empty, validation passed.
    
    Supports: type, required, properties, items (for lists), additionalProperties.
    """
    errors: List[str] = []
    
    # Type check
    if 'type' in schema:
        expected_type = schema['type']
        if expected_type == 'object':
            if not isinstance(data, dict):
                errors.append(f"Expected object, got {type(data).__name__}")
        elif expected_type == 'array':
            if not isinstance(data, list):
                errors.append(f"Expected array, got {type(data).__name__}")
        elif expected_type == 'string':
            if not isinstance(data, str):
                errors.append(f"Expected string, got {type(data).__name__}")
        elif expected_type == 'number':
            if not isinstance(data, (int, float)):
                errors.append(f"Expected number, got {type(data).__name__}")
        elif expected_type == 'boolean':
            if not isinstance(data, bool):
                errors.append(f"Expected boolean, got {type(data).__name__}")
        elif expected_type == 'integer':
            if not isinstance(data, int) or isinstance(data, bool):
                errors.append(f"Expected integer, got {type(data).__name__}")
    
    # Required fields (for objects)
    if isinstance(data, dict) and 'required' in schema:
        for field in schema['required']:
            if field not in data:
                errors.append(f"Missing required field: '{field}'")
    
    # Properties (for objects)
    if isinstance(data, dict) and 'properties' in schema:
        for prop_name, prop_schema in schema['properties'].items():
            if prop_name in data:
                prop_errors = validate_against_schema(data[prop_name], prop_schema)
                for err in prop_errors:
                    errors.append(f"Field '{prop_name}': {err}")
        
        # Check for additional properties if not allowed
        if schema.get('additionalProperties') is False:
            allowed = set(schema.get('properties', {}).keys())
            extra = set(data.keys()) - allowed
            if extra:
                errors.append(f"Additional properties not allowed: {extra}")
    
    # Items (for arrays)
    if isinstance(data, list) and 'items' in schema:
        for i, item in enumerate(data):
            item_errors = validate_against_schema(item, schema['items'])
            for err in item_errors:
                errors.append(f"Item [{i}]: {err}")
    
    return errors

def validate_raw_schema(input_path: Path, schema_path: Path) -> bool:
    """
    Validate a raw perturbation candidates file against the schema.
    Returns True if valid, False otherwise.
    """
    try:
        data = load_json_file(input_path)
        schema = load_schema_file(schema_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading files: {e}", file=sys.stderr)
        return False
    
    if not isinstance(data, list):
        print("Error: Input file must contain a JSON array.", file=sys.stderr)
        return False
    
    errors = validate_against_schema(data, schema)
    
    if errors:
        print("Validation FAILED with errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return False
    
    print("Validation PASSED.")
    return True

def validate_filtered_schema(input_path: Path, schema_path: Path) -> bool:
    """
    Validate a filtered perturbation candidates file against the schema.
    Same logic as validate_raw_schema but with specific error context if needed.
    Currently identical, but kept separate for future differentiation.
    """
    return validate_raw_schema(input_path, schema_path)

def validate_error_classification_schema(input_path: Path, schema_path: Path) -> bool:
    """
    Validate an error classification report file against a schema.
    Currently uses the same generic validator.
    """
    return validate_raw_schema(input_path, schema_path)

def main():
    parser = argparse.ArgumentParser(
        description="Validate JSON files against a JSON schema."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        type=Path,
        help="Path to the input JSON file to validate."
    )
    parser.add_argument(
        "--schema", "-s",
        required=True,
        type=Path,
        help="Path to the JSON schema file."
    )
    parser.add_argument(
        "--type", "-t",
        choices=["raw", "filtered", "error_classification"],
        default="raw",
        help="Type of validation to perform (default: raw)."
    )
    
    args = parser.parse_args()
    
    if args.type == "raw":
        success = validate_raw_schema(args.input, args.schema)
    elif args.type == "filtered":
        success = validate_filtered_schema(args.input, args.schema)
    elif args.type == "error_classification":
        success = validate_error_classification_schema(args.input, args.schema)
    else:
        print(f"Unknown validation type: {args.type}", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()