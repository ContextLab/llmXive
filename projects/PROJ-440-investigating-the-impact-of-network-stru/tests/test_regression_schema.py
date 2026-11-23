import json
import yaml
from pathlib import Path
import pytest

from code.generate_regression_schema import create_schema, write_schema

SCHEMA_PATH = Path("contracts/regression_schema.schema.yaml")

@pytest.fixture
def schema_dict():
    """Load the generated schema for testing."""
    if not SCHEMA_PATH.exists():
        pytest.skip("Schema file not generated yet.")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_schema_exists():
    """Verify the schema file exists."""
    assert SCHEMA_PATH.exists(), "regression_schema.schema.yaml must exist"

def test_schema_structure(schema_dict):
    """Verify the schema contains required top-level keys."""
    required_keys = [
        "$schema", "title", "description", "type", "required", "properties"
    ]
    for key in required_keys:
        assert key in schema_dict, f"Schema missing required key: {key}"

def test_schema_title(schema_dict):
    """Verify the schema title."""
    assert schema_dict["title"] == "RegressionResults"

def test_schema_required_fields(schema_dict):
    """Verify all required fields are listed."""
    required_fields = [
        "model_type", "n_components", "coefficients", "vip_scores",
        "p_values", "p_values_corrected", "r_squared_train", "r_squared_test",
        "pc_loadings", "excluded_count", "metadata"
    ]
    for field in required_fields:
        assert field in schema_dict["required"], f"Required field '{field}' missing from schema"

def test_schema_property_types(schema_dict):
    """Verify basic property types are defined."""
    props = schema_dict["properties"]
    assert props["model_type"]["type"] == "string"
    assert props["n_components"]["type"] == "integer"
    assert props["coefficients"]["type"] == "object"
    assert props["vip_scores"]["type"] == "object"
    assert props["pc_loadings"]["type"] == "object"
    assert props["metadata"]["type"] == "object"

def test_schema_pc_loadings_structure(schema_dict):
    """Verify PC loadings structure includes PC1 and PC2."""
    pc_loadings = schema_dict["properties"]["pc_loadings"]
    assert "PC1" in pc_loadings["properties"]
    assert "PC2" in pc_loadings["properties"]
    assert "required" in pc_loadings
    assert "PC1" in pc_loadings["required"]
    assert "PC2" in pc_loadings["required"]

def test_schema_valid_json():
    """Verify the schema can be parsed as valid JSON (via yaml conversion)."""
    if not SCHEMA_PATH.exists():
        pytest.skip("Schema file not generated yet.")
    with open(SCHEMA_PATH, 'r') as f:
        data = yaml.safe_load(f)
    # Re-serialize to ensure it's valid JSON-compatible structure
    json_str = json.dumps(data)
    assert len(json_str) > 0