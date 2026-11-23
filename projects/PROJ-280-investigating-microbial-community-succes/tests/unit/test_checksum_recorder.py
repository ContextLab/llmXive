"""
Unit tests for the checksum recorder (T016).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We will mock the external dependencies to test logic in isolation
# Import the functions we want to test
from code import checksum_recorder

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        processed_dir = tmp_path / "data" / "processed"
        state_dir = tmp_path / "state" / "projects"
        processed_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)
        yield {
            "root": tmp_path,
            "processed": processed_dir,
            "state": state_dir
        }

@pytest.fixture
def mock_processed_files(temp_dirs):
    """Create mock processed files."""
    files = [
        "low_depth_results.json",
        "medium_depth_results.json",
        "high_depth_results.json",
        "sensitivity_sweep_results.json",
        "exclusion_log.json"
    ]
    for filename in files:
        file_path = temp_dirs["processed"] / filename
        with open(file_path, "w") as f:
            json.dump({"test": "data"}, f)
    return files

def test_record_checksums_success(temp_dirs, mock_processed_files):
    """Test that checksums are calculated and state is updated."""
    state_file = temp_dirs["state"] / "PROJ-280-investigating-microbial-community-succes.yaml"
    
    # Mock the state tracker functions to avoid YAML parsing issues in test
    with patch('code.checksum_recorder.ensure_state_file') as mock_ensure, \
         patch('code.checksum_recorder.load_state') as mock_load, \
         patch('code.checksum_recorder.update_multiple_artifacts') as mock_update, \
         patch('code.checksum_recorder.generate_checksum', return_value="abc123"):
        
        mock_ensure.return_value = None
        mock_load.return_value = {"project": "test"}
        mock_update.return_value = None

        result = checksum_recorder.record_checksums(
            processed_dir=temp_dirs["processed"],
            state_file_path=state_file,
            project_id="PROJ-280-test"
        )

        assert result["status"] == "success"
        assert result["processed_count"] == 5
        assert mock_update.called
        
        # Verify the artifacts passed to update_multiple_artifacts
        call_args = mock_update.call_args[1]['artifacts']
        assert "low_depth_results.json" in call_args
        assert call_args["low_depth_results.json"]["hash"] == "abc123"
        assert call_args["low_depth_results.json"]["status"] == "verified"

def test_record_checksums_missing_files(temp_dirs):
    """Test behavior when expected files are missing."""
    # Create only one file
    file_path = temp_dirs["processed"] / "low_depth_results.json"
    with open(file_path, "w") as f:
        json.dump({}, f)

    state_file = temp_dirs["state"] / "PROJ-280-investigating-microbial-community-succes.yaml"

    with patch('code.checksum_recorder.ensure_state_file'), \
         patch('code.checksum_recorder.load_state'), \
         patch('code.checksum_recorder.update_multiple_artifacts'), \
         patch('code.checksum_recorder.generate_checksum', return_value="abc123"):

        result = checksum_recorder.record_checksums(
            processed_dir=temp_dirs["processed"],
            state_file_path=state_file,
            project_id="PROJ-280-test"
        )

        assert result["status"] == "success"
        assert result["processed_count"] == 1
        assert len(result["missing_files"]) == 4
        assert "medium_depth_results.json" in result["missing_files"]

def test_record_checksums_directory_not_found(temp_dirs):
    """Test error handling when processed directory is missing."""
    state_file = temp_dirs["state"] / "PROJ-280-investigating-microbial-community-succes.yaml"
    fake_dir = temp_dirs["root"] / "non_existent_dir"

    with pytest.raises(FileNotFoundError, match="Processed directory not found"):
        checksum_recorder.record_checksums(
            processed_dir=fake_dir,
            state_file_path=state_file
        )
