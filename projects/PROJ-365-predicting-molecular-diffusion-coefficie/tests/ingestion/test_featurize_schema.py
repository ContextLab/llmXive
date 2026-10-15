"""
Test that the first line produced by ``code/ingestion/featurize.py`` conforms
to the JSON schema defined in ``contracts/dataset.schema.yaml`` and that the
recorded memory profile respects the SC‑005 upper bound.
"""
import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

# Helper to locate the project root (same logic as utils.config)
def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]

@pytest.fixture(scope="module")
def schema():
    schema_path = get_project_root() / "specs" / "001-predicting-molecular-diffusion-coefficie" / "contracts" / "dataset.schema.yaml"
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def first_record():
    data_path = get_project_root() / "data" / "processed" / "featurized_data.jsonl"
    # Ensure the featurization script has run; if the file is missing, the test will fail
    assert data_path.is_file(), f"Featurized data file not found at {data_path}"
    with data_path.open("r", encoding="utf-8") as f:
        line = f.readline()
        assert line, "Featurized data file is empty"
        return json.loads(line)

def test_record_schema_valid(first_record, schema):
    # jsonschema.validate will raise ValidationError if the record does not match
    try:
        validate(instance=first_record, schema=schema)
    except ValidationError as exc:
        pytest.fail(f"Record does not match schema: {exc}")

def test_memory_profile():
    mem_path = get_project_root() / "artifacts" / "reports" / "memory_profile.json"
    assert mem_path.is_file(), "Memory profile JSON not found"
    with mem_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert "peak_memory_mb" in data, "peak_memory_mb missing in memory profile"
    peak = data["peak_memory_mb"]
    assert isinstance(peak, (int, float)), "peak_memory_mb is not numeric"
    assert peak <= 7000, f"Peak memory {peak} MB exceeds the 7000 MB limit"