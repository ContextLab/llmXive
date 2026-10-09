"""
Utility script to validate JSON files against a JSON schema.

This module provides command-line validation for JSON data files
against schema definitions defined in contracts/.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

def load_json_file(path: Path) -> Any:
    """Load a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_schema_file(path: Path) -> Dict[str, Any]:
    """Load a JSON schema file."""
    return load_json_file(path)

def validate_against_schema(data: Any, schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against a JSON schema (basic validation without external libs).

    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    # Basic type checking for root
    if schema.get("type") == "array":
        if not isinstance(data, list):
            errors.append(f"Expected root to be a list, got {type(data)}")
            return errors
        
        items_schema = schema.get("items", {})
        for i, item in enumerate(data):
            item_errors = validate_item_against_schema(item, items_schema, i)
            errors.extend(item_errors)
    elif schema.get("type") == "object":
        if not isinstance(data, dict):
            errors.append(f"Expected root to be an object, got {type(data)}")
    else:
        # Default: no strict root type check if not specified
        pass

    return errors

def validate_item_against_schema(item: Any, schema: Dict[str, Any], index: int) -> List[str]:
    """Validate a single item against the items schema."""
    errors = []
    
    if schema.get("type") == "object":
        if not isinstance(item, dict):
            errors.append(f"Item {index}: Expected object, got {type(item)}")
            return errors
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Check required fields
        for field in required:
            if field not in item:
                errors.append(f"Item {index}: Missing required field '{field}'")
        
        # Check property types
        for field, field_schema in properties.items():
            if field in item:
                value = item[field]
                expected_type = field_schema.get("type")
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Item {index}.{field}: Expected string, got {type(value)}")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Item {index}.{field}: Expected number, got {type(value)}")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Item {index}.{field}: Expected boolean, got {type(value)}")
                elif expected_type == "integer" and not isinstance(value, int):
                    errors.append(f"Item {index}.{field}: Expected integer, got {type(value)}")
                
                # Check enum
                if "enum" in field_schema:
                    if value not in field_schema["enum"]:
                        errors.append(f"Item {index}.{field}: Value '{value}' not in enum {field_schema['enum']}")
                
                # Check minimum/maximum for numbers
                if expected_type in ["number", "integer"]:
                    if "minimum" in field_schema and value < field_schema["minimum"]:
                        errors.append(f"Item {index}.{field}: Value {value} is less than minimum {field_schema['minimum']}")
                    if "maximum" in field_schema and value > field_schema["maximum"]:
                        errors.append(f"Item {index}.{field}: Value {value} is greater than maximum {field_schema['maximum']}")
    return errors

def validate_raw_schema(input_path: Path, schema_path: Path) -> bool:
    """Validate perturbation candidates raw file."""
    return validate_generic(input_path, schema_path)

def validate_filtered_schema(input_path: Path, schema_path: Path) -> bool:
    """Validate perturbation candidates filtered file."""
    return validate_generic(input_path, schema_path)

def validate_error_classification_schema(input_path: Path, schema_path: Path) -> bool:
    """Validate error classification report file."""
    return validate_generic(input_path, schema_path)

def validate_generic(input_path: Path, schema_path: Path) -> bool:
    """Generic validation function."""
    try:
        data = load_json_file(input_path)
        schema = load_schema_file(schema_path)
        
        errors = validate_against_schema(data, schema)
        
        if errors:
            print(f"Validation FAILED for {input_path}:")
            for err in errors:
                print(f"  - {err}")
            return False
        else:
            print(f"Validation PASSED for {input_path}")
            return True
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}")
        return False
    except Exception as e:
        print(f"Error: Unexpected error - {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate JSON files against a schema.")
    parser.add_argument("--input", required=True, help="Path to the input JSON file")
    parser.add_argument("--schema", required=True, help="Path to the JSON schema file")
    parser.add_argument("--type", choices=["raw", "filtered", "error_classification", "generic"], 
                        default="generic", help="Type of validation to perform")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    schema_path = Path(args.schema)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)
    
    success = False
    if args.type == "raw":
        success = validate_raw_schema(input_path, schema_path)
    elif args.type == "filtered":
        success = validate_filtered_schema(input_path, schema_path)
    elif args.type == "error_classification":
        success = validate_error_classification_schema(input_path, schema_path)
    else:
        success = validate_generic(input_path, schema_path)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()