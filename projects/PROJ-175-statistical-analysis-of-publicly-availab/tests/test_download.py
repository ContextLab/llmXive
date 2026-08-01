import os
import json
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.download import (
    ensure_directories,
    load_verification_report,
    verify_url_status,
    DataUnavailableError,
    download_datasets
)

@pytest.fixture
def mock_verification_report(tmp_path):
    """Create a mock verification report."""
    report_path = tmp_path / "verification_report.json"
    report = {
        "status": "PASS",
        "datasets": [
            {
                "name": "recipe1m-full",
                "dataset_name": "recipe1m-full",
                "url": "https://huggingface.co/datasets/recipe1m-full",
                "status": "available"
            },
            {
                "name": "ratings",
                "dataset_name": "recipe1m-ratings",
                "url": "https://huggingface.co/datasets/recipe1m-ratings",
                "status": "available"
            }
        ]
    }
    with open(report_path, 'w') as f:
        json.dump(report, f)
    return str(report_path)

def test_ensure_directories(tmp_path):
    """Test that ensure_directories creates the required structure."""
    output_dir = tmp_path / "test_data"
    ensure_directories(str(output_dir))
    
    required_dirs = [
        "raw", "processed", "final", "logs"
    ]
    
    for d in required_dirs:
        assert (output_dir / d).exists(), f"Directory {d} was not created"

def test_load_verification_report_missing(mock_verification_report, tmp_path):
    """Test loading a missing verification report."""
    # Move the report to a different location to simulate missing
    missing_path = tmp_path / "nonexistent.json"
    
    with pytest.raises(FileNotFoundError):
        load_verification_report(str(missing_path))

def test_load_verification_report_success(mock_verification_report):
    """Test successful loading of verification report."""
    report = load_verification_report(mock_verification_report)
    
    assert report["status"] == "PASS"
    assert len(report["datasets"]) == 2
    assert report["datasets"][0]["name"] == "recipe1m-full"

def test_verify_url_status_success():
    """Test URL verification with successful responses."""
    urls = [
        {"url": "https://httpbin.org/status/200"},
        {"url": "https://httpbin.org/status/200"}
    ]
    
    # Note: This test might be flaky depending on network, so we mock
    with patch('data.download.requests.head') as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        result = verify_url_status(urls)
        assert result is True
        assert mock_head.call_count == 2

def test_verify_url_status_failure():
    """Test URL verification with failed responses."""
    urls = [
        {"url": "https://httpbin.org/status/404"}
    ]
    
    with patch('data.download.requests.head') as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        result = verify_url_status(urls)
        assert result is False

@pytest.mark.integration
def test_download_datasets_pilot(mock_verification_report, tmp_path):
    """
    Integration test for pilot dataset download.
    This test requires network access and the actual HuggingFace dataset.
    """
    # This is an integration test that would require real data
    # For unit testing purposes, we'll mock the download process
    pass

def test_download_datasets_missing_verification(tmp_path):
    """Test download_datasets when verification report is missing."""
    with pytest.raises(FileNotFoundError):
        download_datasets(output_dir=str(tmp_path / "raw"))

def test_download_datasets_no_records(tmp_path, mock_verification_report):
    """Test download_datasets when no records are streamed."""
    # Mock the load_dataset to return an empty iterator
    with patch('data.download.load_dataset') as mock_load:
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = lambda self: iter([])
        mock_load.return_value = mock_dataset
        
        with pytest.raises(DataUnavailableError) as exc_info:
            download_datasets(pilot_size=10, output_dir=str(tmp_path / "raw"))
        
        assert "Failed to stream any records" in str(exc_info.value)