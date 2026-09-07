"""
Unit tests for the proxy_saver module.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

from code.services.proxy_saver import save_proxy_results, run_proxy_saver_pipeline

@pytest.fixture
def sample_proxy_data():
    return [
        {
            'post_id': '1001',
            'user_id': 'user_123',
            'control_proxy': 0.85,
            'timestamp_regularity': 0.92
        },
        {
            'post_id': '1002',
            'user_id': 'user_456',
            'control_proxy': 0.12,
            'timestamp_regularity': 0.45
        },
        {
            'post_id': '1003',
            'user_id': 'user_789',
            'control_proxy': 0.50,
            'timestamp_regularity': 0.60
        }
    ]

@pytest.fixture
def temp_output_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_proxy_results.csv"

def test_save_proxy_results_creates_file(sample_proxy_data, temp_output_path):
    """Test that save_proxy_results creates the file and writes data correctly."""
    save_proxy_results(sample_proxy_data, temp_output_path)
    
    assert temp_output_path.exists(), "Output file was not created."
    
    df = pd.read_csv(temp_output_path)
    
    assert len(df) == 3, "Incorrect number of rows saved."
    assert list(df.columns) == ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity'], \
        "Columns do not match expected schema."
    
    assert df['post_id'].iloc[0] == '1001'
    assert df['control_proxy'].iloc[0] == 0.85

def test_save_proxy_results_empty_data(temp_output_path):
    """Test that save_proxy_results handles empty data gracefully."""
    save_proxy_results([], temp_output_path)
    
    assert temp_output_path.exists(), "Output file was not created for empty data."
    
    df = pd.read_csv(temp_output_path)
    assert len(df) == 0, "Expected empty DataFrame."
    assert list(df.columns) == ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity'], \
        "Headers should still be present for empty data."

def test_save_proxy_results_missing_columns_raises_error(temp_output_path):
    """Test that missing required columns raise an error."""
    bad_data = [
        {'post_id': '1001', 'user_id': 'u1'} # Missing control_proxy and timestamp_regularity
    ]
    
    with pytest.raises(ValueError, match="Missing expected column"):
        save_proxy_results(bad_data, temp_output_path)

def test_save_proxy_results_column_order(temp_output_path, sample_proxy_data):
    """Verify columns are saved in the specific order defined in T026."""
    save_proxy_results(sample_proxy_data, temp_output_path)
    df = pd.read_csv(temp_output_path)
    expected_order = ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity']
    assert list(df.columns) == expected_order, f"Column order mismatch: {list(df.columns)} vs {expected_order}"