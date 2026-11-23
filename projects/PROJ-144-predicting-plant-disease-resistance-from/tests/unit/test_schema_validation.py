import pytest
import json
import yaml
from pathlib import Path

from code.research.validate_schema import load_yaml_schema, validate_schema_structure, validate_with_jsonschema

SCHEMA_PATH = Path("contracts/metadata.schema.yaml")

@pytest.fixture
def schema_dict():
    if SCHEMA_PATH.exists():
        return load_yaml_schema(SCHEMA_PATH)
    return {}

def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), "contracts/metadata.schema.yaml must exist"

def test_schema_loads_valid_yaml(schema_dict):
    assert isinstance(schema_dict, dict), "Schema must be a valid dictionary"
    assert "$schema" in schema_dict, "Schema must define $schema"
    assert "type" in schema_dict, "Schema must define root type"

def test_schema_structure_valid(schema_dict):
    errors = validate_schema_structure(schema_dict)
    assert len(errors) == 0, f"Schema structure errors found: {errors}"

def test_schema_valid_json_schema(schema_dict):
    errors = validate_with_jsonschema(schema_dict)
    assert len(errors) == 0, f"JSON Schema validation errors found: {errors}"

def test_required_definitions_present(schema_dict):
    assert "$defs" in schema_dict
    assert "MetaboliteProfile" in schema_dict["$defs"]
    assert "ResistanceLabel" in schema_dict["$defs"]

def test_metabolite_profile_required_fields(schema_dict):
    profile = schema_dict["$defs"]["MetaboliteProfile"]
    assert "required" in profile
    required = set(profile["required"])
    assert "sample_id" in required
    assert "InChIKey" in required
    assert "normalized_intensity" in required

def test_resistance_label_required_fields(schema_dict):
    label = schema_dict["$defs"]["ResistanceLabel"]
    assert "required" in label
    required = set(label["required"])
    assert "germplasm_id" in required
    assert "assay_score" in required
    assert "harmonized_score" in required
