import json
import pytest
from pathlib import Path
import yaml

# Import schema validation logic
from src.utils.validators import validate_json_schema

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

@pytest.fixture
def schema():
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def test_schema_exists():
    assert SCHEMA_PATH.exists(), "Schema file must exist"

def test_schema_structure(schema):
    assert "type" in schema
    assert schema["type"] == "object"
    assert "required" in schema
    assert "properties" in schema

def test_record_validation(schema):
    valid_record = {
        "sequence_id": "test-123",
        "tokens": ["token1", "token2"],
        "source": "gsm8k",
        "validity": True,
        "reason": "matched",
        "metadata": {}
    }
    validate_json_schema(valid_record, schema)

def test_record_missing_field(schema):
    invalid_record = {
        "sequence_id": "test-123",
        "tokens": ["token1"],
        # Missing source
        "validity": True,
        "reason": "matched"
    }
    with pytest.raises(ValueError):
        validate_json_schema(invalid_record, schema)

def test_record_wrong_type(schema):
    invalid_record = {
        "sequence_id": "test-123",
        "tokens": "not-a-list",
        "source": "gsm8k",
        "validity": True,
        "reason": "matched"
    }
    with pytest.raises(ValueError):
        validate_json_schema(invalid_record, schema)
