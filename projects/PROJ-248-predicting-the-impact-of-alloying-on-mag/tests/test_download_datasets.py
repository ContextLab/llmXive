"""
Test suite for the ``code/download_datasets.py`` script.

The tests verify that the script:
1. Executes without raising an exception.
2. Produces the three expected artefacts under the ``data/`` directory.
3. Writes non‑empty files and records a valid SHA‑256 checksum in the
   manifest.
"""

import json
import hashlib
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the module under test.
from code import download_datasets

@pytest.fixture(scope="module")
def run_download():
    """Run the download script once for the whole test module."""
    download_datasets.main()
    # Return the paths for convenience.
    return {
        "raw_mp": paths.data("raw_mp.jsonl"),
        "raw_oqmd": paths.data("raw_oqmd.csv"),
        "manifest": paths.data("data_sources.yaml"),
    }

def _compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def test_artifacts_exist(run_download):
    """All three artefacts must exist after the download step."""
    assert run_download["raw_mp"].exists(), "raw_mp.jsonl was not created"
    assert run_download["raw_oqmd"].exists(), "raw_oqmd.csv was not created"
    assert run_download["manifest"].exists(), "data_sources.yaml was not created"

def test_raw_mp_not_empty(run_download):
    """The Materials Project JSON‑lines file must contain at least one record."""
    path = run_download["raw_mp"]
    # Count non‑blank lines.
    line_count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    assert line_count > 0, "raw_mp.jsonl is empty"

    # Verify that each line is valid JSON.
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        # At minimum we expect a ``magnetic_type`` field that is not ``NM``.
        assert obj.get("magnetic_type") != "NM", "Found a non‑magnetic entry in raw_mp.jsonl"

def test_raw_oqmd_not_empty(run_download):
    """The OQMD CSV must be non‑empty and contain a header line."""
    path = run_download["raw_oqmd"]
    size = path.stat().st_size
    assert size > 0, "raw_oqmd.csv is empty"
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    assert "," in first_line, "raw_oqmd.csv does not appear to be a CSV file"

def test_manifest_checksums(run_download):
    """The manifest must contain SHA‑256 checksums that match the actual files."""
    manifest_path = run_download["manifest"]
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    mp_info = manifest.get("materials_project", {})
    oqmd_info = manifest.get("oqmd", {})

    # Verify that the recorded checksums correspond to the real files.
    assert mp_info.get("sha256") == _compute_sha256(run_download["raw_mp"])
    assert oqmd_info.get("sha256") == _compute_sha256(run_download["raw_oqmd"])