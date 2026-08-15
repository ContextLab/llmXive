"""
Validation logic for schema files.
Ensures generated YAML schemas match the Pydantic definitions.
"""
import yaml
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

# Required fields for CeramicEntry as per T012a
REQUIRED_CERAMIC_ENTRY_FIELDS = {
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

# Required fields for ModelResult as per T012b
REQUIRED_MODEL_RESULT_FIELDS = {
    "model_type",
    "mae",
    "r_squared",
    "feature_importance_ranking",
    "cv_stability_scores"
}

SCHEMA_DIR = Path(__file__).parent
CERAMIC_SCHEMA_PATH = SCHEMA_DIR / "ceramic_entry.schema.yaml"
MODEL_SCHEMA_PATH = SCHEMA_DIR / "model_result.schema.yaml"


def load_yaml_schema(path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_ceramic_entry_schema(schema: Dict[str, Any]) -> List[str]:
    """
    Validate ceramic_entry.schema.yaml against required fields.
    Returns a list of error messages. Empty list if valid.
    """
    errors = []
    
    # Check top-level structure
    if "properties" not in schema:
        errors.append("Schema missing 'properties' key")
        return errors
    
    properties = schema["properties"]
    
    # Check required fields
    missing_fields = REQUIRED_CERAMIC_ENTRY_FIELDS - set(properties.keys())
    if missing_fields:
        errors.append(f"Missing required fields in ceramic_entry schema: {sorted(missing_fields)}")
    
    # Check 'required' list in schema matches required fields
    schema_required = set(schema.get("required", []))
    if not REQUIRED_CERAMIC_ENTRY_FIELDS.issubset(schema_required):
        missing_in_required = REQUIRED_CERAMIC_ENTRY_FIELDS - schema_required
        errors.append(f"Fields in properties but not in 'required' list: {sorted(missing_in_required)}")
    
    return errors


def validate_model_result_schema(schema: Dict[str, Any]) -> List[str]:
    """
    Validate model_result.schema.yaml against required fields.
    Returns a list of error messages. Empty list if valid.
    """
    errors = []
    
    # Check top-level structure
    if "properties" not in schema:
        errors.append("Schema missing 'properties' key")
        return errors
    
    properties = schema["properties"]
    
    # Check required fields
    missing_fields = REQUIRED_MODEL_RESULT_FIELDS - set(properties.keys())
    if missing_fields:
        errors.append(f"Missing required fields in model_result schema: {sorted(missing_fields)}")
    
    # Check 'required' list in schema matches required fields
    schema_required = set(schema.get("required", []))
    if not REQUIRED_MODEL_RESULT_FIELDS.issubset(schema_required):
        missing_in_required = REQUIRED_MODEL_RESULT_FIELDS - schema_required
        errors.append(f"Fields in properties but not in 'required' list: {sorted(missing_in_required)}")
    
    return errors


def main():
    """Main entry point for schema validation."""
    all_valid = True
    
    print("Validating ceramic_entry.schema.yaml...")
    try:
        ceramic_schema = load_yaml_schema(CERAMIC_SCHEMA_PATH)
        ceramic_errors = validate_ceramic_entry_schema(ceramic_schema)
        if ceramic_errors:
            print(f"  ❌ Invalid: {len(ceramic_errors)} error(s)")
            for err in ceramic_errors:
                print(f"     - {err}")
            all_valid = False
        else:
            print("  ✅ Valid")
    except FileNotFoundError as e:
        print(f"  ❌ Error: {e}")
        all_valid = False
    except Exception as e:
        print(f"  ❌ Error loading schema: {e}")
        all_valid = False
    
    print("\nValidating model_result.schema.yaml...")
    try:
        model_schema = load_yaml_schema(MODEL_SCHEMA_PATH)
        model_errors = validate_model_result_schema(model_schema)
        if model_errors:
            print(f"  ❌ Invalid: {len(model_errors)} error(s)")
            for err in model_errors:
                print(f"     - {err}")
            all_valid = False
        else:
            print("  ✅ Valid")
    except FileNotFoundError as e:
        print(f"  ❌ Error: {e}")
        all_valid = False
    except Exception as e:
        print(f"  ❌ Error loading schema: {e}")
        all_valid = False
    
    if all_valid:
        print("\n✅ All schemas validated successfully.")
        sys.exit(0)
    else:
        print("\n❌ Schema validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()