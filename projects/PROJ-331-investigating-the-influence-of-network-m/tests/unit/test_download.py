"""
Unit tests for the download module.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module
import sys
sys.path.insert(0, 'code')
from download import download_subject_data, verify_data_integrity, _download_file
from utils import DataNotFoundError

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data/raw."""
    temp_dir = tempfile.mkdtemp()
    # Create the expected structure
    data_root = Path(temp_dir)
    (data_root / "data" / "raw").mkdir(parents=True)
    # Patch the global data root for testing
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield data_root
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_download_subject_data_missing_file(temp_data_dir):
    """Test that download_subject_data raises DataNotFoundError if data is missing and fetch fails."""
    subject_id = "999999"
    # Ensure no local data
    subject_dir = Path(temp_data_dir) / "data" / "raw" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock the download function to raise an error
    with patch('download._download_file') as mock_download:
        mock_download.side_effect = Exception("Network error")
        
        with pytest.raises(DataNotFoundError):
            download_subject_data(subject_id)

def test_download_subject_data_local_file_exists(temp_data_dir):
    """Test that download_subject_data returns local file paths if they exist."""
    subject_id = "100307"
    subject_dir = Path(temp_data_dir) / "data" / "raw" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy files
    dwi_path = subject_dir / "T1w" / "DWI" / "dwi.trk"
    dwi_path.parent.mkdir(parents=True, exist_ok=True)
    dwi_path.touch()
    
    rsfmr_path = subject_dir / "MNINonLinear" / "Results" / "rfMRI_REST1_LR" / "rfMRI_REST1_LR_hp2000_clean.nii.gz"
    rsfmr_path.parent.mkdir(parents=True, exist_ok=True)
    rsfmr_path.touch()
    
    result = download_subject_data(subject_id)
    
    assert "dwi_path" in result
    assert "rsfmri_path" in result
    assert result["dwi_path"] == str(dwi_path)
    assert result["rsfmri_path"] == str(rsfmr_path)

def test_verify_data_integrity(temp_data_dir):
    """Test verify_data_integrity with valid checksums."""
    subject_id = "100307"
    subject_dir = Path(temp_data_dir) / "data" / "raw" / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy files
    dwi_path = subject_dir / "T1w" / "DWI" / "dwi.trk"
    dwi_path.parent.mkdir(parents=True, exist_ok=True)
    dwi_path.write_text("dummy data")
    
    rsfmr_path = subject_dir / "MNINonLinear" / "Results" / "rfMRI_REST1_LR" / "rfMRI_REST1_LR_hp2000_clean.nii.gz"
    rsfmr_path.parent.mkdir(parents=True, exist_ok=True)
    rsfmr_path.write_text("dummy data")
    
    # Create checksums file
    checksums_file = Path(temp_data_dir) / "data" / "raw" / ".checksums.json"
    checksums = {
        subject_id: {
            "dwi": {"path": str(dwi_path), "sha256": "dummy_sha_dwi"},
            "rsfmr": {"path": str(rsfmr_path), "sha256": "dummy_sha_rsfmr"}
        }
    }
    # This test is simplified; in reality, we would compute real checksums.
    # For now, we just check that the function runs without error.
    # We will skip the actual checksum comparison in this mock test.
    
    # The function will compute real checksums and compare.
    # Since we used dummy data, the checksums won't match.
    # We will mock compute_sha256 to return the dummy checksums.
    from unittest.mock import patch
    from utils import compute_sha256
    
    with patch('download.compute_sha256', side_effect=lambda p: "dummy_sha"):
        # Also need to patch the checksums file to have the dummy checksums
        checksums = {
            subject_id: {
                "dwi": {"path": str(dwi_path), "sha256": "dummy_sha"},
                "rsfmr": {"path": str(rsfmr_path), "sha256": "dummy_sha"}
            }
        }
        with patch('download.safe_read_json', return_value=checksums):
            result = verify_data_integrity(subject_id)
            assert result is True

def test_download_file(temp_data_dir):
    """Test _download_file with a mock response."""
    url = "http://example.com/file.nii.gz"
    dest_path = Path(temp_data_dir) / "file.nii.gz"
    
    with patch('download.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_response.headers = {'content-length': '100'}
        mock_get.return_value = mock_response
        
        _download_file(url, dest_path)
        
        assert dest_path.exists()
        assert dest_path.read_bytes() == b"chunk1chunk2"
