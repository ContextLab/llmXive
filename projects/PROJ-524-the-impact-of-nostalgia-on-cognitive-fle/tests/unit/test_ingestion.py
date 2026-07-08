"""
Unit tests for the ingestion module.
"""
import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile
import os

# Mock the config and utils modules for testing
from unittest.mock import patch, MagicMock

@patch('ingestion.get_config')
@patch('ingestion.ensure_dirs')
@patch('ingestion.load_dataset')
@patch('ingestion.setup_logging')
def test_main_success(mock_setup_logging, mock_load_dataset, mock_ensure_dirs, mock_get_config):
    """Test that main() successfully loads and saves data."""
    # Setup mocks
    mock_get_config.return_value = {
        'raw_data_dir': 'data/raw',
        'data_source': 'local',
        'data_config': {'file_path': 'test.csv'}
    }
    mock_df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
    mock_load_dataset.return_value = (mock_df, None)
    
    # Import and run main
    from ingestion import main
    result = main()
    
    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    mock_ensure_dirs.assert_called_once()
    mock_load_dataset.assert_called_once()

@patch('ingestion.get_config')
@patch('ingestion.ensure_dirs')
@patch('ingestion.load_dataset')
@patch('ingestion.setup_logging')
def test_main_with_metadata(mock_setup_logging, mock_load_dataset, mock_ensure_dirs, mock_get_config):
    """Test that main() saves metadata when available."""
    # Setup mocks
    mock_get_config.return_value = {
        'raw_data_dir': 'data/raw',
        'data_source': 'local',
        'data_config': {'file_path': 'test.csv'}
    }
    mock_df = pd.DataFrame({'col1': [1, 2, 3]})
    mock_metadata = {'source': 'test', 'version': '1.0'}
    mock_load_dataset.return_value = (mock_df, mock_metadata)
    
    # Import and run main
    from ingestion import main
    result = main()
    
    # Assertions
    assert isinstance(result, pd.DataFrame)
    mock_ensure_dirs.assert_called_once()

def test_compute_sha256_integration():
    """Test that checksum computation works correctly."""
    from utils import compute_sha256
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = compute_sha256(Path(temp_path))
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex length
    finally:
        os.unlink(temp_path)

def test_verify_checksum():
    """Test checksum verification."""
    from utils import compute_sha256, verify_checksum
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = compute_sha256(Path(temp_path))
        assert verify_checksum(checksum, checksum) is True
        assert verify_checksum(checksum, "wrong_checksum") is False
    finally:
        os.unlink(temp_path)
