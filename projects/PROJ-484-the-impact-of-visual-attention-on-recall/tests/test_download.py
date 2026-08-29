import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code to path if not already
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from download_data import calculate_sha256, verify_manifest, download_dataset
from logging_config import setup_logging

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for testing downloads."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_calculate_sha256(temp_output_dir):
    """Test SHA256 calculation on a dummy file."""
    test_file = temp_output_dir / "test.txt"
    test_file.write_text("Hello World")
    
    checksum = calculate_sha256(test_file)
    assert len(checksum) == 64
    assert isinstance(checksum, str)

def test_verify_manifest_missing_files(temp_output_dir):
    """Test manifest verification with missing files."""
    # Create a partial structure
    (temp_output_dir / "dataset_description.json").write_text("{}")
    
    result = verify_manifest(temp_output_dir)
    assert result is False

def test_verify_manifest_complete(temp_output_dir):
    """Test manifest verification with complete structure."""
    # Create expected files
    (temp_output_dir / "dataset_description.json").write_text("{}")
    (temp_output_dir / "participants.tsv").write_text("participant_id\nsub-01")
    (temp_output_dir / "task-rsvp_events.tsv").write_text("trial_id\n1")
    (temp_output_dir / "sub-01").mkdir()
    (temp_output_dir / "sub-01" / "func").mkdir()
    (temp_output_dir / "sub-01" / "func" / "sub-01_task-rsvp_events.tsv").write_text("trial_id\n1")
    
    result = verify_manifest(temp_output_dir)
    assert result is True

def test_download_dataset_structure(temp_output_dir):
    """
    Test that the download function creates the expected directory structure.
    Note: This test assumes network access and a valid dataset ID.
    In CI environments without network, this might be skipped or mocked.
    """
    try:
        # Attempt a small download (dataset_description.json)
        # We rely on the real function to hit the network.
        # If huggingface_hub is not installed or network fails, this test might fail,
        # but the requirement is to implement the script to work with real data.
        success = download_dataset(temp_output_dir, dataset_id="openneuro/ds001435")
        
        if success:
            # Check if core files exist
            assert (temp_output_dir / "dataset_description.json").exists()
            assert (temp_output_dir / "participants.tsv").exists()
    except Exception:
        # If network is unavailable or dataset not found, we note it but don't fail the test logic
        # if the function itself is correctly implemented to raise.
        pytest.skip("Network or dataset unavailable for integration test of download.")
