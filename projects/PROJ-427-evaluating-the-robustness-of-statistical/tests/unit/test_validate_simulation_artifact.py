"""
Unit tests for the `validate_and_record_artifact` function in `code/simulate.py`.
The test creates a temporary valid result JSON file, runs validation, and checks
that the state file is updated with the correct checksum and validation flag.
"""

import json
import hashlib
import os
import tempfile
from pathlib import Path

import pytest

# Import the function from the simulate module
from simulate import validate_and_record_artifact


@pytest.fixture
def valid_result(tmp_path: Path) -> Path:
    """Create a minimal valid result JSON adhering to the result schema."""
    data = {
        "p_value": 0.123,
        "ci_lower": -0.5,
        "ci_upper": 0.7,
        "effect_size": 0.42,
        "type_i_flag": False,
    }
    result_path = tmp_path / "result.json"
    with result_path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return result_path


def test_validate_and_record_artifact(valid_result: Path, tmp_path: Path):
    """Validate that the artifact is checked, checksum computed, and state updated."""
    # Use a temporary state file
    state_path = tmp_path / "simulation_artifacts.yaml"

    # Run validation
    validate_and_record_artifact(
        artifact_path=str(valid_result),
        schema_path="contracts/result.schema.yaml",
        state_path=str(state_path),
    )

    # Verify state file exists and contains the expected entry
    assert state_path.is_file()
    with state_path.open("rt", encoding="utf-8") as f:
        state_data = yaml.safe_load(f)

    rel_path = str(valid_result)
    assert rel_path in state_data
    entry = state_data[rel_path]
    # Compute expected checksum independently
    expected_checksum = hashlib.sha256(valid_result.read_bytes()).hexdigest()
    assert entry["checksum"] == expected_checksum
    assert entry["validated"] is True

# Ensure that a missing required key raises a ValueError
def test_missing_key_raises(tmp_path: Path):
    bad_data = {
        "p_value": 0.2,
        # ci_lower omitted on purpose
        "ci_upper": 1.0,
        "effect_size": 0.1,
        "type_i_flag": True,
    }
    bad_path = tmp_path / "bad.json"
    with bad_path.open("w", encoding="utf-8") as f:
        json.dump(bad_data, f)

    state_path = tmp_path / "state.yaml"
    with pytest.raises(ValueError):
        validate_and_record_artifact(
            artifact_path=str(bad_path),
            schema_path="contracts/result.schema.yaml",
            state_path=str(state_path),
        )