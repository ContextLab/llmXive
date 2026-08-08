"""
Unit tests for code/download.py
"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from utils import DataNotFoundError, PipelineError

# Import the module to test
# We assume the module is importable as 'download'
import sys
sys.path.insert(0, 'code')
import download

def test_download_subject_data_missing_data():
    """
    Contract: Verify download_subject_data(subject_id) raises FileNotFoundError 
    (or DataNotFoundError) if missing.
    """
    subject_id = "999999" # Non-existent subject
    # Ensure the raw directory does not have the files
    raw_dir = Path("data/raw") / subject_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    # Remove any existing files
    for f in raw_dir.glob("*"):
        f.unlink()
    
    with pytest.raises(DataNotFoundError):
        download.download_subject_data(subject_id)

def test_download_subject_data_present_data():
    """
    Contract: Verify download_subject_data returns dict with keys 
    {'dwi_path', 'rsfmri_path'} if files exist.
    """
    subject_id = "100106"
    raw_dir = Path("data/raw") / subject_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy files
    dwi_path = raw_dir / "dwi.trk"
    rsfmr_path = raw_dir / "rs-fMRI.nii.gz"
    dwi_path.touch()
    rsfmr_path.touch()
    
    result = download.download_subject_data(subject_id)
    
    assert isinstance(result, dict)
    assert "dwi_path" in result
    assert "rsfmri_path" in result
    assert result["dwi_path"] == str(dwi_path)
    assert result["rsfmri_path"] == str(rsfmr_path)
    
    # Cleanup
    dwi_path.unlink()
    rsfmr_path.unlink()

def test_process_subjects_skips_missing():
    """
    Contract: Verify process_subjects logs warning for missing subjects
    and continues.
    """
    subject_ids = ["100106", "999999"]
    raw_dir_1 = Path("data/raw") / "100106"
    raw_dir_2 = Path("data/raw") / "999999"
    
    # Setup existing data for first subject
    raw_dir_1.mkdir(parents=True, exist_ok=True)
    (raw_dir_1 / "dwi.trk").touch()
    (raw_dir_1 / "rs-fMRI.nii.gz").touch()
    
    # Ensure second subject has no data
    raw_dir_2.mkdir(parents=True, exist_ok=True)
    
    with patch.object(download, 'get_logger_module') as mock_logger:
        mock_log_instance = MagicMock()
        mock_logger.return_value = mock_log_instance
        
        results = download.process_subjects(subject_ids)
        
        # Should have one success and one skip
        assert len(results) == 1
        assert results[0]["subject_id"] == "100106"
        
        # Check that warning was logged for the missing subject
        warning_calls = [call for call in mock_log_instance.warning.call_args_list if "Skipping" in str(call)]
        assert len(warning_calls) > 0

def test_checksum_verification():
    """
    Contract: Verify checksum logic works.
    """
    # Create a temporary file with known content
    test_file = Path("data/raw/test_checksum.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("test content")
    
    # Compute checksum
    checksum = download.compute_sha256_file(test_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64 # SHA256 hex length
    
    # Verify against itself
    assert download.verify_checksum(test_file, checksum)
    
    # Verify against wrong checksum
    assert not download.verify_checksum(test_file, "wrong_checksum")
    
    # Cleanup
    test_file.unlink()
