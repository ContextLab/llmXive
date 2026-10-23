"""
Unit tests for ``code.data.loader.load_refs``.
"""

import json
import os
import tempfile
import hashlib
from pathlib import Path

import pytest
from llmxive_toolkit import paths

# Import the function under test
from code.data.loader import load_refs

def test_load_valid():
    """The curated JSON file should load and contain three entries with the correct schema."""
    refs = load_refs()
    assert isinstance(refs, list)
    assert len(refs) == 3

    solvents = {r["solvent"] for r in refs}
    assert solvents == {"water", "ethanol", "acetone"}

    for entry in refs:
        assert isinstance(entry["solvent"], str)
        assert isinstance(entry["temperature_K"], (int, float))
        assert isinstance(entry["D_exp_m2_s"], (int, float))
        assert isinstance(entry["source"], str)

def test_missing_file():
    """A missing file must raise FileNotFoundError."""
    missing_path = Path("nonexistent_nist_refs.json")
    with pytest.raises(FileNotFoundError):
        load_refs(missing_path)

def test_malformed_schema():
    """Entries that do not conform to the schema raise ValueError."""
    malformed_data = [
        {
            "solvent": "water",
            "temperature_K": 298,
            # 'D_exp_m2_s' key is omitted deliberately
            "source": "NIST"
        }
    ]

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
        json.dump(malformed_data, tmp)
        tmp_path = Path(tmp.name)

    try:
        with pytest.raises(ValueError) as excinfo:
            load_refs(tmp_path)
        assert "Missing required keys" in str(excinfo.value) or "Schema validation error" in str(excinfo.value)
    finally:
        os.unlink(tmp_path)

def test_checksum_matches():
    """The committed .sha256 file must match the actual nist_refs.json."""
    refs_path = paths.data("raw", "nist_refs.json")
    checksum_path = refs_path.with_name(refs_path.name + ".sha256")
    
    assert refs_path.exists(), f"missing curated file {refs_path}"
    assert checksum_path.exists(), f"missing checksum file {checksum_path}"

    actual_hash = hashlib.sha256(refs_path.read_bytes()).hexdigest()
    # Checksum file format: "<hash>  <filename>"
    recorded_hash = checksum_path.read_text().split()[0].strip()
    
    assert actual_hash == recorded_hash, (
        f"checksum mismatch: file hashes to {actual_hash} but "
        f"{checksum_path} records {recorded_hash}"
    )