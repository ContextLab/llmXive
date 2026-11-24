"""
Unit tests for the Materials Project bulk download script (T013).
The test suite checks that:
1. The expected number of JSON files are created under ``data/raw/mp_records``.
2. Each file's SHA‑256 checksum is recorded in ``data/metadata.yaml``.
3. The top‑level field ``materials_project_status`` is set to ``AVAILABLE``.
"""
import os
import json
import hashlib
from pathlib import Path

import pytest
import yaml

from code.download_mp import download_mp_records, main

@pytest.fixture(scope="module")
def mp_api_key(monkeypatch):
    """Provide a dummy API key – the real key must be set in CI."""
    dummy_key = os.getenv("MP_API_KEY")
    if not dummy_key:
        pytest.skip("MP_API_KEY not available in the test environment")
    monkeypatch.setenv("MP_API_KEY", dummy_key)

def test_download_creates_files(mp_api_key, tmp_path, monkeypatch):
    """
    Execute the download script in a temporary project layout and verify
    that files are written and metadata is updated.
    """
    # Point the project root to a temporary directory.
    project_root = tmp_path
    monkeypatch.setattr("code.download_mp.paths.root", project_root)

    # Run the download (uses the real MP API key).
    download_mp_records(max_retries=3, seed=20231023)

    # ------------------------------------------------------------------
    # 1. Verify file count (600 total)
    # ------------------------------------------------------------------
    mp_dir = project_root / "data" / "raw" / "mp_records"
    assert mp_dir.is_dir(), "MP records directory not created"
    json_files = list(mp_dir.glob("*.json"))
    assert len(json_files) == 600, f"Expected 600 JSON files, found {len(json_files)}"

    # ------------------------------------------------------------------
    # 2. Verify checksums recorded in metadata.yaml
    # ------------------------------------------------------------------
    metadata_path = project_root / "data" / "metadata.yaml"
    assert metadata_path.is_file(), "metadata.yaml not created"

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = yaml.safe_load(f)

    # Status flag
    assert metadata.get("materials_project_status") == "AVAILABLE"

    # Checksums mapping
    mp_files = metadata.get("mp_files", {})
    assert isinstance(mp_files, dict), "mp_files entry missing or not a dict"
    assert len(mp_files) == 600, "Checksum map does not contain 600 entries"

    # Spot‑check a random file's checksum.
    sample_file = json_files[0]
    with open(sample_file, "rb") as f:
        content = f.read()
    expected_checksum = hashlib.sha256(content).hexdigest()
    rel_path = str(sample_file.relative_to(project_root))
    assert mp_files.get(rel_path) == expected_checksum

def test_main_requires_api_key(monkeypatch):
    """
    Ensure that invoking ``main()`` without an MP_API_KEY raises an error.
    """
    monkeypatch.delenv("MP_API_KEY", raising=False)
    with pytest.raises(EnvironmentError):
        main()