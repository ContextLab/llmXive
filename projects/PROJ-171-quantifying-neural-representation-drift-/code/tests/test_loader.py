"""
Tests for the synthetic data loader and validator.
"""

import json
import pathlib

import pytest

from src.data import loader, validator
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

    # Monkey‑patch the paths used inside the loader to point to the temp dir
    monkeypatch.setattr(
        loader,
        "paths",
        type(
            "TmpPaths",
            (),
            {
                "data": lambda *parts: pathlib.Path(tmp_path, *parts),
                "code": lambda *parts: pathlib.Path(tmp_path, *parts),
            },
        ),
    )
    # Run the generation
    loader.main()

    # Verify files exist
    assert out_jsonl.exists()
    assert out_checksum.exists()

    # Load a few records and validate them
    with out_jsonl.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 20 * 10  # 20 subjects × 10 days

    # Pick a valid record and ensure validator passes
    valid_record = json.loads(lines[0])
    validator.validate_record(valid_record)

    # Create an invalid record (missing trial_success) and check the error
    invalid = valid_record.copy()
    del invalid["trial_success"]
    with pytest.raises(RuntimeError) as excinfo:
        validator.validate_record(invalid)
    assert "Missing variable 'trial_success'" in str(excinfo.value)