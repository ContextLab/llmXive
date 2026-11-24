"""
Unit test for the HCP data fetching functionality.

This test verifies that `fetch_hcp_data` downloads the expected
resting‑state fMRI CIFTI file and the behavioral JSON, records SHA‑256
checksums, and updates the manifest correctly.
"""
import json
import hashlib
from pathlib import Path

import pytest

# Import the function under test
from data.loader import fetch_hcp_data, _load_checksums, _load_manifest

# Use a subject ID known to exist in the OpenNeuro HCP S1200 dataset.
# The HCP subject "100206" is part of the public release and includes both
# the resting‑state CIFTI file and a behavioral JSON with a CAQ field.
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
    Test that `fetch_hcp_data`:
    1. Downloads the fMRI and behavioral files.
    2. Writes non‑empty files to disk.
    3. Records SHA‑256 checksums for both files in `data/checksums.json`.
    4. Updates `data/raw/manifest.json` with the subject ID.
    """
    # ------------------------------------------------------------------
    # Redirect all data writes to a temporary directory to keep the repo clean.
    # ------------------------------------------------------------------
    # Monkey‑patch the llmxive_toolkit.paths.data() helper so that every
    # call returns a location inside the temporary directory.
    from llmxive_toolkit import paths

    def data_override(*parts):
        """Return a Path rooted at the temporary directory."""
        return Path(tmp_path, *parts)

    monkeypatch.setattr(paths, "data", data_override)

    # Change the current working directory to the temporary directory.
    # This ensures that relative paths used by the loader (e.g. for
    # checksums.json) also point inside the temp area.
    monkeypatch.chdir(tmp_path)

    # ------------------------------------------------------------------
    # Execute the fetch routine.
    # ------------------------------------------------------------------
    target_dir = fetch_hcp_data(SUBJECT_ID)

    # Expected file names based on the implementation in `loader.py`.
    fmri_filename = f"sub-{SUBJECT_ID}_task-rest_bold.dtseries.nii"
    behav_filename = f"sub-{SUBJECT_ID}_behav.json"

    fmri_path = target_dir / fmri_filename
    behav_path = target_dir / behav_filename

    # ------------------------------------------------------------------
    # Verify that the files were created and are non‑empty.
    # ------------------------------------------------------------------
    assert fmri_path.is_file(), f"fMRI file not found at {fmri_path}"
    assert behav_path.is_file(), f"Behavioral JSON not found at {behav_path}"
    assert fmri_path.stat().st_size > 0, "Downloaded fMRI file is empty"
    assert behav_path.stat().st_size > 0, "Downloaded behavioral JSON is empty"

    # ------------------------------------------------------------------
    # Verify that SHA‑256 checksums were recorded.
    # ------------------------------------------------------------------
    checksums = _load_checksums()
    rel_fmri = str(fmri_path.relative_to(Path.cwd()))
    rel_behav = str(behav_path.relative_to(Path.cwd()))
    assert rel_fmri in checksums, "fMRI checksum missing from checksums.json"
    assert rel_behav in checksums, "Behavioral JSON checksum missing from checksums.json"

    # Cross‑check that the stored checksum matches the file content.
    assert checksums[rel_fmri] == compute_sha256(fmri_path)
    assert checksums[rel_behav] == compute_sha256(behav_path)

    # ------------------------------------------------------------------
    # Verify that the manifest contains the fetched subject ID.
    # ------------------------------------------------------------------
    manifest = _load_manifest()
    assert SUBJECT_ID in manifest, "Subject ID not recorded in manifest.json"