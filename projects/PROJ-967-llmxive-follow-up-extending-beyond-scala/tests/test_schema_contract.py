"""
Tests for T001d: Schema Contract Validation.
Ensures the schema file exists, is valid YAML, and meets structural requirements.
"""
import pytest
import yaml
import sys
import os
from pathlib import Path

# Add parent code directory to path for imports if needed, 
# though we will test the file directly here.
ROOT_DIR = Path(__file__).parent.parent
SCHEMA_PATH = ROOT_DIR / "contracts" / "dataset.schema.yaml"

REQUIRED_TOP_LEVEL = [
    "prompt",
    "image_path",
    "teacher_logits",
    "student_scalar",
    "human_annotations",
    "primary_dimension"
]

REQUIRED_HUMAN_DIMS = [
    "Alignment",
    "Realism",
    "Aesthetics",
    "Plausibility"
]

@pytest.fixture
def schema_data():
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_schema_file_exists():
    """Verify the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

def test_schema_is_valid_yaml(schema_data):
    """Verify the file parses as valid YAML."""
    assert isinstance(schema_data, dict), "Schema root must be a dictionary."

def test_schema_has_properties_key(schema_data):
    """Verify the 'properties' key exists."""
    assert "properties" in schema_data, "Missing 'properties' key in schema."

def test_required_top_level_fields(schema_data):
    """Verify all required top-level fields are defined."""
    props = schema_data["properties"]
    missing = [k for k in REQUIRED_TOP_LEVEL if k not in props]
    assert not missing, f"Missing required top-level fields: {missing}"

def test_human_annotations_structure(schema_data):
    """Verify human_annotations contains all required dimensions."""
    props = schema_data["properties"]
    ha = props.get("human_annotations", {})
    ha_props = ha.get("properties", {})
    
    missing_dims = [d for d in REQUIRED_HUMAN_DIMS if d not in ha_props]
    assert not missing_dims, f"Missing dimensions in human_annotations: {missing_dims}"

def test_prompt_type_is_string(schema_data):
    """Verify prompt is defined as string."""
    props = schema_data["properties"]
    assert props.get("prompt", {}).get("type") == "string", "prompt must be type 'string'"

def test_student_scalar_type_is_number(schema_data):
    """Verify student_scalar is defined as number."""
    props = schema_data["properties"]
    assert props.get("student_scalar", {}).get("type") == "number", "student_scalar must be type 'number'"

def test_primary_dimension_type_is_string(schema_data):
    """Verify primary_dimension is defined as string."""
    props = schema_data["properties"]
    assert props.get("primary_dimension", {}).get("type") == "string", "primary_dimension must be type 'string'"

def test_primary_dimension_enum_values(schema_data):
    """Verify primary_dimension has correct enum values."""
    props = schema_data["properties"]
    pd = props.get("primary_dimension", {})
    enum_vals = pd.get("enum", [])
    expected = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    assert set(enum_vals) == set(expected), f"primary_dimension enum mismatch. Expected {expected}, got {enum_vals}"