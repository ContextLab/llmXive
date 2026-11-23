"""
Unit test for the T003 ingestion implementation.
It verifies that ``code/ingest.py`` creates ``data/raw/dataset_manifest.json``
and that the manifest contains entries for both required OpenNeuro datasets.
The test runs against the live OpenNeuro API – no mocking is performed,
ensuring that real data is used as mandated by the project rules.
"""

import json
import os
import pathlib

from ingest import run_ingestion, get_path

def test_ingest_creates_manifest(tmp_path, monkeypatch):
    """
    Execute the ingestion pipeline in a temporary directory and
    assert that the manifest file exists and contains the expected
    structure.
    """
    # Redirect the raw, interim, and processed data directories to a temporary location.
    raw_dir = tmp_path / "raw"
    interim_dir = tmp_path / "interim"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Monkey‑patch ``get_path`` so the script writes into the temporary folders.
    def fake_get_path(key: str) -> str:
        if key == "raw":
            return str(raw_dir)
        if key == "interim":
            return str(interim_dir)
        if key == "processed":
            return str(processed_dir)
        # For any other key fall back to the real implementation.
        from config import get_path as real_get_path
        return real_get_path(key)

    monkeypatch.setattr("ingest.get_path", fake_get_path)

    # Run the ingestion (this will hit the real OpenNeuro API).
    run_ingestion()

    manifest_path = raw_dir / "dataset_manifest.json"
    assert manifest_path.is_file(), "Manifest file was not created"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # The manifest should be a list with two entries.
    assert isinstance(manifest, list), "Manifest should be a list"
    assert len(manifest) == 2, "Manifest should contain two dataset entries"

    # Verify required keys for each entry.
    required_keys = {"url", "sha256", "size_bytes", "file_count", "dataset_id"}
    for entry in manifest:
        assert required_keys.issubset(entry.keys()), f"Missing keys in manifest entry: {entry}"
        assert entry["dataset_id"] in {"ds000208", "ds003392"}, "Unexpected dataset_id"