"""
Unit tests for T020: download_ground_truth module.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add code directory to path
code_dir = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(code_dir))

from data.download_ground_truth import calculate_sha256, verify_checksum, download_ground_truth
from utils.errors import DatasetUnavailableError

def test_calculate_sha256():
    """Test SHA256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        # "test content" hash
        expected_hash = "6ae8af4980b53463a51015abd5919e97bed0af072cf86078288040d8f7655c00"
        actual_hash = calculate_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_verify_checksum_success():
    """Test successful checksum verification."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        # Use the hash of "test content"
        expected_hash = "6ae8af4980b53463a51015abd5919e97bed0af072cf86078288040d8f7655c00"
        assert verify_checksum(temp_path, expected_hash) is True
    finally:
        os.unlink(temp_path)

def test_verify_checksum_failure():
    """Test failed checksum verification."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        assert verify_checksum(temp_path, wrong_hash) is False
    finally:
        os.unlink(temp_path)

@patch('data.download_ground_truth.requests.get')
def test_download_ground_truth_success(mock_get, tmp_path):
    """Test successful download."""
    mock_response = MagicMock()
    mock_response.text = '{"annotations": []}'
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    output_dir = tmp_path / "guava"
    output_file = download_ground_truth(output_dir, "http://fake-url.com/gt.json")

    assert output_file.exists()
    assert output_file.name == "ground_truth_annotations.json"
    mock_get.assert_called_once_with("http://fake-url.com/gt.json", timeout=60)

@patch('data.download_ground_truth.requests.get')
def test_download_ground_truth_failure(mock_get, tmp_path):
    """Test download failure raises DatasetUnavailableError."""
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

    output_dir = tmp_path / "guava"
    
    with pytest.raises(DatasetUnavailableError):
        download_ground_truth(output_dir, "http://fake-url.com/gt.json")
    
    assert not (output_dir / "ground_truth_annotations.json").exists()