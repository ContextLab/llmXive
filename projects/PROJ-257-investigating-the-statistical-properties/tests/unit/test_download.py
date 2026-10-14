"""
Unit tests for the GWTC download module.
"""

import json
import pathlib

import pytest
import requests_mock

from src.data.download import download_all, _doi_to_record_id, _select_file_info

# Mock Zenodo API responses
@pytest.fixture
def mock_zenodo(requests_mock):
    # Example minimal metadata with a single HDF5 file entry
    record_meta = {
        "id": 123456,
        "files": [
            {
                "key": "gwtc_sample.h5",
                "links": {"download": "https://example.org/gwtc_sample.h5"},
            }
        ],
    }
    # Mock the metadata endpoint
    requests_mock.get(
        "https://zenodo.org/api/records/123456", json=record_meta, status_code=200
    )
    # Mock the file download (small dummy HDF5 content)
    dummy_h5 = b"\x89HDF\r\n\x1a\n\x00\x00\x00\x00"
    requests_mock.get("https://example.org/gwtc_sample.h5", content=dummy_h5)

def test_doi_to_record_id():
    assert _doi_to_record_id("10.5281/zenodo.3966973") == "3966973"

def test_select_file_info():
    meta = {
        "id": 999,
        "files": [
            {"key": "not_hdf5.txt", "links": {"download": "https://example.org/1.txt"}},
            {"key": "data.h5", "links": {"download": "https://example.org/data.h5"}},
        ],
    }
    fname, url = _select_file_info(meta)
    assert fname == "data.h5"
    assert url == "https://example.org/data.h5"

def test_download_all(mock_zenodo, tmp_path, monkeypatch):
    # Redirect the data directory to a temporary location
    from llmxive_toolkit import paths

    monkeypatch.setattr(paths, "data", lambda *parts: pathlib.Path(tmp_path, *parts))

    result = download_all()
    # Two datasets are configured; both should map to the same dummy file
    assert isinstance(result, dict)
    assert len(result) == 2
    for p in result.values():
        assert p.is_file()
    # Verify that checksums manifest was written
    manifest_path = pathlib.Path(tmp_path, "raw", "checksums.json")
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text())
    assert set(manifest.keys()) == {"gwtc1.h5", "gwtc2.h5"}