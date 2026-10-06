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
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. Ensure T007 or T010 has created the schema.")
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
    valid_id = {
        "id": "ds003104",
        "description": {"Name": "Test"},
        "summary": {
            "subjects": 1,
            "subjectMetadata": [{"participantId": "sub-01"}],
            "tasks": [],
            "modalities": [],
            "size": 100,
            "totalFiles": 1
        }
    }
    invalid_id = {
        "id": "dataset_123",
        "description": {"Name": "Test"},
        "summary": {
            "subjects": 1,
            "subjectMetadata": [{"participantId": "sub-01"}],
            "tasks": [],
            "modalities": [],
            "size": 100,
            "totalFiles": 1
        }
    }
    
    validate(instance=valid_id, schema=schema)
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_id, schema=schema)

def test_subject_metadata_validation(schema):
    """Contract test: Ensure subject metadata validates correctly."""
    valid_subject = {
        "id": "ds003104",
        "description": {"Name": "Test"},
        "summary": {
            "subjects": 1,
            "subjectMetadata": [
                {
                    "participantId": "sub-01",
                    "age": 50,
                    "sex": "M",
                    "handedness": "R"
                }
            ],
            "tasks": ["rest"],
            "modalities": ["eeg"],
            "size": 100,
            "totalFiles": 1
        }
    }
    invalid_subject = {
        "id": "ds003104",
        "description": {"Name": "Test"},
        "summary": {
            "subjects": 1,
            "subjectMetadata": [
                {
                    "participantId": "sub-01",
                    "age": "fifty", # Should be integer
                    "sex": "M",
                    "handedness": "R"
                }
            ],
            "tasks": ["rest"],
            "modalities": ["eeg"],
            "size": 100,
            "totalFiles": 1
        }
    }

    validate(instance=valid_subject, schema=schema)
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_subject, schema=schema)

def test_required_fields_enforcement(schema):
    """Contract test: Ensure required fields are enforced."""
    partial_data = {
        "id": "ds003104",
        "description": {"Name": "Test"},
        # Missing summary
    }
    with pytest.raises(ValidationError):
        validate(instance=partial_data, schema=schema)

def test_subject_age_type(schema):
    """Contract test: Ensure age is an integer."""
    data = {
        "id": "ds003104",
        "description": {"Name": "Test"},
        "summary": {
            "subjects": 1,
            "subjectMetadata": [{"participantId": "sub-01", "age": 25.5}], # Float not allowed
            "tasks": [],
            "modalities": [],
            "size": 100,
            "totalFiles": 1
        }
    }
    with pytest.raises(ValidationError):
        validate(instance=data, schema=schema)

def test_sex_enum(schema):
    """Contract test: Ensure sex is one of M, F, O."""
    data = {
        "id": "ds003104",
        "description": {"Name": "Test"},
        "summary": {
            "subjects": 1,
            "subjectMetadata": [{"participantId": "sub-01", "age": 25, "sex": "Unknown"}],
            "tasks": [],
            "modalities": [],
            "size": 100,
            "totalFiles": 1
        }
    }
    with pytest.raises(ValidationError):
        validate(instance=data, schema=schema)