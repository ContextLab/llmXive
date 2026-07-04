"""
Unit tests for data download functionality.

Tests retry logic, column validation, and error handling.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.download import (
    validate_columns,
    download_with_retry,
    compute_file_hash,
    REQUIRED_COLUMNS,
    MAX_RETRIES
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with required columns."""
    return pd.DataFrame({
        "composition": ["As20Se80", "Ge20Se80", "Sb20Se80"],
        "Tg": [250.5, 260.3, 245.1],
        "other_col": ["a", "b", "c"]
    })

@pytest.fixture
def incomplete_df():
    """Create a DataFrame missing required columns."""
    return pd.DataFrame({
        "composition": ["As20Se80", "Ge20Se80"],
        "other_col": ["a", "b"]
    })

def test_validate_columns_success(sample_df):
    """Test validation when all required columns are present."""
    is_valid, missing_col = validate_columns(sample_df, REQUIRED_COLUMNS)
    assert is_valid is True
    assert missing_col is None

def test_validate_columns_missing_column(incomplete_df):
    """Test validation when a required column is missing."""
    is_valid, missing_col = validate_columns(incomplete_df, REQUIRED_COLUMNS)
    assert is_valid is False
    assert missing_col == "Tg"

def test_validate_columns_multiple_missing():
    """Test validation when multiple required columns are missing."""
    df = pd.DataFrame({"other": [1, 2, 3]})
    is_valid, missing_col = validate_columns(df, REQUIRED_COLUMNS)
    assert is_valid is False
    assert missing_col == "composition"  # First missing column

@patch('src.data.download.requests.get')
def test_download_with_retry_success(mock_get, sample_df, temp_dir):
    """Test successful download with retry logic."""
    # Mock response
    mock_response = MagicMock()
    mock_response.text = sample_df.to_csv(index=False)
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    # Change to temp dir to avoid side effects
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        result = download_with_retry("http://test.com/data.csv")
        assert result is not None
        assert len(result) == 3
        assert "composition" in result.columns
    finally:
        os.chdir(original_cwd)

@patch('src.data.download.requests.get')
def test_download_with_retry_timeout(mock_get, temp_dir):
    """Test retry logic on timeout."""
    from requests.exceptions import Timeout
    
    # First two attempts timeout, third succeeds
    mock_response = MagicMock()
    mock_response.text = "composition,Tg\nAs20Se80,250.5"
    mock_response.raise_for_status = MagicMock()
    
    mock_get.side_effect = [
        Timeout(),
        Timeout(),
        mock_response
    ]

    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        result = download_with_retry("http://test.com/data.csv", max_retries=3)
        assert result is not None
        assert len(mock_get.call_args_list) == 3  # Called 3 times
    finally:
        os.chdir(original_cwd)

@patch('src.data.download.requests.get')
def test_download_with_retry_failure(mock_get, temp_dir):
    """Test download fails after max retries."""
    from requests.exceptions import RequestException
    
    mock_get.side_effect = RequestException("Network error")

    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        result = download_with_retry("http://test.com/data.csv", max_retries=2)
        assert result is None
        assert len(mock_get.call_args_list) == 2  # Called max_retries times
    finally:
        os.chdir(original_cwd)

def test_compute_file_hash(temp_dir):
    """Test file hash computation."""
    test_file = temp_dir / "test.txt"
    test_content = "test content"
    test_file.write_text(test_content)
    
    hash1 = compute_file_hash(test_file)
    hash2 = compute_file_hash(test_file)
    
    assert len(hash1) == 64  # SHA-256 hex length
    assert hash1 == hash2  # Deterministic

def test_compute_file_hash_not_found():
    """Test hash computation for non-existent file."""
    result = compute_file_hash(Path("/nonexistent/file.txt"))
    assert result == "FILE_NOT_FOUND"