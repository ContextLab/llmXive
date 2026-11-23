"""
Contract test for dataset schema validation.

This test validates that the generated dataset metadata conforms to the
schema defined in contracts/dataset_schema.schema.yaml.

It verifies:
1. The schema file exists and is valid YAML.
2. Required fields are present in the schema.
3. Enum constraints (alloy_family) are respected in the data.
4. Data types match the schema definitions.
"""
import os
import json
import yaml
import pytest
from pathlib import Path
from typing import Any, Dict, List

SCHEMA_PATH = Path("contracts/dataset_schema.schema.yaml")
DATA_PATH = Path("data/raw/metadata.json")

@pytest.fixture
def schema() -> Dict[str, Any]:
    """Load the dataset schema from YAML."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    try:
        with open(SCHEMA_PATH, "r") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in schema: {e}")

@pytest.fixture
def dataset_metadata() -> List[Dict[str, Any]]:
    """Load the generated dataset metadata from JSON."""
    if not DATA_PATH.exists():
        pytest.fail(f"Dataset metadata not found: {DATA_PATH}")
    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in dataset metadata: {e}")

def test_schema_structure(schema: Dict[str, Any]) -> None:
    """Verify the schema has the required top-level keys."""
    assert "type" in schema, "Schema must have a 'type' field"
    assert schema["type"] == "object", "Schema root type must be 'object'"
    assert "properties" in schema, "Schema must have 'properties'"
    assert "required" in schema, "Schema must have 'required' fields list"

def test_required_fields_present(schema: Dict[str, Any], dataset_metadata: List[Dict[str, Any]]) -> None:
    """Verify all required fields are present in every record."""
    required_fields = schema.get("required", [])
    assert len(required_fields) > 0, "Schema must define required fields"

    for i, record in enumerate(dataset_metadata):
        for field in required_fields:
            assert field in record, f"Record {i} missing required field: {field}"

def test_alloy_family_enum(schema: Dict[str, Any], dataset_metadata: List[Dict[str, Any]]) -> None:
    """Verify alloy_family values match the schema enum."""
    properties = schema.get("properties", {})
    alloy_def = properties.get("alloy_family", {})
    allowed_values = alloy_def.get("enum")
    
    assert allowed_values is not None, "alloy_family must define an enum"
    assert set(allowed_values) == {"steel", "Al", "Ti"}, "Alloy enum must contain steel, Al, Ti"

    for i, record in enumerate(dataset_metadata):
        value = record.get("alloy_family")
        assert value in allowed_values, f"Record {i} has invalid alloy_family: {value}"

def test_k_ic_type(schema: Dict[str, Any], dataset_metadata: List[Dict[str, Any]]) -> None:
    """Verify k_ic values are numbers (float/int)."""
    properties = schema.get("properties", {})
    k_ic_def = properties.get("k_ic", {})
    k_ic_type = k_ic_def.get("type")
    
    assert k_ic_type in ["number", "integer"], "k_ic must be defined as number or integer"

    for i, record in enumerate(dataset_metadata):
        value = record.get("k_ic")
        assert isinstance(value, (int, float)), f"Record {i} k_ic is not a number: {type(value)}"

def test_image_path_format(schema: Dict[str, Any], dataset_metadata: List[Dict[str, Any]]) -> None:
    """Verify image_path is a string."""
    properties = schema.get("properties", {})
    img_def = properties.get("image_path", {})
    img_type = img_def.get("type")
    
    assert img_type == "string", "image_path must be defined as string"

    for i, record in enumerate(dataset_metadata):
        value = record.get("image_path")
        assert isinstance(value, str), f"Record {i} image_path is not a string: {type(value)}"
        # Basic path check
        assert value.endswith(".png"), f"Record {i} image_path does not end with .png: {value}"

def test_magnification_calibration_exists(schema: Dict[str, Any], dataset_metadata: List[Dict[str, Any]]) -> None:
    """Verify magnification_calibration field exists and is a number."""
    properties = schema.get("properties", {})
    assert "magnification_calibration" in properties, "Schema missing magnification_calibration"
    
    for i, record in enumerate(dataset_metadata):
        assert "magnification_calibration" in record, f"Record {i} missing magnification_calibration"
        assert isinstance(record["magnification_calibration"], (int, float)), \
            f"Record {i} magnification_calibration is not a number"

def test_section_thickness_exists(schema: Dict[str, Any], dataset_metadata: List[Dict[str, Any]]) -> None:
    """Verify section_thickness field exists and is a number."""
    properties = schema.get("properties", {})
    assert "section_thickness" in properties, "Schema missing section_thickness"
    
    for i, record in enumerate(dataset_metadata):
        assert "section_thickness" in record, f"Record {i} missing section_thickness"
        assert isinstance(record["section_thickness"], (int, float)), \
            f"Record {i} section_thickness is not a number"