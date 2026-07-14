"""
Unit tests for download_datasets.py
Tests the download functionality without actually downloading files.
"""
import pytest
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add the code/src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.download_datasets import (
    DownloadResult,
    compute_file_checksum,
    load_search_results,
    download_electricity_dataset,
    download_traffic_dataset,
    download_nab_dataset,
    main
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path

@pytest.fixture
def mock_search_results(temp_dir):
    """Create mock search results file."""
    search_results = {
        "status": "SUCCESS",
        "datasets": [
            {"name": "electricity", "type": "UCI", "url": "http://example.com/electricity.csv"},
            {"name": "traffic", "type": "UCI", "url": "http://example.com/traffic.csv"}
        ],
        "search_query": "anomaly detection time series",
        "result_count": 2
    }
    search_path = temp_dir / "search_results.json"
    with open(search_path, 'w') as f:
        json.dump(search_results, f)
    return search_path

def test_download_result_dataclass():
    """Test that DownloadResult dataclass works correctly."""
    result = DownloadResult(
        dataset_name="test",
        source="test_source",
        url="http://example.com",
        local_path="/tmp/test.csv",
        checksum="abc123",
        status="success"
    )
    
    assert result.dataset_name == "test"
    assert result.source == "test_source"
    assert result.url == "http://example.com"
    assert result.local_path == "/tmp/test.csv"
    assert result.checksum == "abc123"
    assert result.status == "success"
    assert result.error_message is None

def test_compute_file_checksum(temp_dir):
    """Test checksum computation on a real file."""
    test_file = temp_dir / "test.txt"
    test_content = "Hello, World!"
    test_file.write_text(test_content)
    
    checksum = compute_file_checksum(str(test_file))
    
    # SHA256 of "Hello, World!"
    expected_checksum = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert checksum == expected_checksum

def test_compute_file_checksum_not_found(temp_dir):
    """Test checksum computation on non-existent file."""
    non_existent = temp_dir / "non_existent.txt"
    checksum = compute_file_checksum(str(non_existent))
    assert checksum == "FILE_NOT_FOUND"

def test_load_search_results_success(temp_dir, mock_search_results):
    """Test successful loading of search results."""
    # Temporarily change the global path
    import data.download_datasets as dd
    original_path = dd.SEARCH_RESULTS_PATH
    dd.SEARCH_RESULTS_PATH = mock_search_results
    
    try:
        results = load_search_results()
        assert results is not None
        assert results["status"] == "SUCCESS"
        assert len(results["datasets"]) == 2
    finally:
        dd.SEARCH_RESULTS_PATH = original_path

def test_load_search_results_file_not_found(temp_dir):
    """Test loading search results when file doesn't exist."""
    import data.download_datasets as dd
    original_path = dd.SEARCH_RESULTS_PATH
    dd.SEARCH_RESULTS_PATH = temp_dir / "non_existent.json"
    
    try:
        results = load_search_results()
        assert results is None
    finally:
        dd.SEARCH_RESULTS_PATH = original_path

@patch('data.download_datasets.download_from_url')
@patch('data.download_datasets.compute_file_checksum')
def test_download_electricity_dataset_success(mock_checksum, mock_download, temp_dir):
    """Test successful electricity dataset download."""
    mock_download.return_value = True
    mock_checksum.return_value = "test_checksum"
    
    import data.download_datasets as dd
    original_raw_dir = dd.DATA_RAW_DIR
    dd.DATA_RAW_DIR = temp_dir / "raw"
    dd.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        result = download_electricity_dataset()
        assert result.status == "success"
        assert result.dataset_name == "Electricity Load Diagrams"
        assert result.checksum == "test_checksum"
    finally:
        dd.DATA_RAW_DIR = original_raw_dir

@patch('data.download_datasets.download_from_url')
def test_download_electricity_dataset_failure(mock_download, temp_dir):
    """Test failed electricity dataset download."""
    mock_download.return_value = False
    
    import data.download_datasets as dd
    original_raw_dir = dd.DATA_RAW_DIR
    dd.DATA_RAW_DIR = temp_dir / "raw"
    dd.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        result = download_electricity_dataset()
        assert result.status == "failed"
        assert result.error_message == "Download failed"
    finally:
        dd.DATA_RAW_DIR = original_raw_dir

@patch('data.download_datasets.download_from_url')
@patch('data.download_datasets.compute_file_checksum')
def test_download_traffic_dataset_success(mock_checksum, mock_download, temp_dir):
    """Test successful traffic dataset download."""
    mock_download.return_value = True
    mock_checksum.return_value = "test_checksum"
    
    import data.download_datasets as dd
    original_raw_dir = dd.DATA_RAW_DIR
    dd.DATA_RAW_DIR = temp_dir / "raw"
    dd.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        result = download_traffic_dataset()
        assert result.status == "success"
        assert result.dataset_name == "Traffic"
    finally:
        dd.DATA_RAW_DIR = original_raw_dir

@patch('data.download_datasets.download_from_url')
def test_download_nab_dataset_success(mock_download, temp_dir):
    """Test successful NAB dataset download."""
    mock_download.return_value = True
    
    import data.download_datasets as dd
    original_raw_dir = dd.DATA_RAW_DIR
    dd.DATA_RAW_DIR = temp_dir / "raw"
    dd.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        result = download_nab_dataset("test_dataset")
        assert result.status == "success"
        assert result.dataset_name == "test_dataset"
        assert result.source == "NAB"
    finally:
        dd.DATA_RAW_DIR = original_raw_dir

def test_main_no_search_results(temp_dir, caplog):
    """Test main function when search results are missing."""
    import data.download_datasets as dd
    
    original_search_path = dd.SEARCH_RESULTS_PATH
    original_manifest_path = dd.DOWNLOAD_MANIFEST_PATH
    original_raw_dir = dd.DATA_RAW_DIR
    original_processed_dir = dd.PROCESSED_RESULTS_DIR
    
    dd.SEARCH_RESULTS_PATH = temp_dir / "non_existent.json"
    dd.DOWNLOAD_MANIFEST_PATH = temp_dir / "manifest.json"
    dd.DATA_RAW_DIR = temp_dir / "raw"
    dd.PROCESSED_RESULTS_DIR = temp_dir / "processed"
    
    dd.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    dd.PROCESSED_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        result = main()
        assert result == 1
        
        # Check that manifest was created
        assert dd.DOWNLOAD_MANIFEST_PATH.exists()
        
        with open(dd.DOWNLOAD_MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
        
        assert manifest["status"] == "aborted"
        assert "T052b search failed" in manifest["reason"]
    finally:
        dd.SEARCH_RESULTS_PATH = original_search_path
        dd.DOWNLOAD_MANIFEST_PATH = original_manifest_path
        dd.DATA_RAW_DIR = original_raw_dir
        dd.PROCESSED_RESULTS_DIR = original_processed_dir

def test_main_search_failed(temp_dir, caplog):
    """Test main function when search failed."""
    import data.download_datasets as dd
    
    # Create failed search results
    search_data = {
        "status": "FAILED",
        "reason": "No datasets found"
    }
    search_path = temp_dir / "search_results.json"
    with open(search_path, 'w') as f:
        json.dump(search_data, f)
    
    original_search_path = dd.SEARCH_RESULTS_PATH
    original_manifest_path = dd.DOWNLOAD_MANIFEST_PATH
    original_raw_dir = dd.DATA_RAW_DIR
    original_processed_dir = dd.PROCESSED_RESULTS_DIR
    
    dd.SEARCH_RESULTS_PATH = search_path
    dd.DOWNLOAD_MANIFEST_PATH = temp_dir / "manifest.json"
    dd.DATA_RAW_DIR = temp_dir / "raw"
    dd.PROCESSED_RESULTS_DIR = temp_dir / "processed"
    
    dd.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    dd.PROCESSED_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        result = main()
        assert result == 1
        
        # Check that manifest was created
        assert dd.DOWNLOAD_MANIFEST_PATH.exists()
        
        with open(dd.DOWNLOAD_MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
        
        assert manifest["status"] == "aborted"
        assert "No datasets found" in manifest["reason"]
    finally:
        dd.SEARCH_RESULTS_PATH = original_search_path
        dd.DOWNLOAD_MANIFEST_PATH = original_manifest_path
        dd.DATA_RAW_DIR = original_raw_dir
        dd.PROCESSED_RESULTS_DIR = original_processed_dir