"""
Unit tests for the GWTC download module.

The tests verify that the ``download_all`` function creates the expected
files in ``data/raw/`` and that a ``checksums.json`` manifest is written.
Because the real Zenodo endpoints are external, the tests use ``requests_mock``
to simulate the Zenodo API responses and file streams.
"""

import json
from pathlib import Path

import pytest
import requests
import requests_mock

from src.data.download import download_all, DATASETS
from llmxive_toolkit import paths

# Helper to create a small binary payload for the mocked file download
def _dummy_file_content() -> bytes:
    return b"dummy hdf5 content for testing"

@pytest.fixture
def mock_zenodo():
    with requests_mock.Mocker() as m:
        for doi, target_name in DATASETS:
            record_id = doi.rsplit(".", 1)[-1]
            # Mock metadata endpoint
            meta_url = f"https://zenodo.org/api/records/{record_id}"
            meta_response = {
                "id": int(record_id),
                "files": [
                    {
                        "key": f"{target_name}",
                        "links": {"download": f"https://zenodo.org/records/{record_id}/files/{target_name}?download=1"},
                    }
                ],
            }
            m.get(meta_url, json=meta_response)

            # Mock file download endpoint
            file_url = f"https://zenodo.org/records/{record_id}/files/{target_name}?download=1"
            m.get(file_url, content=_dummy_file_content())
        yield m

def test_download_all_creates_files_and_manifest(tmp_path, mock_zenodo, monkeypatch):
    # Redirect the data directory to a temporary location
    monkeypatch.setattr(paths, "data", lambda *parts: Path(tmp_path, *parts))

    # Run the download routine
    result = download_all()

    # Verify that both files exist
    for _, target_name in DATASETS:
        expected_path = Path(tmp_path, "raw", target_name)
        assert expected_path.is_file()
        assert result[target_name] == expected_path

    # Verify checksums.json exists and contains entries for both files
    checksum_path = Path(tmp_path, "raw", "checksums.json")
    assert checksum_path.is_file()
    with open(checksum_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert set(manifest.keys()) == {name for _, name in DATASETS}
    # Ensure the stored hash matches the SHA‑256 of the dummy content
    import hashlib

    expected_hash = hashlib.sha256(_dummy_file_content()).hexdigest()
    for hash_val in manifest.values():
        assert hash_val == expected_hash