"""
Schema Validation Module.

Validates the generated YAML schemas (ceramic_entry.schema.yaml and model_result.schema.yaml)
to ensure they are correctly formatted and contain all required fields as specified in the task.
"""
import yaml
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

# Define the required fields for CeramicEntry schema
CERAMIC_ENTRY_REQUIRED_FIELDS: Set[str] = {
    "composition",
    "weibull_modulus",
    "sample_count",
    "is_range_flag",
    "range_original",
    "primary_anion_cation_group",
    "sintering_temp",
    "is_imputed",
    "mean_atomic_radius",
    "electronegativity_std",
    "valence_electron_concentration"
}

# Define the required fields for ModelResult schema
MODEL_RESULT_REQUIRED_FIELDS: Set[str] = {
    "model_type",
    "mae",
    "r_squared",
    "feature_importance_ranking",
    "cv_stability_scores"
}

def load_yaml_schema(file_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML schema file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Schema file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in {file_path}: {e}")

def validate_ceramic_entry_schema(schema: Dict[str, Any]) -> List[str]:
    """
    Validate the CeramicEntry schema.
    
    Checks:
    1. Valid YAML structure (properties exist)
    2. Contains all required fields
    
    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    
    if "properties" not in schema:
        errors.append("Schema missing 'properties' key.")
        return errors
    
    properties = schema["properties"]
    missing_fields = CERAMIC_ENTRY_REQUIRED_FIELDS - set(properties.keys())
    
    if missing_fields:
        errors.append(f"CeramicEntry schema missing required fields: {sorted(missing_fields)}")
    else:
        print("✓ CeramicEntry schema contains all required fields.")
        
    # Optional: Check for basic type definitions if present
    for field in CERAMIC_ENTRY_REQUIRED_FIELDS:
        if field in properties and "type" not in properties[field]:
            errors.append(f"CeramicEntry field '{field}' is missing 'type' definition.")
    
    return errors

def validate_model_result_schema(schema: Dict[str, Any]) -> List[str]:
    """
    Validate the ModelResult schema.
    
    Checks:
    1. Valid YAML structure (properties exist)
    2. Contains all required fields
    
    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    
    if "properties" not in schema:
        errors.append("Schema missing 'properties' key.")
        return errors
    
    properties = schema["properties"]
    missing_fields = MODEL_RESULT_REQUIRED_FIELDS - set(properties.keys())
    
    if missing_fields:
        errors.append(f"ModelResult schema missing required fields: {sorted(missing_fields)}")
    else:
        print("✓ ModelResult schema contains all required fields.")
        
    # Optional: Check for basic type definitions if present
    for field in MODEL_RESULT_REQUIRED_FIELDS:
        if field in properties and "type" not in properties[field]:
            errors.append(f"ModelResult field '{field}' is missing 'type' definition.")
    
    return errors

def main() -> int:
    """
    Main entry point for schema validation.
    
    Validates both ceramic_entry.schema.yaml and model_result.schema.yaml
    in the code/contracts/ directory.
    """
    contracts_dir = Path(__file__).parent
    ceramic_entry_path = contracts_dir / "ceramic_entry.schema.yaml"
    model_result_path = contracts_dir / "model_result.schema.yaml"
    
    all_errors = []
    success = True

    # Validate CeramicEntry Schema
    print(f"Validating: {ceramic_entry_path}")
    if not ceramic_entry_path.exists():
        print(f"❌ ERROR: File not found: {ceramic_entry_path}")
        success = False
    else:
        try:
            schema = load_yaml_schema(ceramic_entry_path)
            errors = validate_ceramic_entry_schema(schema)
            if errors:
                all_errors.extend(errors)
                success = False
            else:
                print("✓ CeramicEntry schema is valid.")
        except Exception as e:
            print(f"❌ ERROR: Failed to load CeramicEntry schema: {e}")
            success = False

    # Validate ModelResult Schema
    print(f"Validating: {model_result_path}")
    if not model_result_path.exists():
        print(f"❌ ERROR: File not found: {model_result_path}")
        success = False
    else:
        try:
            schema = load_yaml_schema(model_result_path)
            errors = validate_model_result_schema(schema)
            if errors:
                all_errors.extend(errors)
                success = False
            else:
                print("✓ ModelResult schema is valid.")
        except Exception as e:
            print(f"❌ ERROR: Failed to load ModelResult schema: {e}")
            success = False

    # Final Report
    print("\n" + "="*50)
    if success and not all_errors:
        print("✅ ALL SCHEMAS VALIDATED SUCCESSFULLY")
        return 0
    else:
        print("❌ VALIDATION FAILED")
        for err in all_errors:
            print(f"  - {err}")
        return 1

if __name__ == "__main__":
    sys.exit(main())