import json
from pathlib import Path

import pytest
import yaml

from src.utils import save_json, get_logger


def test_save_json_writes_file(tmp_path: Path):
    """Ensure that ``save_json`` creates a file with the correct content."""
    data = {"alpha": 1, "beta": [2, 3]}
    out_file = tmp_path / "out.json"

    # No schema supplied – just write.
    save_json(data, out_file)

    assert out_file.is_file(), "JSON file was not created"
    with out_file.open() as f:
        loaded = json.load(f)
    assert loaded == data, "Saved JSON does not match input data"


def test_save_json_with_schema_validation(tmp_path: Path):
    """Validate that ``save_json`` respects a provided JSON schema."""
    # Define a simple schema (YAML format, as used in the contracts directory).
    schema = {
        "type": "object",
        "properties": {
            "value": {"type": "integer"}
        },
        "required": ["value"]
    }
    schema_path = tmp_path / "schema.yaml"
    with schema_path.open("w") as sf:
        yaml.safe_dump(schema, sf)

    valid_obj = {"value": 42}
    valid_out = tmp_path / "valid.json"
    # Should succeed without raising.
    save_json(valid_obj, valid_out, schema_path)

    # Verify the file was written correctly.
    with valid_out.open() as f:
        assert json.load(f) == valid_obj

    # Now an invalid object – should raise a jsonschema.ValidationError.
    invalid_obj = {"value": "not an integer"}
    invalid_out = tmp_path / "invalid.json"
    with pytest.raises(Exception):
        save_json(invalid_obj, invalid_out, schema_path)