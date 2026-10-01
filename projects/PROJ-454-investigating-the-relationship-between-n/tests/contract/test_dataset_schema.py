import pytest
import json
import yaml
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError

# Path to the schema
SCHEMA_PATH = Path(__file__).parent.parent.parent / "specs" / "001-neural-entropy-cognitive-flexibility" / "contracts" / "dataset.schema.yaml"

@pytest.fixture
def schema():
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def sample_dataset_metadata():
    """Valid sample dataset metadata matching the schema."""
    return {
        "id": "ds003104",
        "description": {
            "Name": "Test Dataset",
            "Authors": ["Test Author"],
            "License": "CC0"
        },
        "summary": {
            "subjects": 10,
            "subjectMetadata": [
                {"participantId": "sub-01", "age": 55, "sex": "M"},
                {"participantId": "sub-02", "age": 60, "sex": "F"}
            ],
            "tasks": ["rest", "task"],
            "modalities": ["eeg"],
            "size": 1024,
            "totalFiles": 5
        }
    }

@pytest.fixture
def invalid_dataset_metadata():
    """Invalid sample dataset metadata missing required fields."""
    return {
        "id": "ds003104",
        # Missing 'description' and 'summary'
    }

def test_dataset_schema_validation(schema, sample_dataset_metadata):
    """Contract test: Validate dataset metadata against schema."""
    try:
        validate(instance=sample_dataset_metadata, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Dataset metadata failed schema validation: {e.message}")

def test_schema_structure(schema):
    """Contract test: Ensure schema has required top-level keys."""
    assert "type" in schema, "Schema must define a type"
    assert "properties" in schema, "Schema must define properties"
    assert schema["type"] == "object", "Schema type must be object"

def test_dataset_schema_rejects_invalid(schema, invalid_dataset_metadata):
    """Contract test: Ensure schema rejects invalid metadata."""
    with pytest.raises(ValidationError):
        validate(instance=invalid_dataset_metadata, schema=schema)

def test_dataset_id_format(schema):
    """Contract test: Ensure dataset ID follows dsXXXXXX pattern."""
    valid_id = {"id": "ds003104", "description": {"Name": "Test"}, "summary": {"subjects": 1, "subjectMetadata": [{"participantId": "sub-01"}], "tasks": [], "modalities": []}}
    invalid_id = {"id": "dataset_123", "description": {"Name": "Test"}, "summary": {"subjects": 1, "subjectMetadata": [{"participantId": "sub-01"}], "tasks": [], "modalities": []}}
    
    validate(instance=valid_id, schema=schema)
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_id, schema=schema)