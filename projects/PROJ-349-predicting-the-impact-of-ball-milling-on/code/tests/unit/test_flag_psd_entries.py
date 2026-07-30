"""
Unit tests for T014b: Flagging Logic.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.ingest.flag_psd_entries import (
    compute_blob_hash,
    flag_entry,
    run_flagging_pipeline,
    FLAGGED_OUTPUT_PATH,
)


@pytest.fixture
def temp_image_file():
    """Create a temporary image file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"fake_image_data_12345")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_detected_images_json(temp_image_file):
    """Create a temporary JSON file simulating T014a output."""
    data = [
        {
            "file_path": temp_image_file,
            "experiment_id": "EXP-001",
            "source": "arXiv",
            "page_number": 3,
            "detection_score": 0.95,
        }
    ]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump(data, f)
        temp_json_path = f.name
    yield temp_json_path
    os.unlink(temp_json_path)


def test_compute_blob_hash():
    """Test that compute_blob_hash returns a valid SHA-256 hex string."""
    data = b"test_data"
    hash_val = compute_blob_hash(data)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA-256 hex length
    # Verify determinism
    assert compute_blob_hash(data) == hash_val


def test_flag_entry_schema():
    """Test that flag_entry produces the correct schema."""
    entry = flag_entry(
        experiment_id="EXP-001",
        source="Materials Project",
        issue_type="unstructured_psd_image",
        raw_data=b"test",
    )

    assert "experiment_id" in entry
    assert "source" in entry
    assert "issue_type" in entry
    assert "raw_blob_hash" in entry

    assert entry["experiment_id"] == "EXP-001"
    assert entry["source"] == "Materials Project"
    assert entry["issue_type"] == "unstructured_psd_image"
    assert len(entry["raw_blob_hash"]) == 64


def test_flag_entry_with_metadata():
    """Test that flag_entry includes optional metadata."""
    meta = {"page": 5, "score": 0.8}
    entry = flag_entry(
        experiment_id="EXP-002",
        source="NIST",
        issue_type="missing_values",
        raw_data=b"test",
        metadata=meta,
    )
    assert "metadata" in entry
    assert entry["metadata"] == meta


def test_run_flagging_pipeline(temp_detected_images_json, temp_image_file):
    """Test the full pipeline writes the correct JSON file."""
    output_path = Path(tempfile.mktemp(suffix=".json"))
    try:
        # Run pipeline
        results = run_flagging_pipeline(
            detected_images=[
                {
                    "file_path": temp_image_file,
                    "experiment_id": "EXP-001",
                    "source": "arXiv",
                    "page_number": 1,
                    "detection_score": 0.9,
                }
            ],
            output_path=output_path,
        )

        # Verify return value
        assert len(results) == 1
        assert results[0]["experiment_id"] == "EXP-001"

        # Verify file written
        assert output_path.exists()
        with open(output_path, "r") as f:
            written_data = json.load(f)

        assert isinstance(written_data, list)
        assert len(written_data) == 1
        assert written_data[0]["source"] == "arXiv"
        assert "raw_blob_hash" in written_data[0]

    finally:
        if output_path.exists():
            output_path.unlink()


def test_run_flagging_pipeline_missing_file(caplog):
    """Test that missing files are skipped and logged."""
    results = run_flagging_pipeline(
        detected_images=[
            {
                "file_path": "/nonexistent/path/image.png",
                "experiment_id": "EXP-001",
                "source": "arXiv",
            }
        ],
        output_path=Path(tempfile.mktemp(suffix=".json")),
    )
    assert len(results) == 0
    assert "Skipping missing file" in caplog.text