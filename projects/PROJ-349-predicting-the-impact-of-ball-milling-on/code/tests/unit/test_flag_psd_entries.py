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
    run_flagging_pipeline
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
def temp_detected_images_json():
    """Create a temporary JSON file with detected image paths."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False) as f:
        json.dump(["/path/to/image1.png", "/path/to/image2.png"], f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup handled by caller or pytest fixture finalizer if needed
    # os.rmdir(temp_dir) # Avoid recursive removal issues if not empty


def test_compute_blob_hash(temp_image_file):
    """Test that compute_blob_hash returns a valid SHA-256 hex string."""
    result = compute_blob_hash(temp_image_file)
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in result)


def test_compute_blob_hash_missing_file():
    """Test that compute_blob_hash raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_blob_hash("/nonexistent/path/file.png")


def test_flag_entry_schema(temp_image_file):
    """Test that flag_entry returns a dict with the correct schema."""
    entry = flag_entry(temp_image_file, source="TestSource")
    assert "experiment_id" in entry
    assert "source" in entry
    assert "issue_type" in entry
    assert "raw_blob_hash" in entry
    assert entry["source"] == "TestSource"
    assert entry["issue_type"] == "unstructured_psd_image"
    assert len(entry["raw_blob_hash"]) == 64


def test_flag_entry_with_metadata(temp_image_file):
    """Test flag_entry with custom issue type."""
    entry = flag_entry(temp_image_file, source="TestSource", issue_type="custom_issue")
    assert entry["issue_type"] == "custom_issue"
    assert entry["source"] == "TestSource"


def test_run_flagging_pipeline(temp_detected_images_json, temp_output_dir):
    """Test the full flagging pipeline."""
    output_path = os.path.join(temp_output_dir, "flagged_psd.json")

    # Mock os.path.exists to return True for the fake paths in the JSON
    # since the paths in temp_detected_images_json are fake
    with patch('os.path.exists', return_value=True):
        # We also need to mock the file reading for hashing since the paths don't exist on disk
        # But compute_blob_hash checks os.path.exists first.
        # Let's create actual temp files for the paths in the JSON to make the test robust
        pass

    # Better approach: Create actual temp files and update the JSON
    with tempfile.TemporaryDirectory() as actual_temp_dir:
        img1_path = os.path.join(actual_temp_dir, "image1.png")
        img2_path = os.path.join(actual_temp_dir, "image2.png")

        with open(img1_path, 'wb') as f:
            f.write(b"data1")
        with open(img2_path, 'wb') as f:
            f.write(b"data2")

        # Update the JSON to point to real files
        real_detected_json = os.path.join(actual_temp_dir, "detected.json")
        with open(real_detected_json, 'w') as f:
            json.dump([img1_path, img2_path], f)

        output_path = os.path.join(actual_temp_dir, "flagged.json")

        flagged_entries = run_flagging_pipeline(
            detected_images_path=real_detected_json,
            output_path=output_path
        )

        assert len(flagged_entries) == 2
        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            saved_data = json.load(f)

        assert len(saved_data) == 2
        for entry in saved_data:
            assert "experiment_id" in entry
            assert "source" in entry
            assert "issue_type" in entry
            assert "raw_blob_hash" in entry
            assert len(entry["raw_blob_hash"]) == 64


def test_run_flagging_pipeline_no_input_file(temp_output_dir):
    """Test pipeline when input file does not exist."""
    output_path = os.path.join(temp_output_dir, "flagged.json")
    non_existent_input = os.path.join(temp_output_dir, "non_existent.json")

    flagged_entries = run_flagging_pipeline(
        detected_images_path=non_existent_input,
        output_path=output_path
    )

    assert flagged_entries == []
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        assert json.load(f) == []
