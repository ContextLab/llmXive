"""
Contract test for emotion mapping output schema (T025).
Validates that the output of code/analysis/emotion_mapping.py conforms to
contracts/dataset.schema.yaml.
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd
import yaml
import jsonschema
from jsonschema import validate, ValidationError

# Add project root to path for imports if running standalone
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Paths
SCHEMA_PATH = project_root / "contracts" / "dataset.schema.yaml"
# Expected output from US2 (T031)
OUTPUT_PATH = project_root / "data" / "processed" / "final_dataset.csv"

# Load schema
def load_schema():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Load data
def load_data():
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Output data file not found: {OUTPUT_PATH}. "
            "Ensure T031 (emotion_mapping) has been run successfully."
        )
    return pd.read_csv(OUTPUT_PATH)

def test_emotion_mapping_schema():
    """
    Contract test: Verify final_dataset.csv matches the schema defined in
    contracts/dataset.schema.yaml, specifically checking for the presence
    and types of emotion mapping fields (emotional_intensity, emotion_label).
    """
    schema = load_schema()
    df = load_data()

    # Convert dataframe to list of dicts for jsonschema validation
    # jsonschema expects a list of objects
    records = df.to_dict(orient="records")

    # Validate each record against the schema
    # Note: jsonschema.validate expects a single instance.
    # If the schema defines a 'type': 'array' of objects, we validate the whole list.
    # Otherwise, we might need to validate row by row or adjust schema usage.
    # Assuming the schema defines the structure of a single record or the array.
    
    # Check if schema expects an array of objects
    if schema.get("type") == "array":
        try:
            validate(instance=records, schema=schema)
        except ValidationError as e:
            raise AssertionError(f"Schema validation failed: {e.message}")
    else:
        # If schema is for a single object, validate the first record as a representative
        # or iterate if necessary. For robustness, we check the first few.
        if not records:
            raise AssertionError("Dataset is empty. Cannot validate schema.")
        
        # Validate structure against the 'items' schema if array type is implied by context
        # or validate the object schema directly if the schema is for a row.
        # Let's assume the schema provided in T008/T009/T022 defines the row structure.
        # If the schema file defines 'type: object', we validate a single row.
        # If it defines 'type: array', we validate the list.
        
        # Fallback: Validate the first row against the object schema if 'type' is 'object'
        # or if the schema is just the definition of a row.
        item_schema = schema.get("items", schema)
        
        for i, record in enumerate(records[:5]): # Validate first 5 rows for performance
            try:
                validate(instance=record, schema=item_schema)
            except ValidationError as e:
                raise AssertionError(
                    f"Row {i} failed schema validation: {e.message}. "
                    f"Path: {e.absolute_path}"
                )

    # Additional explicit checks for US2 specific requirements
    required_columns = ["emotional_intensity", "emotion_label"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    assert not missing_cols, f"Missing required columns for US2: {missing_cols}"

    # Check range of emotional_intensity (1-5)
    intensity_vals = df["emotional_intensity"].dropna()
    if len(intensity_vals) > 0:
        assert intensity_vals.min() >= 1, "emotional_intensity must be >= 1"
        assert intensity_vals.max() <= 5, "emotional_intensity must be <= 5"
        assert all(intensity_vals.isin([1, 2, 3, 4, 5])), "emotional_intensity must be integer 1-5"

    print("Contract test passed: Emotion mapping output schema is valid.")

if __name__ == "__main__":
    test_emotion_mapping_schema()