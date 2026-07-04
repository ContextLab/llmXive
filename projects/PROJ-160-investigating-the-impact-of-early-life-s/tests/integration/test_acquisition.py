"""
Integration test for data acquisition module.
Tests the download, checksum verification, and acquisition logic for ABCD data.
"""
import pytest
import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from code.data.acquisition import acquire_data, download_file, verify_checksum, calculate_md5
from code.main import DataLoadError, PipelineError
from code.config_env import get_raw_dir

def test_download_file_success(tmp_path):
    """Test successful file download."""
    url = "https://httpbin.org/bytes/1024"  # Public test endpoint returning 1KB
    output_path = tmp_path / "test_file.bin"
    
    download_file(url, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size == 1024

def test_download_file_failure(tmp_path):
    """Test download failure raises DataLoadError."""
    url = "https://httpbin.org/status/404"
    output_path = tmp_path / "test_file.bin"
    
    with pytest.raises(DataLoadError):
        download_file(url, output_path)

def test_verify_checksum_match(tmp_path):
    """Test checksum verification for matching files."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test data")
    
    # Calculate actual checksum
    actual_checksum = calculate_md5(file_path)
    
    assert verify_checksum(file_path, actual_checksum) is True

def test_verify_checksum_mismatch(tmp_path):
    """Test checksum verification for mismatched files."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test data")
    
    assert verify_checksum(file_path, "wrong_checksum") is False

@patch('code.data.acquisition.requests.get')
@patch('code.data.acquisition.get_raw_dir')
def test_acquire_data_download_success(mock_get_raw_dir, mock_requests_get, tmp_path):
    """Test acquire_data with successful download."""
    mock_raw_dir = tmp_path / "raw"
    mock_raw_dir.mkdir()
    mock_get_raw_dir.return_value = mock_raw_dir
    
    # Mock response for phenotypic
    mock_response_pheno = MagicMock()
    mock_response_pheno.iter_content.return_value = [b"phenotypic_data"]
    mock_response_pheno.raise_for_status = MagicMock()
    
    # Mock response for subcortical
    mock_response_sub = MagicMock()
    mock_response_sub.iter_content.return_value = [b"subcortical_data"]
    mock_response_sub.raise_for_status = MagicMock()
    
    mock_requests_get.side_effect = [mock_response_pheno, mock_response_sub]
    
    phenotypic_path, subcortical_path = acquire_data()
    
    assert phenotypic_path.exists()
    assert subcortical_path.exists()

@patch('code.data.acquisition.requests.get')
@patch('code.data.acquisition.get_raw_dir')
def test_acquire_data_download_failure_fallback_to_local(mock_get_raw_dir, mock_requests_get, tmp_path):
    """Test acquire_data falls back to local files when download fails."""
    mock_raw_dir = tmp_path / "raw"
    mock_raw_dir.mkdir()
    mock_get_raw_dir.return_value = mock_raw_dir
    
    # Create local sample files
    sample_pheno = mock_raw_dir / "sample_phenotypic.csv"
    sample_pheno.write_text("phenotypic_data")
    sample_sub = mock_raw_dir / "sample_subcortical.csv"
    sample_sub.write_text("subcortical_data")
    
    # Mock download to fail
    mock_requests_get.side_effect = Exception("Download failed")
    
    phenotypic_path, subcortical_path = acquire_data()
    
    # Should return the local sample files
    assert phenotypic_path == sample_pheno
    assert subcortical_path == sample_sub

@patch('code.data.acquisition.requests.get')
@patch('code.data.acquisition.get_raw_dir')
def test_acquire_data_no_local_fallback(mock_get_raw_dir, mock_requests_get, tmp_path):
    """Test acquire_data raises error when download fails and no local files."""
    mock_raw_dir = tmp_path / "raw"
    mock_raw_dir.mkdir()
    mock_get_raw_dir.return_value = mock_raw_dir
    
    # Mock download to fail
    mock_requests_get.side_effect = Exception("Download failed")
    
    with pytest.raises(PipelineError):
        acquire_data()