"""
Integration tests for the Data Exporter (T017).

Verifies:
1. Labeled frames are correctly copied to data/raw/.
2. Manifest.jsonl is generated with correct structure and counts.
3. File hashes are computed correctly.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from src.data_synthesis.exporter import export_raw_data, generate_manifest, compute_file_hash
from src.data_synthesis.visual_labeler import FrameLabel
from src.data_synthesis.models import SyntheticVideoFrame


@pytest.fixture
def temp_export_dirs():
    """Create temporary source and target directories for export tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        source_dir = Path(tmp_dir) / "source"
        target_dir = Path(tmp_dir) / "target"
        source_dir.mkdir()
        target_dir.mkdir()
        
        # Create a mock labeled frames file
        labeled_file = source_dir / "chunk_001_labeled_frames.jsonl"
        mock_data = [
            {"frame_id": 1, "label": "critical", "confidence": 0.95, "objects": [{"class": "person", "bbox": [0,0,10,10]}]},
            {"frame_id": 2, "label": "silence", "confidence": 0.88, "objects": []},
            {"frame_id": 3, "label": "critical", "confidence": 0.92, "objects": [{"class": "person", "bbox": [0,0,10,10]}]},
        ]
        with open(labeled_file, "w") as f:
            for item in mock_data:
                f.write(json.dumps(item) + "\n")
        
        yield {
            "source": source_dir,
            "target": target_dir,
            "expected_jsonl": target_dir / "chunk_001_frames.jsonl"
        }


def test_export_raw_data_creates_files(temp_export_dirs):
    """Test that export_raw_data creates the target JSONL file."""
    stats = export_raw_data(
        source_dir=temp_export_dirs["source"],
        target_dir=temp_export_dirs["target"],
        chunk_id="chunk_001"
    )
    
    assert stats["success"] is True
    assert stats["frames_exported"] == 3
    assert stats["labels_exported"] == 3  # All are critical or silence
    assert temp_export_dirs["expected_jsonl"].exists()
    
    # Verify content
    with open(temp_export_dirs["expected_jsonl"], "r") as f:
        lines = f.readlines()
        assert len(lines) == 3


def test_export_raw_data_handles_missing_source(temp_export_dirs):
    """Test behavior when source directory does not exist."""
    stats = export_raw_data(
        source_dir=Path("/nonexistent/path"),
        target_dir=temp_export_dirs["target"],
        chunk_id="chunk_001"
    )
    
    assert stats["success"] is False
    assert "Source directory does not exist" in str(stats.get("error", ""))


def test_generate_manifest_correct_counts(temp_export_dirs):
    """Test that generate_manifest correctly counts frames and labels."""
    # First export data
    export_raw_data(
        source_dir=temp_export_dirs["source"],
        target_dir=temp_export_dirs["target"],
        chunk_id="chunk_001"
    )
    
    manifest_path = Path(temp_export_dirs["target"].parent) / "manifest.jsonl"
    manifest_result = generate_manifest(
        raw_data_dir=temp_export_dirs["target"],
        output_path=manifest_path
    )
    
    assert manifest_result["success"] is True
    assert manifest_result["total_frames"] == 3
    assert manifest_result["chunks"] == 1
    
    # Verify manifest content
    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)
        assert manifest_data["total_frames"] == 3
        assert manifest_data["total_critical_labels"] == 2
        assert manifest_data["total_silence_labels"] == 1
        assert len(manifest_data["chunks"]) == 1
        assert manifest_data["chunks"][0]["file_path"].endswith("chunk_001_frames.jsonl")


def test_compute_file_hash(temp_export_dirs):
    """Test SHA-256 hash computation."""
    # Create a known file
    test_file = temp_export_dirs["target"] / "test.txt"
    test_content = "Hello, World!"
    with open(test_file, "w") as f:
        f.write(test_content)
    
    # Compute hash manually
    import hashlib
    expected_hash = hashlib.sha256(test_content.encode()).hexdigest()
    
    # Compute via function
    actual_hash = compute_file_hash(test_file)
    
    assert actual_hash == expected_hash


def test_dry_run_mode(temp_export_dirs):
    """Test that dry_run=True does not create files."""
    stats = export_raw_data(
        source_dir=temp_export_dirs["source"],
        target_dir=temp_export_dirs["target"],
        chunk_id="chunk_001",
        dry_run=True
    )
    
    assert stats["success"] is True  # Logic succeeds, but no files written
    assert not temp_export_dirs["expected_jsonl"].exists()