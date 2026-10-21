"""
Unit tests for ``code.data.loader.load_refs``.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the function under test
from code.data.loader import load_refs, NIST_REFS_PATH


def test_load_valid():
    """The curated JSON file should load and contain three entries."""
    refs = load_refs()
    assert isinstance(refs, list)
    assert len(refs) == 3

    solvents = {r["solvent"] for r in refs}
    assert solvents == {"water", "ethanol", "acetone"}

    for entry in refs:
        # basic sanity checks on types
        assert isinstance(entry["solvent"], str)
        assert isinstance(entry["temperature"], (int, float))
        assert isinstance(entry["value"], (int, float))
        assert isinstance(entry["source"], str)


def test_missing_file():
    """A missing file must raise FileNotFoundError."""
    missing_path = Path("nonexistent_nist_refs.json")
    with pytest.raises(FileNotFoundError):
        load_refs(missing_path)


def test_malformed_schema():
    """Entries that do not conform to the schema raise ValueError."""
    malformed_data = [
        {"solvent": "water", "temperature": 298.15, "value": 2.3e-9}
        # ``source`` key is omitted deliberately
    ]

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
        json.dump(malformed_data, tmp)
        tmp_path = Path(tmp.name)

    try:
        with pytest.raises(ValueError) as excinfo:
            load_refs(tmp_path)
        assert "Missing required keys" in str(excinfo.value)
    finally:
        os.unlink(tmp_path)


def test_checksum_matches():
    """The committed .sha256 file must match the actual nist_refs.json."""
    import hashlib

    refs_path = Path(NIST_REFS_PATH)
    checksum_path = refs_path.parent / "nist_refs.json.sha256"
    assert refs_path.exists(), f"missing curated file {refs_path}"
    assert checksum_path.exists(), f"missing checksum file {checksum_path}"

    actual = hashlib.sha256(refs_path.read_bytes()).hexdigest()
    recorded = checksum_path.read_text().split()[0].strip()
    assert actual == recorded, (
        f"checksum mismatch: file hashes to {actual} but "
        f"{checksum_path} records {recorded}"
    )