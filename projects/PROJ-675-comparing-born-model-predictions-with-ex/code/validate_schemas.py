"""
Schema validation utility for Born Model project.

Validates JSON Schema syntax and verifies that the schemas match the Pydantic models
defined in code/data_models.py.
"""
import json
import sys
from pathlib import Path

import jsonschema
from pydantic import TypeAdapter
from data_models import IonSolventPair, BornPrediction, ResidualAnalysis

SCHEMAS_DIR = Path(__file__).parent.parent / "contracts"
SCHEMA_FILES = {
    "IonSolventPair": "IonSolventPair.json",
    "BornPrediction": "BornPrediction.json",
    "ResidualAnalysis": "ResidualAnalysis.json",
}

def validate_schema_syntax(schema_path: Path) -> dict:
    """Load and parse a JSON Schema file, ensuring it is valid JSON."""
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return schema
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {schema_path}: {e}")

def validate_model_against_schema(model_class: type, schema: dict, instance: dict) -> bool:
    """
    Validate a dictionary instance against a JSON Schema.
    
    Args:
        model_class: The Pydantic model class (used for type hinting context).
        schema: The loaded JSON Schema.
        instance: A dictionary representing an instance of the model.
        
    Returns:
        True if valid, raises jsonschema.ValidationError otherwise.
    """
    try:
        jsonschema.validate(instance, schema)
        return True
    except jsonschema.ValidationError as e:
        raise e

def main():
    """
    Main entry point for schema validation.
    
    1. Loads all schemas from contracts/.
    2. Validates JSON syntax.
    3. Validates a sample instance (derived from Pydantic model defaults/types) against the schema.
    """
    print("Starting schema validation...")
    all_valid = True

    for model_name, schema_filename in SCHEMA_FILES.items():
        schema_path = SCHEMAS_DIR / schema_filename
        
        if not schema_path.exists():
            print(f"ERROR: Schema file not found: {schema_path}")
            all_valid = False
            continue

        print(f"Checking {schema_filename}...")
        
        # 1. Validate Syntax
        try:
            schema = validate_schema_syntax(schema_path)
            print(f"  - JSON Syntax: OK")
        except ValueError as e:
            print(f"  - JSON Syntax: FAILED - {e}")
            all_valid = False
            continue

        # 2. Validate against Pydantic Model
        # We construct a minimal valid instance based on the model's fields to ensure schema compatibility
        # This checks that the schema allows the fields the model expects.
        model_class = {
            "IonSolventPair": IonSolventPair,
            "BornPrediction": BornPrediction,
            "ResidualAnalysis": ResidualAnalysis
        }[model_name]

        # Create a dummy instance to get a dictionary representation for validation
        # We use TypeAdapter to handle the pydantic model to dict conversion robustly
        # Note: We are validating the *structure* compatibility, not running a full business logic test.
        # We create a minimal valid dict that satisfies the schema requirements.
        
        # For robustness, we'll generate a minimal valid instance based on schema 'required' fields
        # and basic types, then ensure the schema accepts it.
        # However, the task asks to verify schema matches model. 
        # A strong check: Ensure the schema's required fields match the model's required fields.
        
        model_fields = model_class.model_fields
        schema_required = set(schema.get("required", []))
        model_required = {k for k, v in model_fields.items() if v.is_required()}
        
        if schema_required != model_required:
            missing_in_schema = model_required - schema_required
            extra_in_schema = schema_required - model_required
            msg = f"  - Field Mismatch: Required fields differ.\n      Missing in schema: {missing_in_schema}\n      Extra in schema: {extra_in_schema}"
            print(msg)
            all_valid = False
            continue
        
        print(f"  - Required Fields Match: OK")

        # 3. Validate a synthetic instance
        # We construct a valid instance manually to ensure the schema accepts valid data types
        # matching the model's types.
        dummy_instance = {}
        for field_name, field_info in model_fields.items():
            if field_name == "instrument_metadata":
                dummy_instance[field_name] = {"source": "test"}
            elif field_name == "confidence_interval":
                dummy_instance[field_name] = [0.0, 1.0]
            elif field_name in ["temperature", "charge", "radius", "predicted_deltaG", "experimental_deltaG", "uncertainty", "p_value", "residual", "dielectric_constant", "ionic_radius"]:
                dummy_instance[field_name] = 1.0 if "float" in str(field_info.annotation) or "number" in str(schema["properties"].get(field_name, {}).get("type", "")) else 1
            elif field_name in ["ion_identifier", "solvent_identifier", "radius_type", "ion_size_class", "solvent_class", "calculation_timestamp"]:
                dummy_instance[field_name] = "test"
            elif field_name == "statistical_significance":
                dummy_instance[field_name] = True
            else:
                dummy_instance[field_name] = "test"

        try:
            validate_model_against_schema(model_class, schema, dummy_instance)
            print(f"  - Instance Validation: OK")
        except jsonschema.ValidationError as e:
            print(f"  - Instance Validation: FAILED - {e.message}")
            all_valid = False

        print("-" * 20)

    if all_valid:
        print("All schemas validated successfully.")
        sys.exit(0)
    else:
        print("Schema validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
