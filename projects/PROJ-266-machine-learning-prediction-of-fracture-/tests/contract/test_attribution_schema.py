"""
Contract test for attribution_schema.schema.yaml (Task T006b).

Verifies that the schema file exists, is valid YAML, and contains
the required 'image_id' property as per the verification command:
`python -c "import yaml; s=yaml.safe_load(open('contracts/attribution_schema.schema.yaml')); assert 'image_id' in s['properties']"`
"""
import os
import yaml
import pytest
from pathlib import Path

SCHEMA_PATH = Path("contracts/attribution_schema.schema.yaml")

@pytest.fixture
def schema():
    """Load the attribution schema."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, "r") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in schema file: {e}")

def test_schema_exists_and_is_valid(schema):
    """Basic sanity check that the schema loaded."""
    assert schema is not None
    assert isinstance(schema, dict)

def test_image_id_property_exists(schema):
    """
    Verification requirement: 
    assert 'image_id' in s['properties']
    """
    assert "properties" in schema, "Schema must have a 'properties' key"
    assert "image_id" in schema["properties"], "Schema must define 'image_id' property"

def test_image_id_has_type_and_description(schema):
    """Ensure image_id is well-defined."""
    image_id_def = schema["properties"]["image_id"]
    assert "type" in image_id_def, "image_id must have a type"
    assert image_id_def["type"] == "string", "image_id must be a string"
    assert "description" in image_id_def, "image_id should have a description"

def test_required_fields(schema):
    """Ensure critical fields are marked as required."""
    required = schema.get("required", [])
    assert "image_id" in required, "image_id must be a required field"
    assert "method" in required, "method must be a required field"
    assert "attribution_map_path" in required, "attribution_map_path must be required"
    assert "stability_metrics" in required, "stability_metrics must be required"

def test_stability_metrics_structure(schema):
    """Verify the nested stability_metrics structure."""
    stability_def = schema["properties"]["stability_metrics"]
    assert "properties" in stability_def, "stability_metrics must have properties"
    props = stability_def["properties"]
    
    required_metrics = ["mean_iou", "std_iou", "images_analyzed"]
    for metric in required_metrics:
        assert metric in props, f"stability_metrics must contain {metric}"