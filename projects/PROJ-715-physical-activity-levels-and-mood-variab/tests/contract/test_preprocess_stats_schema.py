import sys
from pathlib import Path

import yaml
import pytest

SCHEMA_PATH = Path(
    "specs/001-physical-activity-levels-and-mood-variab/contracts/preprocess_stats.schema.yaml"
)


def _load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"


def test_schema_structure():
    schema = _load_schema()
    assert schema["type"] == "object"
    props = schema["properties"]
    assert props["excluded_days_count"]["type"] == "integer"
    assert props["reason"]["type"] == "string"
    assert props["data_source_url"]["type"] == "string"
    assert set(schema["required"]) == {
        "excluded_days_count",
        "reason",
        "data_source_url",
    }
    assert schema["additionalProperties"] is False


def test_valid_document_passes():
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not available")
    schema = _load_schema()
    doc = {
        "excluded_days_count": 5,
        "reason": "n_mood_ratings < 2",
        "data_source_url": "https://osf.io/download/5b1a9f1b9ad5a10018669804/",
    }
    jsonschema.validate(doc, schema)


def test_missing_required_field_fails():
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not available")
    schema = _load_schema()
    doc = {
        "excluded_days_count": 5,
        "reason": "n_mood_ratings < 2",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, schema)