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
        pytest.skip("Schema file not found")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def sample_dataset_metadata():
    return {
        "id": "ds003104",
        "description": {
            "Name": "Test Dataset",
            "Authors": ["Test Author"]
        },
        "summary": {
            "subjects": 10,
            "subjectMetadata": [
                {"participantId": "sub-01", "age": 55, "sex": "M"},
                {"participantId": "sub-02", "age": 60, "sex": "F"}
            ],
            "tasks": ["rest", "task"],
            "modalities": ["eeg"]
        }
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
