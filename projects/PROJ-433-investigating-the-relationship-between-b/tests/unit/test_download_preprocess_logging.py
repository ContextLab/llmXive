"""
Tests for logging in download and preprocess modules (Task T015).
"""
import os
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import setup_logger, LOG_FILE_PREPROCESS
from download import verify_fMRI_availability, log_download_start
from preprocess import run_fmriprep, validate_preprocessed_outputs

@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file path."""
    log_path = tmp_path / "test_preprocess_log.txt"
    # Temporarily patch the global log file path in utils
    import utils
    original_log_file = utils.LOG_FILE_PREPROCESS
    utils.LOG_FILE_PREPROCESS = log_path
    yield log_path
    utils.LOG_FILE_PREPROCESS = original_log_file

def test_download_logs_to_preprocess_log(temp_log_file):
    """Test that download operations log to preprocess_log.txt."""
    # Reset logger handlers to ensure fresh state
    logger = setup_logger()
    # Remove existing handlers to force re-creation with temp file
    logger.handlers = []
    setup_logger(log_file=temp_log_file)

    # Perform an action that should log
    log_download_start("sub-999", "http://example.com/data")

    # Verify log file exists and contains the message
    assert temp_log_file.exists(), "Log file was not created"
    
    content = temp_log_file.read_text()
    assert "Starting download for subject sub-999" in content, "Expected log message not found"

def test_verify_fmri_missing_logs_to_preprocess_log(temp_log_file, tmp_path):
    """Test that missing fMRI data logs to preprocess_log.txt."""
    # Setup logger with temp file
    logger = setup_logger()
    logger.handlers = []
    setup_logger(log_file=temp_log_file)

    # Create a fake data root that doesn't contain the subject
    fake_data_root = tmp_path / "data" / "raw" / "HCP1200" / "missing_sub"
    # No files created here

    # Patch the DATA_ROOT in download module
    import download
    original_data_root = download.DATA_ROOT
    download.DATA_ROOT = tmp_path / "data" / "raw"

    try:
        result = verify_fMRI_availability("missing_sub")
        assert result['status'] == 'MISSING'
    finally:
        download.DATA_ROOT = original_data_root

    # Verify log content
    assert temp_log_file.exists()
    content = temp_log_file.read_text()
    assert "Data Gap" in content or "fMRI time-series not found" in content

def test_fmriprep_skips_missing_data_logs(temp_log_file, tmp_path):
    """Test that preprocessing skips missing data and logs correctly."""
    # Setup logger
    logger = setup_logger()
    logger.handlers = []
    setup_logger(log_file=temp_log_file)

    # Patch data root
    import preprocess
    import download
    original_data_root = preprocess.DATA_ROOT
    preprocess.DATA_ROOT = tmp_path / "data"
    download.DATA_ROOT = tmp_path / "data" / "raw"

    try:
        result = run_fmriprep("missing_sub", mode="ci")
        assert result['status'] == 'SKIPPED'
    finally:
        preprocess.DATA_ROOT = original_data_root
        download.DATA_ROOT = tmp_path / "data" / "raw"

    # Verify log content
    assert temp_log_file.exists()
    content = temp_log_file.read_text()
    assert "N/A - Data Unavailable" in content, "Expected 'N/A - Data Unavailable' log message"

def test_fmriprep_qc_exclusion_logs(temp_log_file, tmp_path):
    """Test that QC exclusion logs to preprocess_log.txt."""
    # Setup logger
    logger = setup_logger()
    logger.handlers = []
    setup_logger(log_file=temp_log_file)

    # Create a dummy subject structure with high FD
    subject_dir = tmp_path / "data" / "processed" / "high_fd_sub"
    subject_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy confounds with high motion (simulated)
    confounds_file = subject_dir / "sub-high_fd_sub_desc-confounds_timeseries.tsv"
    # We mock the calculation in validate_preprocessed_outputs to return high FD
    
    # Patch the calculate_fd function to return a high value
    import preprocess
    original_calc_fd = preprocess.calculate_fd_from_confounds
    
    def mock_calc_fd(path):
        return 0.8 # High FD
    
    preprocess.calculate_fd_from_confounds = mock_calc_fd

    try:
        result = validate_preprocessed_outputs("high_fd_sub")
        assert result['status'] == 'EXCLUDED'
    finally:
        preprocess.calculate_fd_from_confounds = original_calc_fd

    # Verify log content
    assert temp_log_file.exists()
    content = temp_log_file.read_text()
    assert "Exclusion logged" in content or "EXCLUDED" in content
    assert "FD" in content and "0.5" in content