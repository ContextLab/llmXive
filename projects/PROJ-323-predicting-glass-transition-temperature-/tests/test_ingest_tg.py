"""
Unit tests for the ``code.ingest_tg`` module.

The tests verify that:
* The checksum loading logic raises ``FileNotFoundError`` when the
  ``checksums.json`` file is absent.
* A checksum mismatch raises ``ValueError``.
* Successful download writes the file to the expected location and
  records a provenance entry.
"""

import json
import hashlib
from pathlib import Path
from unittest import mock

import pytest

# Import the module under test
from code.ingest_tg import (
    _sha256_checksum,
    _load_checksums,
    main,
    CHECKSUM_KEY,
)

# Helper to compute a checksum for a given byte string
def _calc(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def temp_checksums(tmp_path):
    """Create a temporary ``checksums.json`` file."""
    checksums_path = tmp_path / "checksums.json"
    # Dummy checksum; will be overwritten in each test as needed
    checksums_path.write_text(json.dumps({CHECKSUM_KEY: "dummy"}))
    return checksums_path


def test_load_checksums_missing(tmp_path, monkeypatch):
    """``_load_checksums`` should raise if the file does not exist."""
    # Point the ``paths.data`` helper to the temporary directory
    from llmxive_toolkit import paths

    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path.joinpath(*parts))
    with pytest.raises(FileNotFoundError):
        _load_checksums()


def test_checksum_mismatch(tmp_path, monkeypatch):
    """A mismatched checksum must raise ``ValueError``."""
    # Prepare a fake checksums file with a known value
    checksums_path = tmp_path / "checksums.json"
    fake_content = b"polymer_id,smiles,experimental_tg\n1,CCO,350"
    correct_checksum = _calc(fake_content)
    wrong_checksum = "0" * 64
    checksums_path.write_text(json.dumps({CHECKSUM_KEY: correct_checksum}))
    # Patch ``paths.data`` to locate our temporary files
    from llmxive_toolkit import paths

    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path.joinpath(*parts))

    # Mock ``requests.get`` to return the fake content
    mock_response = mock.Mock()
    mock_response.content = fake_content
    mock_response.raise_for_status = mock.Mock()
    with mock.patch("requests.get", return_value=mock_response):
        # Overwrite the checksum in the file to be wrong
        checksums_path.write_text(json.dumps({CHECKSUM_KEY: wrong_checksum}))
        with pytest.raises(ValueError, match="Checksum mismatch"):
            main()


def test_successful_download_and_provenance(tmp_path, monkeypatch):
    """Successful download writes the CSV and creates a provenance entry."""
    fake_content = b"polymer_id,smiles,experimental_tg\n1,CCO,350"
    expected_checksum = _calc(fake_content)

    # Create a correct checksums file
    checksums_path = tmp_path / "checksums.json"
    checksums_path.write_text(json.dumps({CHECKSUM_KEY: expected_checksum}))

    # Patch ``paths.data`` and ``paths.outputs`` to use the temporary directory
    from llmxive_toolkit import paths

    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path.joinpath(*parts))
    monkeypatch.setattr(paths, "outputs", lambda *parts: tmp_path.joinpath(*parts))

    # Mock ``requests.get`` to return the fake CSV content
    mock_response = mock.Mock()
    mock_response.content = fake_content
    mock_response.raise_for_status = mock.Mock()
    with mock.patch("requests.get", return_value=mock_response):
        # Run the ingestion script
        main()

    # Verify that the CSV was written to the expected location
    tg_path = tmp_path / "raw" / "tg_dataset.csv"
    assert tg_path.is_file()
    assert tg_path.read_bytes() == fake_content

    # Verify provenance log entry
    ssot_path = tmp_path / "logs" / "ssot_log.jsonl"
    assert ssot_path.is_file()
    lines = ssot_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["artifact_path"].endswith(str(tg_path))
    assert entry["checksum"] == expected_checksum
    assert entry["generated_by"] == "ingest_tg.py"