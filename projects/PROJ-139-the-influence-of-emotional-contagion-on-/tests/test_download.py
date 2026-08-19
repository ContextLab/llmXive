import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
from data.download import (
    ensure_directories, 
    log_download_attempt, 
    compute_sha256, 
    fetch_from_pushshift,
    download_data,
    validate_origin_types,
    main
)
from config.settings import Config, DatasetPaths, APIKeys

@pytest.fixture
def temp_config():
    """Create a temporary config for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config = Config(
            project_root=tmp_path,
            raw_dir=tmp_path / "data" / "raw",
            processed_dir=tmp_path / "data" / "processed",
            state_dir=tmp_path / "state",
            docs_dir=tmp_path / "docs"
        )
        yield config

def test_ensure_directories(temp_config):
    ensure_directories(temp_config)
    assert temp_config.raw_dir.exists()
    assert temp_config.processed_dir.exists()
    assert temp_config.state_dir.exists()

def test_log_download_attempt(temp_config):
    log_download_attempt(
        temp_config, 
        thread_id="test_123", 
        origin_type="Pushshift", 
        success=True, 
        message="Success"
    )
    log_path = temp_config.processed_dir / "download_attempts.log"
    assert log_path.exists()
    with open(log_path, 'r') as f:
        line = f.readline()
        data = json.loads(line)
        assert data["thread_id"] == "test_123"
        assert data["origin_type"] == "Pushshift"
        assert data["success"] is True

def test_compute_sha256(temp_config):
    test_file = temp_config.raw_dir / "test.txt"
    test_content = "Hello, World!"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    checksum = compute_sha256(test_file)
    assert len(checksum) == 64
    assert checksum == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

@patch('data.download.requests.get')
def test_fetch_from_pushshift(mock_get, temp_config):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "1", "title": "Test", "subreddit": "test"},
            {"id": "2", "title": "Test2", "subreddit": "test"}
        ]
    }
    mock_get.return_value = mock_response

    result = fetch_from_pushshift("test", limit=10)
    assert len(result) == 2
    assert result[0]["id"] == "1"

@patch('data.download.fetch_from_pushshift')
@patch('data.download.fetch_from_reddit_api')
@patch('data.download.fetch_from_internet_archive')
def test_download_data_success(mock_archive, mock_reddit, mock_pushshift, temp_config):
    mock_pushshift.return_value = [{"id": "1", "title": "Test"}]
    mock_reddit.return_value = None
    mock_archive.return_value = None

    output_file = temp_config.raw_dir / "test_output.jsonl"
    log_file = temp_config.processed_dir / "test_log.log"

    count = download_data("test", output_file, log_file)
    assert count == 1
    assert output_file.exists()
    with open(output_file, 'r') as f:
        line = f.readline()
        data = json.loads(line)
        assert data["origin_type"] == "Pushshift"

@patch('data.download.fetch_from_pushshift')
@patch('data.download.fetch_from_reddit_api')
@patch('data.download.fetch_from_internet_archive')
def test_download_data_failure(mock_archive, mock_reddit, mock_pushshift, temp_config):
    mock_pushshift.return_value = None
    mock_reddit.return_value = None
    mock_archive.return_value = None

    output_file = temp_config.raw_dir / "test_output.jsonl"
    log_file = temp_config.processed_dir / "test_log.log"

    with pytest.raises(RuntimeError) as excinfo:
        download_data("test", output_file, log_file)
    
    assert "CRITICAL FAILURE" in str(excinfo.value)

def test_validate_origin_types(temp_config):
    # Create a valid raw file
    raw_file = temp_config.raw_dir / "reddit_threads.jsonl"
    with open(raw_file, 'w') as f:
        f.write(json.dumps({"id": "1", "origin_type": "Pushshift"}) + '\n')
        f.write(json.dumps({"id": "2", "origin_type": "Reddit API"}) + '\n')
    
    assert validate_origin_types(temp_config) is True

def test_validate_origin_types_missing(temp_config):
    # Create a raw file with missing origin_type
    raw_file = temp_config.raw_dir / "reddit_threads.jsonl"
    with open(raw_file, 'w') as f:
        f.write(json.dumps({"id": "1"}) + '\n')
        f.write(json.dumps({"id": "2", "origin_type": "Pushshift"}) + '\n')
    
    assert validate_origin_types(temp_config) is False