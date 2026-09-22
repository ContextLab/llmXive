"""
Unit tests for T070b: verify_columns.py
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Mock the ingestion module to avoid real network calls during unit tests
@pytest.fixture
def mock_df():
    """Create a mock DataFrame with the expected schema."""
    data = {
        'age': [18, 19, 20],
        'gender': ['M', 'F', 'Other'],
        'social_support': [5, 4, 3],
        'harassment_severity': [2, 5, 1],
        'platform': ['Twitter', 'Instagram', 'TikTok'],
        'depression': [10, 15, 5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_df_no_platform():
    """Create a mock DataFrame without the platform column."""
    data = {
        'age': [18, 19, 20],
        'gender': ['M', 'F', 'Other'],
        'social_support': [5, 4, 3],
        'harassment_severity': [2, 5, 1],
        'depression': [10, 15, 5]
    }
    return pd.DataFrame(data)

def test_verify_platform_present(mock_df, tmp_path, monkeypatch):
    """Test that the script correctly identifies the presence of the 'platform' column."""
    # Patch the load_cyber_data function
    with patch('data.verify_columns.load_cyber_data', return_value=mock_df):
        # Patch the output path to use a temp directory
        with patch('data.verify_columns.Path') as mock_path_class:
            mock_output_dir = MagicMock()
            mock_output_path = tmp_path / "platform_status.json"
            mock_output_dir.__truediv__.return_value = mock_output_path
            mock_path_class.return_value = mock_output_dir
            mock_output_dir.mkdir = MagicMock()
            
            # Import and run the function
            from data.verify_columns import verify_platform_column
            result = verify_platform_column()
            
            # Assertions
            assert result['platform_exists'] is True
            assert 'platform_categories' in result
            assert len(result['platform_categories']) == 3
            
            # Verify the file was written
            assert mock_output_dir.mkdir.called
            
            # Read the actual file content if we can simulate the write
            # Since we mocked Path, we check the logic result primarily
            assert result['platform_categories'] == ['Twitter', 'Instagram', 'TikTok']

def test_verify_platform_missing(mock_df_no_platform, tmp_path, monkeypatch):
    """Test that the script correctly identifies the absence of the 'platform' column."""
    with patch('data.verify_columns.load_cyber_data', return_value=mock_df_no_platform):
        with patch('data.verify_columns.Path') as mock_path_class:
            mock_output_dir = MagicMock()
            mock_output_path = tmp_path / "platform_status.json"
            mock_output_dir.__truediv__.return_value = mock_output_path
            mock_path_class.return_value = mock_output_dir
            mock_output_dir.mkdir = MagicMock()
            
            from data.verify_columns import verify_platform_column
            result = verify_platform_column()
            
            assert result['platform_exists'] is False
            assert result['platform_categories'] == []

def test_verify_empty_df(tmp_path):
    """Test that the script raises an error on empty data."""
    empty_df = pd.DataFrame()
    
    with patch('data.verify_columns.load_cyber_data', return_value=empty_df):
        with patch('data.verify_columns.Path'):
            from data.verify_columns import verify_platform_column
            with pytest.raises(RuntimeError, match="E-EMPTY-DATA"):
                verify_platform_column()