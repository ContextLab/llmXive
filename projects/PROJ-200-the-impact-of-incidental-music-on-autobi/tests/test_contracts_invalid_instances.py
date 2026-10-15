import json
import pathlib

import pytest
from jsonschema import Draft7Validator, ValidationError

CONTRACTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "contracts"

@pytest.fixture(scope="module")
def dataset_schema():
    schema_path = CONTRACTS_DIR / "dataset.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_invalid_memory_cue_fails(dataset_schema):
    # matched_track_id must be string or null; providing an integer should fail
    invalid_instance = {
        "cue_id": "c1",
        "user_id": "u1",
        "cue_text": "some cue",
        "vividness": 3,
        "valence": 0,
        "matched_track_id": 123,  # invalid type
        "match_confidence": 0.8,
    }
    validator = Draft7Validator(dataset_schema["definitions"]["MemoryCue"])
    with pytest.raises(ValidationError):
        validator.validate(invalid_instance)