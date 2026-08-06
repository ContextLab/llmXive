"""
Contract validation module for TransitLM pipeline.

Validates data against YAML schemas defined in data/contracts/
to ensure data integrity at pipeline stages.
"""
import json
import sys
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Simple schema validator without external heavy dependencies
# In a full production environment, jsonschema library would be used.
# Here we implement a lightweight check for critical fields and types.

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_type(value: Any, expected_type: str) -> bool:
    """Check if value matches expected JSON Schema type string."""
    if expected_type == "object":
        return isinstance(value, dict)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "null":
        return value is None
    return False

def validate_required(data: Dict[str, Any], required_fields: List[str], path: str = "") -> List[str]:
    """Check if all required fields are present."""
    errors = []
    for field in required_fields:
        if field not in data:
          errors.append(f"Missing required field '{field}' at {path or 'root'}")
    return errors

def validate_properties(
    data: Dict[str, Any], 
    schema: Dict[str, Any], 
    path: str = ""
) -> List[str]:
    """Recursively validate data against schema properties."""
    errors = []
    
    if "required" in schema:
        errors.extend(validate_required(data, schema["required"], path))
    
    if "properties" in schema:
        for prop, prop_schema in schema["properties"].items():
            if prop in data:
                value = data[prop]
                
                # Check type
                if "type" in prop_schema:
                    if not validate_type(value, prop_schema["type"]):
                        errors.append(
                            f"Type mismatch for '{prop}' at {path}. "
                            f"Expected {prop_schema['type']}, got {type(value).__name__}"
                        )
                        continue
                
                # Recurse for objects
                if prop_schema["type"] == "object" and isinstance(value, dict):
                    errors.extend(validate_properties(value, prop_schema, f"{path}.{prop}"))
                
                # Check array items
                elif prop_schema["type"] == "array" and isinstance(value, list):
                    if "items" in prop_schema:
                        item_schema = prop_schema["items"]
                        for idx, item in enumerate(value):
                            if item_schema["type"] == "object" and isinstance(item, dict):
                                errors.extend(
                                    validate_properties(item, item_schema, f"{path}.{prop}[{idx}]")
                                )
                            elif "type" in item_schema:
                                if not validate_type(item, item_schema["type"]):
                                    errors.append(
                                        f"Array item type mismatch at {path}.{prop}[{idx}]. "
                                        f"Expected {item_schema['type']}, got {type(item).__name__}"
                                    )
                
                # Check enum
                if "enum" in prop_schema:
                    if value not in prop_schema["enum"]:
                        errors.append(
                            f"Value '{value}' for '{prop}' at {path} not in enum {prop_schema['enum']}"
                        )
                
                # Check minimum/maximum for numbers
                if "minimum" in prop_schema and isinstance(value, (int, float)):
                    if value < prop_schema["minimum"]:
                        errors.append(
                            f"Value {value} for '{prop}' at {path} is below minimum {prop_schema['minimum']}"
                        )
                if "maximum" in prop_schema and isinstance(value, (int, float)):
                    if value > prop_schema["maximum"]:
                        errors.append(
                            f"Value {value} for '{prop}' at {path} is above maximum {prop_schema['maximum']}"
                        )
                
                # Check pattern for strings
                if "pattern" in prop_schema and isinstance(value, str):
                    import re
                    if not re.match(prop_schema["pattern"], value):
                        errors.append(
                            f"Value '{value}' for '{prop}' at {path} does not match pattern {prop_schema['pattern']}"
                        )
                
                # Check minItems for arrays
                if "minItems" in prop_schema and isinstance(value, list):
                    if len(value) < prop_schema["minItems"]:
                        errors.append(
                            f"Array '{prop}' at {path} has {len(value)} items, minimum is {prop_schema['minItems']}"
                        )
                
                # Check maxItems for arrays
                if "maxItems" in prop_schema and isinstance(value, list):
                    if len(value) > prop_schema["maxItems"]:
                        errors.append(
                            f"Array '{prop}' at {path} has {len(value)} items, maximum is {prop_schema['maxItems']}"
                        )

    return errors

def validate_dataset_schema(data_path: Path, schema_path: Path) -> Tuple[bool, List[str]]:
    """Validate the preprocessed dataset against the dataset schema."""
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in data file: {e}"]
    except FileNotFoundError:
        return False, [f"Data file not found: {data_path}"]

    schema = load_schema(schema_path)
    errors = validate_properties(data, schema)
    
    if errors:
        return False, errors
    return True, []

def validate_output_schema(data_path: Path, schema_path: Path) -> Tuple[bool, List[str]]:
    """Validate an analysis output file against the output schema."""
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in data file: {e}"]
    except FileNotFoundError:
        return False, [f"Data file not found: {data_path}"]

    schema = load_schema(schema_path)
    errors = validate_properties(data, schema)
    
    if errors:
        return False, errors
    return True, []

def main():
    """Main entry point for CLI validation."""
    if len(sys.argv) < 3:
        print("Usage: python -m data.contract_validator <data_file> <schema_type>")
        print("  schema_type: 'dataset' or 'output'")
        sys.exit(1)

    data_file = Path(sys.argv[1])
    schema_type = sys.argv[2]

    base_dir = data_file.parent.parent
    contracts_dir = base_dir / "contracts"

    if schema_type == "dataset":
        schema_path = contracts_dir / "dataset.schema.yaml"
        is_valid, errors = validate_dataset_schema(data_file, schema_path)
    elif schema_type == "output":
        schema_path = contracts_dir / "output.schema.yaml"
        is_valid, errors = validate_output_schema(data_file, schema_path)
    else:
        print(f"Unknown schema type: {schema_type}. Use 'dataset' or 'output'.")
        sys.exit(1)

    if is_valid:
        print(f"Validation PASSED for {data_file.name}")
        sys.exit(0)
    else:
        print(f"Validation FAILED for {data_file.name}")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
