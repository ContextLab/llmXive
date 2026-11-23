"""
Tests for the synthetic data loader and validator.
"""

import json
import pathlib
from pathlib import Path

import pytest

from code.src.data import loader, validator
from llmxive_toolkit import paths

def test_generate_and_validate(tmp_path, monkeypatch):
    """
    Ensure that the generator creates the expected number of records
    and that the validator accepts a correct record while rejecting a
    malformed one.
    """
    # Use a temporary output location to avoid polluting the repository
    out_jsonl = tmp_path / "synthetic_records.jsonl"
    out_checksum = tmp_path / "checksums.json"

    # Monkey‑patch paths.data to point to the temp dir
    def mock_data(*parts):
        return tmp_path / Path(*parts)

    def mock_code(*parts):
        return paths.code(*parts)

    monkeypatch.setattr("code.src.data.loader.paths.data", mock_data)
    monkeypatch.setattr("code.src.data.loader.paths.code", mock_code)

    # Run the generation
    loader.main()

    # Verify files exist
    assert out_jsonl.exists(), f"Expected {out_jsonl} to exist"
    assert out_checksum.exists(), f"Expected {out_checksum} to exist"

    # Load records and validate them
    with out_jsonl.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 20 * 10, f"Expected 200 records, got {len(lines)}"

    # Pick a valid record and ensure validator passes
    valid_record = json.loads(lines[0])
    validator.validate_record(valid_record)

    # Create an invalid record (missing trial_success) and check the error
    invalid = valid_record.copy()
    del invalid["trial_success"]
    with pytest.raises(RuntimeError) as excinfo:
        validator.validate_record(invalid)
    assert "Missing variable 'trial_success'" in str(excinfo.value)
