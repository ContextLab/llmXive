"""
Contract test for dataset schema validation.
Verifies that the dataset schema file exists, is valid YAML, and contains
all required fields defined in T012.
"""
import pytest
import yaml
from pathlib import Path
from typing import Any, Dict

SCHEMA_PATH = Path("specs/001-predict-stiffness-cnn/contracts/dataset.schema.yaml")

# Required fields as per T012 and data-model.md
REQUIRED_FIELDS = {
    "image_path": str,
    "stiffness_tensor": list,
    "inclusion_density": float,
    "topology_type": str,
    "shape_factor": float,
    "connectivity": float,
    "seed": int,
}

def test_dataset_schema_exists():
    """Verify the schema file exists on disk."""
    assert SCHEMA_PATH.exists(), f"Dataset schema file missing at {SCHEMA_PATH}"

def test_dataset_schema_valid_yaml():
    """Verify the schema file is valid YAML."""
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema root must be a dictionary"
    except yaml.YAMLError as e:
        pytest.fail(f"Schema file is not valid YAML: {e}")

def test_dataset_schema_has_properties():
    """Verify the schema contains a 'properties' key."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    assert "properties" in schema, "Schema must contain 'properties' key"

def test_dataset_schema_contains_all_required_fields():
    """Verify all required fields defined in T012 are present in the schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    properties = schema.get("properties", {})
    missing_fields = []

    for field_name, expected_type in REQUIRED_FIELDS.items():
        if field_name not in properties:
            missing_fields.append(field_name)

    assert not missing_fields, f"Missing required fields in schema: {missing_fields}"

def test_dataset_schema_field_types_match_contract():
    """Verify the type definitions in the schema match the contract expectations."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    properties = schema.get("properties", {})

    # Map our expected Python types to common YAML/JSON schema type strings
    type_mapping = {
        str: ["string"],
        int: ["integer", "number"],
        float: ["number"],
        list: ["array"],
    }

    for field_name, expected_type in REQUIRED_FIELDS.items():
        field_def = properties[field_name]
        expected_schema_types = type_mapping.get(expected_type, [expected_type.__name__])

        # Handle both simple type string and object with 'type' key
        actual_type = field_def.get("type", field_def) if isinstance(field_def, dict) else field_def

        if actual_type not in expected_schema_types:
            pytest.fail(
                f"Field '{field_name}' has type '{actual_type}', "
                f"expected one of {expected_schema_types}"
            )

def test_dataset_schema_stiffness_tensor_is_array():
    """Specific check that stiffness_tensor is defined as an array."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    properties = schema.get("properties", {})
    stiffness_def = properties.get("stiffness_tensor", {})

    # Can be defined as "type: array" or just "array"
    actual_type = stiffness_def.get("type", stiffness_def) if isinstance(stiffness_def, dict) else stiffness_def

    assert actual_type == "array", "stiffness_tensor must be an array type"