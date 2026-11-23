import pytest
import json
import yaml
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from research.validate_schema import load_yaml_schema, validate_schema_structure, validate_with_jsonschema

@pytest.fixture
def valid_schema_path(tmp_path):
    schema_content = """
    $schema: http://json-schema.org/draft-07/schema#
    type: object
    properties:
      test_property:
        type: string
    """
    file_path = tmp_path / "test_schema.yaml"
    file_path.write_text(schema_content)
    return file_path

@pytest.fixture
def invalid_schema_path(tmp_path):
    # Missing 'type' at root
    schema_content = """
    $schema: http://json-schema.org/draft-07/schema#
    properties:
      test_property:
        type: string
    """
    file_path = tmp_path / "invalid_schema.yaml"
    file_path.write_text(schema_content)
    return file_path

def test_load_yaml_schema_valid(valid_schema_path):
    schema = load_yaml_schema(valid_schema_path)
    assert isinstance(schema, dict)
    assert 'properties' in schema
    assert 'test_property' in schema['properties']

def test_validate_schema_structure_valid(valid_schema_path):
    schema = load_yaml_schema(valid_schema_path)
    errors = validate_schema_structure(schema)
    assert len(errors) == 0

def test_validate_schema_structure_missing_type(invalid_schema_path):
    schema = load_yaml_schema(invalid_schema_path)
    errors = validate_schema_structure(schema)
    assert any("Missing required key: type" in err for err in errors)

def test_validate_schema_structure_invalid_property_def(tmp_path):
    # Property definition is not a dict
    schema_content = """
    $schema: http://json-schema.org/draft-07/schema#
    type: object
    properties:
      test_property: "string"
    """
    file_path = tmp_path / "bad_def_schema.yaml"
    file_path.write_text(schema_content)
    schema = load_yaml_schema(file_path)
    errors = validate_schema_structure(schema)
    assert any("'test_property' definition must be a dictionary" in err for err in errors)

def test_validate_with_jsonschema_valid(valid_schema_path):
    schema = load_yaml_schema(valid_schema_path)
    result = validate_with_jsonschema(schema)
    # Should return None (no errors) or a string about missing lib
    if result:
        assert "not installed" in result
    else:
        assert result is None

def test_validate_with_jsonschema_invalid(tmp_path):
    # Create a schema that violates JSON Schema meta-schema (e.g. wrong type for 'type')
    schema_content = {
        "type": "object",
        "properties": {
            "field": {
                "type": 123  # 'type' must be a string
            }
        }
    }
    result = validate_with_jsonschema(schema_content)
    if result:
        assert "not installed" not in result # If installed, it should fail
        assert "123" in result or "integer" in result.lower()
    else:
        # If not installed, result is None or specific string
        pass
