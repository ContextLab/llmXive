import yaml
import json
import sys
from pathlib import Path
from typing import List, Set, Dict, Any

# Required fields for model_result.schema.yaml as per task T012b
REQUIRED_MODEL_RESULT_FIELDS = {
    "model_type",
    "mae",
    "r_squared",
    "feature_importance_ranking",
    "cv_stability_scores"
}

def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """Load a YAML file and return its contents as a dictionary."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {file_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_schema_fields(schema_data: Dict[str, Any], required_fields: Set[str], schema_name: str) -> bool:
    """
    Validate that the schema contains all required fields.
    Returns True if valid, False otherwise.
    """
    properties = schema_data.get("properties", {})
    found_fields = set(properties.keys())
    
    missing_fields = required_fields - found_fields
    
    if missing_fields:
        print(f"ERROR: {schema_name} is missing required fields: {missing_fields}")
        return False
    
    print(f"SUCCESS: {schema_name} contains all required fields: {required_fields}")
    return True

def main():
    """
    Main function to validate model_result.schema.yaml.
    """
    schema_path = Path("code/contracts/model_result.schema.yaml")
    
    if not schema_path.exists():
        print(f"ERROR: Schema file not found at {schema_path}")
        sys.exit(1)
    
    try:
        schema_data = load_yaml_file(str(schema_path))
        
        if not isinstance(schema_data, dict):
            print("ERROR: Invalid YAML structure (expected a dictionary)")
            sys.exit(1)
        
        is_valid = validate_schema_fields(schema_data, REQUIRED_MODEL_RESULT_FIELDS, "model_result.schema.yaml")
        
        if not is_valid:
            sys.exit(1)
        
        print("Validation passed for model_result.schema.yaml")
        sys.exit(0)
        
    except Exception as e:
        print(f"ERROR during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
