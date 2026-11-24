"""
Unit tests for the GWTC download module.
"""

import json
import pathlib

import pytest
import requests_mock

from src.data.download import download_all, _doi_to_record_id, _select_file_info, DATASETS

@pytest.fixture
def mock_zenodo(requests_mock):
    """
    Mock Zenodo API responses for the specific record IDs used in DATASETS.
    """
    for doi, target_name in DATASETS:
        record_id = doi.rsplit(".", 1)[-1]
        record_meta = {
            "id": int(record_id),
            "files": [
                {
                    "key": target_name,
                    "links": {"download": f"https://example.org/{target_name}"},
                }
            ],
        }
        # Mock the metadata endpoint
        requests_mock.get(
            f"https://zenodo.org/api/records/{record_id}", json=record_meta, status_code=200
        )
        # Mock the file download
        dummy_h5 = b"\x89HDF\r\n\x1a\n\x00\x00\x00\x00"
        requests_mock.get(f"https://example.org/{target_name}", content=dummy_h5)

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
    """
    Verify that download_all fetches all configured datasets and writes the manifest.
    """
    from llmxive_toolkit import paths

    # Redirect paths.data to a temporary directory
    monkeypatch.setattr(paths, "data", lambda *parts: pathlib.Path(tmp_path, *parts))

    result = download_all()
    
    assert isinstance(result, dict)
    assert len(result) == len(DATASETS)
    for target_name, _ in DATASETS:
        assert target_name in result
        assert result[target_name].is_file()
    
    # Verify that checksums manifest was written
    manifest_path = pathlib.Path(tmp_path, "raw", "checksums.json")
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text())
    assert set(manifest.keys()) == {target_name for _, target_name in DATASETS}