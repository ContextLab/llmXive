"""
Unit test for the HCP data fetching functionality.
"""
import json
import hashlib
from pathlib import Path
import pytest
import requests

# Import the functions under test
from data.loader import fetch_hcp_data, _load_checksums, _load_manifest

# Use a subject ID known to exist in the OpenNeuro HCP S1200 dataset.
SUBJECT_ID = "100206"


def compute_sha256(file_path: Path) -> str:
    """Utility to compute the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def test_fetch_hcp_data_downloads_and_records(tmp_path, monkeypatch):
    """
    Test that `fetch_hcp_data` downloads files, records checksums, and updates manifest.
    """
    from llmxive_toolkit import paths

    def data_override(*parts):
        return Path(tmp_path, *parts)

    monkeypatch.setattr(paths, "data", data_override)
    monkeypatch.chdir(tmp_path)

    target_dir = fetch_hcp_data(SUBJECT_ID)

    fmri_filename = f"sub-{SUBJECT_ID}_task-rest_bold.dtseries.nii"
    behav_filename = f"sub-{SUBJECT_ID}_behav.json"

    fmri_path = target_dir / fmri_filename
    behav_path = target_dir / behav_filename

    assert fmri_path.is_file()
    assert behav_path.is_file()
    assert fmri_path.stat().st_size > 0
    assert behav_path.stat().st_size > 0

    checksums = _load_checksums()
    rel_fmri = str(fmri_path.relative_to(Path.cwd()))
    rel_behav = str(behav_path.relative_to(Path.cwd()))
    assert rel_fmri in checksums
    assert rel_behav in checksums
    assert checksums[rel_fmri] == compute_sha256(fmri_path)
    assert checksums[rel_behav] == compute_sha256(behav_path)

    manifest = _load_manifest()
    assert SUBJECT_ID in manifest


def test_fetch_hcp_data_failure_raises_exception(tmp_path, monkeypatch):
    """
    Verify that `fetch_hcp_data` fails loudly when the server returns a 404 or 500.
    """
    from llmxive_toolkit import paths

    def data_override(*parts):
        return Path(tmp_path, *parts)

    monkeypatch.setattr(paths, "data", data_override)
    monkeypatch.chdir(tmp_path)

    # Mock requests.get to return a 404 response
    def mock_get(*args, **kwargs):
        response = requests.Response()
        response.status_code = 404
        return response

    monkeypatch.setattr(requests, "get", mock_get)

    with pytest.raises(requests.exceptions.HTTPError):
        fetch_hcp_data("non_existent_subject")