"""
Unit tests for proxy_saver.py service.

Tests T026: Saving extracted proxies to CSV
"""

import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

from code.services.proxy_saver import save_proxy_results
from code.config import CONFIG

@pytest.fixture
def sample_proxy_data():
    """Sample proxy data for testing."""
    return [
        {
            'post_id': '12345',
            'user_id': 'user_001',
            'control_proxy': 0.8,
            'timestamp_regularity': 0.95
        },
        {
            'post_id': '12346',
            'user_id': 'user_001',
            'control_proxy': 0.6,
            'timestamp_regularity': 0.85
        },
        {
            'post_id': '12347',
            'user_id': 'user_002',
            'control_proxy': 0.9,
            'timestamp_regularity': 0.90
        }
    ]

@pytest.fixture
def temp_output_path():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        yield Path(f.name)
    os.unlink(f.name)

def test_save_proxy_results_creates_file(sample_proxy_data, temp_output_path):
    """Test that save_proxy_results creates the output file."""
    result_path = save_proxy_results(sample_proxy_data, temp_output_path)
    
    assert result_path.exists()
    assert result_path == temp_output_path

def test_save_proxy_results_correct_columns(sample_proxy_data, temp_output_path):
    """Test that saved CSV has correct columns."""
    save_proxy_results(sample_proxy_data, temp_output_path)
    
    df = pd.read_csv(temp_output_path)
    
    expected_columns = ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity']
    assert list(df.columns) == expected_columns

def test_save_proxy_results_correct_data(sample_proxy_data, temp_output_path):
    """Test that saved CSV contains correct data."""
    save_proxy_results(sample_proxy_data, temp_output_path)
    
    df = pd.read_csv(temp_output_path)
    
    assert len(df) == len(sample_proxy_data)
    assert df.iloc[0]['post_id'] == '12345'
    assert df.iloc[0]['user_id'] == 'user_001'
    assert df.iloc[0]['control_proxy'] == 0.8
    assert df.iloc[0]['timestamp_regularity'] == 0.95

def test_save_proxy_results_empty_data_raises_error(temp_output_path):
    """Test that saving empty data raises ValueError."""
    with pytest.raises(ValueError, match="Cannot save empty proxy data"):
        save_proxy_results([], temp_output_path)

def test_save_proxy_results_none_data_raises_error(temp_output_path):
    """Test that saving None data raises ValueError."""
    with pytest.raises(ValueError, match="Cannot save empty proxy data"):
        save_proxy_results(None, temp_output_path)

def test_save_proxy_results_missing_columns_raises_error(temp_output_path):
    """Test that missing columns raise ValueError."""
    incomplete_data = [
        {
            'post_id': '12345',
            'user_id': 'user_001'
            # Missing control_proxy and timestamp_regularity
        }
    ]
    
    with pytest.raises(ValueError, match="Missing required columns"):
        save_proxy_results(incomplete_data, temp_output_path)

def test_save_proxy_results_creates_directory(temp_output_path):
    """Test that save_proxy_results creates parent directory if needed."""
    # Remove parent directory if it exists
    parent_dir = temp_output_path.parent
    if parent_dir.exists():
        import shutil
        shutil.rmtree(parent_dir)
    
    result_path = save_proxy_results(
        [
            {
                'post_id': '12345',
                'user_id': 'user_001',
                'control_proxy': 0.8,
                'timestamp_regularity': 0.95
            }
        ],
        temp_output_path
    )
    
    assert result_path.exists()

def test_save_proxy_results_default_path(sample_proxy_data):
    """Test that save_proxy_results uses CONFIG.PROXY_RESULTS_PATH by default."""
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "test_proxy_results.csv"
        
        # Temporarily override CONFIG
        original_path = CONFIG.PROXY_RESULTS_PATH
        CONFIG.PROXY_RESULTS_PATH = test_path
        
        try:
            result_path = save_proxy_results(sample_proxy_data)
            assert result_path == test_path
            assert result_path.exists()
        finally:
            CONFIG.PROXY_RESULTS_PATH = original_path
