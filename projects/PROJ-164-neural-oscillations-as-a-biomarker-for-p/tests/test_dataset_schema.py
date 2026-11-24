"""Tests for T006: base data schema definition (FR-006)."""
import pathlib

import yaml
from jsonschema import Draft7Validator

SCHEMA_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "specs" / "001-neural-oscillations-tDCS-biomarker"
    / "contracts" / "dataset.schema.yaml"
)

def load_schema():
    with open(SCHEMA_PATH) as f:
        return yaml.safe_load(f)

def valid_record():
    return {
        "subject_id": "sub-001",
        "channel": "C3",
        "time": 0.5,
        "voltage": -12.3,
        "condition": "anodal",
    }

def test_schema_file_exists():
    assert SCHEMA_PATH.is_file()

def test_required_fields_match_spec():
    schema = load_schema()
    assert set(schema["required"]) == {
        "subject_id", "channel", "time", "voltage", "condition"
    }
    assert set(schema["properties"].keys()) == set(schema["required"])

def test_no_extraneous_fields_like_mode_flag():
    schema = load_schema()
    assert "mode_flag" not in schema["properties"]

def test_valid_record_passes():
    validator = Draft7Validator(load_schema())
    assert not list(validator.iter_errors(valid_record()))

def test_missing_required_field_fails():
    validator = Draft7Validator(load_schema())
    record = valid_record()
    del record["voltage"]
    assert list(validator.iter_errors(record))

def test_bad_condition_fails():
    validator = Draft7Validator(load_schema())
    record = valid_record()
    record["condition"] = "unknown-condition"
    assert list(validator.iter_errors(record))

def test_bad_subject_id_fails():
    validator = Draft7Validator(load_schema())
    record = valid_record()
    record["subject_id"] = "subject_1"
    assert list(validator.iter_errors(record))

def test_negative_time_fails():
    validator = Draft7Validator(load_schema())
    record = valid_record()
    record["time"] = -1.0
    assert list(validator.iter_errors(record))

def test_additional_properties_rejected():
    validator = Draft7Validator(load_schema())
    record = valid_record()
    record["mode_flag"] = "Primary"
    assert list(validator.iter_errors(record))