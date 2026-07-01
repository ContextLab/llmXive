"""
Schema Validation Module for llmXive Project PROJ-675.

This module validates that the JSON Schema files in contracts/ are valid
and that they correctly represent the Pydantic models defined in data_models.py.
"""
import json
import sys
from pathlib import Path

import jsonschema
from pydantic import TypeAdapter

# Import Pydantic models from the project API
from data_models import IonSolventPair, BornPrediction, ResidualAnalysis

CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"
SCHEMAS = {
    "IonSolventPair": "IonSolventPair.json",
    "BornPrediction": "BornPrediction.json",
    "ResidualAnalysis": "ResidualAnalysis.json",
}

def validate_schema_syntax(schema_path: Path) -> bool:
    """Validate that a JSON file is syntactically valid JSON."""
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {schema_path}: {e}")
        return False

def validate_model_against_schema(model_class, schema_path: Path) -> bool:
    """
    Validate that the Pydantic model structure is compatible with the JSON Schema.
    We do this by creating a TypeAdapter for the model and checking if a sample
    instance (derived from model fields) passes jsonschema validation.
    """
    model_name = model_class.__name__
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Create a sample instance using default values or dummy data where required
    # This is a structural check, not a runtime data check.
    # We construct a minimal valid dict based on required fields in schema.
    required_fields = schema.get("required", [])
    sample_data = {}

    for field_name in required_fields:
        # Check if the field exists in the Pydantic model
        if field_name not in model_class.model_fields:
            print(f"ERROR: Field '{field_name}' required by schema {schema_path} "
                  f"is missing in Pydantic model {model_name}.")
            return False

        field_info = model_class.model_fields[field_name]
        # Determine a dummy value based on type
        if field_info.annotation == int:
            sample_data[field_name] = 0
        elif field_info.annotation == float:
            sample_data[field_name] = 0.0
        elif field_info.annotation == str:
            sample_data[field_name] = "dummy"
        elif field_info.annotation == bool:
            sample_data[field_name] = False
        elif hasattr(field_info.annotation, "__origin__") and field_info.annotation.__origin__ is list:
            sample_data[field_name] = []
        elif hasattr(field_info.annotation, "__origin__") and field_info.annotation.__origin__ is dict:
            sample_data[field_name] = {}
        else:
            # Fallback for complex types or Optional
            sample_data[field_name] = None

    # Validate the sample data against the schema
    try:
        jsonschema.validate(instance=sample_data, schema=schema)
        print(f"OK: {model_name} schema matches {schema_path.name}.")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"ERROR: {model_name} schema mismatch with {schema_path.name}: {e.message}")
        return False

def main():
    all_passed = True

    print("Validating Schema Files and Pydantic Model Alignment...")
    print("-" * 60)

    for model_name, schema_filename in SCHEMAS.items():
        schema_path = CONTRACTS_DIR / schema_filename
        model_class = globals()[model_name]

        # Step 1: Check JSON syntax
        if not validate_schema_syntax(schema_path):
            all_passed = False
            continue

        # Step 2: Validate model alignment
        if not validate_model_against_schema(model_class, schema_path):
            all_passed = False

    print("-" * 60)
    if all_passed:
        print("SUCCESS: All schemas are valid and align with Pydantic models.")
        sys.exit(0)
    else:
        print("FAILURE: Schema validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
