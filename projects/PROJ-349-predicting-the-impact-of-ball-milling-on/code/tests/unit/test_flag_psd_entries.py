"""
Unit tests for the flagging logic (T014b).
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
    DETECTED_IMAGES_INPUT_PATH
)


@pytest.fixture
def temp_image_file(tmp_path):
    """Create a temporary image file."""
    img_path = tmp_path / "test_image.png"
    img_path.write_bytes(b"fake_image_content")
    return str(img_path)


@pytest.fixture
def temp_detected_images_json(tmp_path):
    """Create a temporary detected images JSON file."""
    detected_path = tmp_path / "detected_psd_images.json"
    data = [
        {
            "image_path": str(tmp_path / "img1.png"),
            "source_name": "TestSource",
            "source_id": "test_123"
        },
        {
            "image_path": str(tmp_path / "img2.png"),
            "source_name": "TestSource",
            "source_id": "test_456"
        }
    ]
    detected_path.write_text(json.dumps(data))
    return detected_path


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    return tmp_path


def test_compute_blob_hash(temp_image_file):
    """Test SHA256 hash computation."""
    hash_val = compute_blob_hash(temp_image_file)
    assert len(hash_val) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in hash_val)


def test_compute_blob_hash_missing_file():
    """Test hash computation with missing file."""
    with pytest.raises(FileNotFoundError):
        compute_blob_hash("non_existent_file.png")


def test_flag_entry_schema(temp_image_file):
    """Test that flag_entry produces correct schema."""
    result = flag_entry(
        image_path=temp_image_file,
        source_name="TestSource",
        source_id="test_123"
    )
    
    assert "experiment_id" in result
    assert "source" in result
    assert "issue_type" in result
    assert "raw_blob_hash" in result
    
    assert result["source"] == "TestSource"
    assert result["issue_type"] == "unstructured_psd_image"
    assert len(result["experiment_id"]) == 12


def test_flag_entry_with_metadata(temp_image_file):
    """Test flag_entry with specific metadata."""
    result = flag_entry(
        image_path=temp_image_file,
        source_name="arXiv",
        source_id="2301.12345",
        issue_type="custom_issue"
    )
    
    assert result["source"] == "arXiv"
    assert result["source_id"] == "2301.12345" # Note: source_id is stored in entry for reference
    assert result["issue_type"] == "custom_issue"


def test_run_flagging_pipeline(temp_detected_images_json, temp_image_file, temp_output_dir):
    """Test the full flagging pipeline."""
    # Mock the input path and output path
    with patch('src.ingest.flag_psd_entries.DETECTED_IMAGES_INPUT_PATH', temp_detected_images_json):
        with patch('src.ingest.flag_psd_entries.FLAGGED_OUTPUT_PATH', temp_output_dir / "flagged.json"):
            # Create dummy image files
            img1 = temp_detected_images_json.parent / "img1.png"
            img2 = temp_detected_images_json.parent / "img2.png"
            img1.write_bytes(b"content1")
            img2.write_bytes(b"content2")
            
            flagged_entries = run_flagging_pipeline()
            
            assert len(flagged_entries) == 2
            
            # Verify output file exists
            output_path = temp_output_dir / "flagged.json"
            assert output_path.exists()
            
            with open(output_path, "r") as f:
                saved_data = json.load(f)
            
            assert len(saved_data) == 2
            assert all("experiment_id" in entry for entry in saved_data)
            assert all("source" in entry for entry in saved_data)
            assert all("issue_type" in entry for entry in saved_data)
            assert all("raw_blob_hash" in entry for entry in saved_data)


def test_run_flagging_pipeline_missing_file(temp_output_dir):
    """Test pipeline when input file is missing."""
    with patch('src.ingest.flag_psd_entries.DETECTED_IMAGES_INPUT_PATH', temp_output_dir / "missing.json"):
        with patch('src.ingest.flag_psd_entries.FLAGGED_OUTPUT_PATH', temp_output_dir / "flagged.json"):
            flagged_entries = run_flagging_pipeline()
            
            assert flagged_entries == []
            assert (temp_output_dir / "flagged.json").exists()