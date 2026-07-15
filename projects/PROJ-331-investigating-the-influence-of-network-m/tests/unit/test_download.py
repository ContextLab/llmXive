"""
Unit tests for download.py
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module to test
# We need to ensure the path is set up correctly
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.download import (
    download_subject_data,
    find_local_files,
    load_checksums,
    DEFAULT_SUBJECTS
)
from code.utils import DataNotFoundError, PipelineError
from code.config import DATA_RAW_DIR

@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a temporary directory structure mimicking data/raw/"""
    # Create subdirectory for a subject
    subject_dir = tmp_path / "100306"
    subject_dir.mkdir()
    
    # Create dummy files
    dwi_file = subject_dir / "100306_dwi.trk"
    dwi_file.write_text("dummy dwi data")
    
    rsfmr_file = subject_dir / "100306_bold.nii.gz"
    rsfmr_file.write_text("dummy rsfmr data")
    
    # Create checksum file
    checksums = {
        "100306_dwi.trk": "abc123",
        "100306_bold.nii.gz": "def456"
    }
    (tmp_path / ".checksums.json").write_text(json.dumps(checksums))
    
    return tmp_path

@pytest.fixture
def mock_manifest(tmp_path):
    """Create a manifest file for download URLs"""
    manifest = {
        "100408": {
            "dwi_url": "https://example.com/100408_dwi.trk",
            "rsfmr_url": "https://example.com/100408_bold.nii.gz"
        }
    }
    (tmp_path / "data_manifest.json").write_text(json.dumps(manifest))
    return tmp_path

def test_find_local_files_found(mock_data_dir):
    """Test finding local files when they exist"""
    with patch('code.download.DATA_RAW_DIR', mock_data_dir):
        result = find_local_files("100306")
        assert 'dwi_path' in result
        assert 'rsfmri_path' in result
        assert result['dwi_path'].name == "100306_dwi.trk"
        assert result['rsfmri_path'].name == "100306_bold.nii.gz"

def test_find_local_files_not_found(tmp_path):
    """Test finding local files when they don't exist"""
    with patch('code.download.DATA_RAW_DIR', tmp_path):
        result = find_local_files("100306")
        assert result == {}

def test_download_subject_data_local_exists(mock_data_dir):
    """Test download_subject_data when local files exist"""
    with patch('code.download.DATA_RAW_DIR', mock_data_dir):
        result = download_subject_data("100306")
        assert result['dwi_path'] == str(mock_data_dir / "100306" / "100306_dwi.trk")
        assert result['rsfmri_path'] == str(mock_data_dir / "100306" / "100306_bold.nii.gz")

def test_download_subject_data_missing_raises_error(tmp_path):
    """Test that download_subject_data raises FileNotFoundError when data is missing and no URL is configured"""
    with patch('code.download.DATA_RAW_DIR', tmp_path):
        with pytest.raises(FileNotFoundError):
            download_subject_data("100306")

def test_download_subject_data_fetch_fails_loudly(tmp_path, mock_manifest):
    """Test that download_subject_data fails loudly on fetch error (no synthetic fallback)"""
    # Setup directory with manifest but no local files
    data_dir = tmp_path
    (data_dir / "100408").mkdir() # Empty dir, no files
    
    with patch('code.download.DATA_RAW_DIR', data_dir):
        with patch('code.download.requests.get') as mock_get:
            # Simulate a network error
            mock_get.side_effect = Exception("Network failure")
            
            with pytest.raises(PipelineError):
                download_subject_data("100408")

def test_load_checksums(tmp_path):
    """Test loading checksums from file"""
    checksums = {
        "file1.trk": "hash1",
        "file2.nii.gz": "hash2"
    }
    checksum_file = tmp_path / ".checksums.json"
    checksum_file.write_text(json.dumps(checksums))
    
    with patch('code.download.DATA_RAW_DIR', tmp_path):
        result = load_checksums()
        assert result == checksums

def test_load_checksums_missing_file(tmp_path):
    """Test loading checksums when file doesn't exist"""
    with patch('code.download.DATA_RAW_DIR', tmp_path):
        result = load_checksums()
        assert result == {}
