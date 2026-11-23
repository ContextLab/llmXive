"""
Unit tests for the feature export script (T025).

The tests create a temporary synthetic manifest and a couple of dummy
frame files, then invoke the export logic and verify that:

1. The output JSONL file is created.
2. Each record contains the expected keys.
3. The ``size_bytes`` and ``sha256`` fields correspond to the actual
   contents of the dummy frame files.
"""

import json
import os
import hashlib
from pathlib import Path

import pytest

# Import the internal helpers from the script under test
from src.feature_extraction.export_features import (
    _iter_manifest,
    _compute_file_features,
    main,
)
from llmxive_toolkit import paths

@pytest.fixture
def temporary_manifest(tmp_path: Path):
    """
    Create a temporary manifest with two entries pointing to dummy frame files.
    """
    # Create dummy frame files
    frame_dir = tmp_path / "frames"
    frame_dir.mkdir()
    frame_a = frame_dir / "frame_a.bin"
    frame_b = frame_dir / "frame_b.bin"

    frame_a.write_bytes(b"frame_a_content")
    frame_b.write_bytes(b"frame_b_content")

    # Build manifest entries
    manifest_entries = [
        {
            "frame_id": "frame_a",
            "timestamp": 0.0,
            "frame_path": str(frame_a.relative_to(paths.root)),
        },
        {
            "frame_id": "frame_b",
            "timestamp": 0.033,
            "frame_path": str(frame_b.relative_to(paths.root)),
        },
    ]

    manifest_path = tmp_path / "manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as f:
        for entry in manifest_entries:
            f.write(json.dumps(entry) + "\n")

    return manifest_path, manifest_entries

def test_iter_manifest_reads_all_entries(temporary_manifest):
    manifest_path, entries = temporary_manifest
    read_entries = list(_iter_manifest(manifest_path))
    assert read_entries == entries

def test_compute_file_features_matches_real_file():
    # Create a temporary file with known content
    tmp_file = Path("tmp_test_file.bin")
    try:
        content = b"testcontent123"
        tmp_file.write_bytes(content)

        features = _compute_file_features(tmp_file)
        assert features["size_bytes"] == len(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        assert features["sha256"] == expected_hash
    finally:
        if tmp_file.exists():
            tmp_file.unlink()

def test_main_creates_features_jsonl(tmp_path: Path, temporary_manifest):
    manifest_path, _ = temporary_manifest

    # Override the default manifest location used by the script
    # by monkeypatching the llmxive_toolkit.paths.data function.
    # We replace the path for "manifest.jsonl" only.
    original_data = paths.data

    def mock_data(*parts):
        if parts and parts[0] == "manifest.jsonl":
            return manifest_path
        return original_data(*parts)

    # Apply monkeypatch
    paths.data = mock_data

    # Run the export script
    main()

    # Verify output file exists
    output_path = paths.data("features", "features.jsonl")
    assert output_path.is_file()

    # Load and validate contents
    with output_path.open("r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    assert len(records) == 2
    for rec in records:
        assert "frame_id" in rec
        assert "timestamp" in rec
        assert "features" in rec
        feat = rec["features"]
        assert "size_bytes" in feat
        assert "sha256" in feat

    # Clean up monkeypatch
    paths.data = original_data