"""
Contract test for the descriptor set schema validation.
"""

import pytest
from jsonschema import validate, ValidationError
from tests.contract import load_schema

def test_descriptor_set_schema_validity():
    """Test that the schema itself is valid JSON Schema."""
    schema = load_schema("descriptor_set")
    assert isinstance(schema, dict)
    assert "properties" in schema

def test_descriptor_set_schema_validation():
    """Test that valid descriptor data passes schema validation."""
    schema = load_schema("descriptor_set")
    valid_data = {
        "metadata": {
            "computed_from_doi": "10.5281/zenodo.5778205",
            "computation_timestamp": "2023-10-27T10:00:00Z",
            "excluded_rows": []
        },
        "descriptors": [
            {
                "id": "sample_1",
                "composition": {"Fe": 0.5, "Ni": 0.5},
                "raw_descriptors": {
                    "delta": 0.05,
                    "delta_h_mix": -10.0,
                    "delta_chi": 0.2
                },
                "target": 1.2
            }
        ]
    }
    
    try:
        validate(instance=valid_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")

def test_descriptor_set_schema_exclusion_reasons():
    """Test that excluded rows have valid reasons."""
    schema = load_schema("descriptor_set")
    valid_data = {
        "metadata": {
            "computed_from_doi": "10.5281/zenodo.5778205",
            "computation_timestamp": "2023-10-27T10:00:00Z",
            "excluded_rows": [
                {"index": 0, "reason": "unknown_element"},
                {"index": 1, "reason": "missing_target"}
            ]
        },
        "descriptors": []
    }
    
    try:
        validate(instance=valid_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")
