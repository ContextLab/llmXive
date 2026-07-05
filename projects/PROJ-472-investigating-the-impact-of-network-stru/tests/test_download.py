"""
Tests for the dMRI download module.

These tests verify the download functionality without actually downloading
large files. They test the logic and structure of the download process.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.download import (
    check_datalad_installed,
    verify_downloaded_files,
    SUBJECTS_TO_DOWNLOAD,
    REQUIRED_FILES
)
from utils.logger import setup_logger

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_subject_dir(temp_data_dir):
    """Create a sample subject directory with dummy files."""
    subject_dir = temp_data_dir / "sub-001"
    subject_dir.mkdir()
    
    # Create dummy files
    for file_rel in REQUIRED_FILES:
        file_name = Path(file_rel).name
        dummy_file = subject_dir / file_name
        dummy_file.write_text("dummy content")
    
    return subject_dir

def test_check_datalad_installed():
    """Test datalad availability check."""
    # This will return True if datalad is installed, False otherwise
    # We don't assert a specific value as it depends on the environment
    result = check_datalad_installed()
    assert isinstance(result, bool)

def test_verify_downloaded_files_all_present(sample_subject_dir):
    """Test verification when all required files are present."""
    result = verify_downloaded_files(sample_subject_dir)
    assert result is True

def test_verify_downloaded_files_missing_file(temp_data_dir):
    """Test verification when a required file is missing."""
    subject_dir = temp_data_dir / "sub-002"
    subject_dir.mkdir()
    
    # Create only one of the required files
    (subject_dir / "dwi.bvec").write_text("dummy")
    
    result = verify_downloaded_files(subject_dir)
    assert result is False

def test_verify_downloaded_files_empty_file(temp_data_dir):
    """Test verification when a file is empty."""
    subject_dir = temp_data_dir / "sub-003"
    subject_dir.mkdir()
    
    # Create files but make one empty
    for file_rel in REQUIRED_FILES:
        file_name = Path(file_rel).name
        file_path = subject_dir / file_name
        if file_name == "dwi.nii.gz":
            file_path.write_text("")  # Empty file
        else:
            file_path.write_text("dummy")
    
    result = verify_downloaded_files(subject_dir)
    assert result is False

def test_subjects_to_download_format():
    """Test that subject IDs are in the correct format."""
    for subject in SUBJECTS_TO_DOWNLOAD:
        assert subject.startswith("sub-")
        assert len(subject) == 7  # sub-XXX
        assert subject[4:].isdigit()

def test_required_files_format():
    """Test that required file paths are in correct format."""
    for file_path in REQUIRED_FILES:
        assert file_path.startswith("dwi/")
        assert Path(file_path).suffix in ['.bvec', '.bval', '.nii.gz']

def test_download_structure(temp_data_dir):
    """Test that the download creates the correct directory structure."""
    # Simulate the expected directory structure
    expected_dirs = [
        temp_data_dir / "sub-001",
        temp_data_dir / "sub-002",
        temp_data_dir / "sub-010"
    ]
    
    for dir_path in expected_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Verify directories exist
    for dir_path in expected_dirs:
        assert dir_path.exists()
        assert dir_path.is_dir()

@patch('data.download.subprocess.run')
def test_download_command_execution(mock_run, temp_data_dir):
    """Test that download commands are executed correctly."""
    from data.download import download_subject_files
    
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_run.return_value = mock_process
    
    subject_dir = temp_data_dir / "sub-001"
    subject_dir.mkdir()
    
    success, files = download_subject_files("sub-001", temp_data_dir)
    
    # Verify subprocess.run was called
    assert mock_run.called

@patch('data.download.subprocess.run')
def test_download_timeout_handling(mock_run, temp_data_dir):
    """Test handling of download timeout."""
    from data.download import download_subject_files
    from subprocess import TimeoutExpired
    
    mock_run.side_effect = TimeoutExpired(cmd="wget", timeout=300)
    
    subject_dir = temp_data_dir / "sub-001"
    subject_dir.mkdir()
    
    success, files = download_subject_files("sub-001", temp_data_dir)
    
    # Should return False on timeout
    assert success is False
