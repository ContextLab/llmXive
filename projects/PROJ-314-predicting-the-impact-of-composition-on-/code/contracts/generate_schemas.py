"""
Script to generate and validate schema YAML files.
"""
import yaml
import sys
from pathlib import Path
import json
import jsonschema
from typing import Dict, Any, List

# Import the schemas to generate JSON schemas from
from contracts.schemas import CeramicEntry, ModelResult, export_schemas_to_yaml

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema from YAML."""
    path = Path(f"code/contracts/{schema_name}.yaml")
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)

def validate_schemas() -> bool:
    """Validate that schemas are correctly formatted and contain required fields."""
    try:
        ceramic_schema = load_schema("ceramic_entry")
        model_schema = load_schema("model_result")
        
        # Basic structure validation
        assert "properties" in ceramic_schema, "CeramicEntry schema missing properties"
        assert "properties" in model_schema, "ModelResult schema missing properties"
        
        # Check required fields for CeramicEntry
        required_ceramic = ["composition", "weibull_modulus", "sample_count", "primary_anion_cation_group"]
        for field in required_ceramic:
            assert field in ceramic_schema["properties"], f"Missing required field in CeramicEntry: {field}"
        
        # Check required fields for ModelResult
        required_model = ["model_type", "mae", "r_squared", "feature_importance_ranking", "cv_stability_scores"]
        for field in required_model:
            assert field in model_schema["properties"], f"Missing required field in ModelResult: {field}"
        
        print("All schemas validated successfully.")
        return True
    except Exception as e:
        print(f"Schema validation failed: {e}")
        return False

def validate_data_against_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """Validate data against a schema using jsonschema."""
    try:
        schema = load_schema(schema_name)
        # Convert Pydantic schema to JSON Schema format if needed
        jsonschema.validate(instance=data, schema=schema)
        return True
    except Exception as e:
        print(f"Data validation failed: {e}")
        return False

def generate_schemas() -> None:
    """Generate the schema YAML files."""
    export_schemas_to_yaml()
    print("Schemas generated successfully.")

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        success = validate_schemas()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "generate":
        generate_schemas()
    else:
        # Default: generate then validate
        generate_schemas()
        success = validate_schemas()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
