"""
Schema validation utilities for model output artifacts.
Validates JSON files against the YAML schema definitions.
"""

import json
import yaml
from pathlib import Path
import sys

# Schema file paths
MODEL_OUTPUT_SCHEMA_PATH = Path(__file__).parent.parent / "specs" / "001-visual-attention-recall" / "contracts" / "model_output.schema.yaml"


def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema from disk."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def validate_json_against_schema(data: dict, schema: dict) -> tuple[bool, list[str]]:
    """
    Validate a JSON object against a schema definition.
    
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []
    
    # Basic type check
    if not isinstance(data, dict):
        errors.append("Data must be a dictionary/object")
        return False, errors
    
    # Check for required top-level keys based on schema definitions
    if "definitions" in schema:
        # Try to match against model_results or power_analysis
        valid_match = False
        
        # Check model_results structure
        if "model_results" in schema["definitions"]:
            model_schema = schema["definitions"]["model_results"]
            if _validate_structure(data, model_schema, "model_results"):
                valid_match = True
        
        # Check power_analysis structure
        if "power_analysis" in schema["definitions"]:
            power_schema = schema["definitions"]["power_analysis"]
            if _validate_structure(data, power_schema, "power_analysis"):
                valid_match = True
        
        if not valid_match:
            errors.append("Data does not match model_results or power_analysis schema")
    
    return len(errors) == 0, errors


def _validate_structure(data: dict, schema_def: dict, schema_name: str) -> bool:
    """Validate the structure of data against a specific schema definition."""
    if "required" not in schema_def:
        return True
    
    missing_keys = []
    for key in schema_def["required"]:
        if key not in data:
            missing_keys.append(key)
    
    if missing_keys:
        return False
    
    # Recursively validate nested structures if needed
    if "properties" in schema_def:
        for prop, prop_schema in schema_def["properties"].items():
            if prop in data and prop_schema.get("type") == "object":
                if "required" in prop_schema:
                    for req_key in prop_schema["required"]:
                        if req_key not in data.get(prop, {}):
                            return False
    
    return True


def validate_model_output_file(file_path: Path) -> bool:
    """
    Validate a model output JSON file against the schema.
    
    Args:
        file_path: Path to the JSON file to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Model output file not found: {file_path}")
    
    schema = load_schema(MODEL_OUTPUT_SCHEMA_PATH)
    
    with open(file_path, "r") as f:
        data = json.load(f)
    
    is_valid, errors = validate_json_against_schema(data, schema)
    
    if not is_valid:
        print(f"Validation failed for {file_path}:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print(f"Validation passed for {file_path}")
    return True


def main():
    """Main entry point for schema validation."""
    # Default paths
    model_results_path = Path(__file__).parent.parent / "artifacts" / "logs" / "model_results.json"
    power_analysis_path = Path(__file__).parent.parent / "artifacts" / "logs" / "power_analysis.json"
    
    all_valid = True
    
    if model_results_path.exists():
        if not validate_model_output_file(model_results_path):
            all_valid = False
    else:
        print(f"Warning: {model_results_path} not found")
    
    if power_analysis_path.exists():
        if not validate_model_output_file(power_analysis_path):
            all_valid = False
    else:
        print(f"Warning: {power_analysis_path} not found")
    
    if not all_valid:
        sys.exit(1)
    
    print("All model output files validated successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()