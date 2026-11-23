"""
Unit tests for the ingestion module.
"""
import os
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from ingestion import load_config, process_draws
from exceptions import LotteryDataError

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def mock_config_file(temp_dir):
    """Create a mock config file."""
    config_path = os.path.join(temp_dir, 'data_sources.json')
    config_data = {
        "source_name": "Test Source",
        "url": "http://example.com/data.csv"
    }
    with open(config_path, 'w') as f:
        json.dump(config_data, f)
    return config_path

@pytest.fixture
def mock_raw_csv(temp_dir):
    """Create a mock raw CSV file with missing sales data."""
    csv_path = os.path.join(temp_dir, 'raw.csv')
    data = {
        'draw_date': ['2023-01-01', '2023-01-08', '2023-01-15'],
        'ball_1': [1, 2, 3],
        'ball_2': [2, 3, 4],
        'ball_3': [3, 4, 5],
        'ball_4': [4, 5, 6],
        'ball_5': [5, 6, 7],
        'ball_6': [6, 7, 8],
        'total_sales': [1000000, None, 1200000]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

def test_load_config_success(mock_config_file):
    """Test loading a valid config file."""
    # Mock the config path resolution
    with patch('ingestion.os.path.join', return_value=mock_config_file):
        config = load_config()
        assert config['source_name'] == 'Test Source'
        assert config['url'] == 'http://example.com/data.csv'

def test_load_config_missing_file():
    """Test loading a missing config file raises error."""
    with patch('ingestion.os.path.exists', return_value=False):
        with pytest.raises(FileNotFoundError):
            load_config()

def test_process_draws_missing_sales(mock_raw_csv, temp_dir):
    """Test processing data with missing total_sales values."""
    processed_path = os.path.join(temp_dir, 'processed.csv')
    
    df = process_draws(mock_raw_csv, processed_path)
    
    # Check that the DataFrame is not empty
    assert not df.empty
    
    # Check that total_sales column exists
    assert 'total_sales' in df.columns
    
    # Check that the row with missing sales is retained (count is 3)
    assert len(df) == 3
    
    # Check that the missing value is NaN
    assert pd.isna(df.loc[1, 'total_sales'])
    
    # Check that the processed file was created
    assert os.path.exists(processed_path)

def test_process_draws_empty_data(temp_dir):
    """Test processing empty data raises error."""
    csv_path = os.path.join(temp_dir, 'empty.csv')
    pd.DataFrame(columns=['draw_date', 'ball_1']).to_csv(csv_path, index=False)
    
    processed_path = os.path.join(temp_dir, 'processed.csv')
    
    with pytest.raises(LotteryDataError):
        process_draws(csv_path, processed_path)

def test_process_draws_missing_column(mock_raw_csv, temp_dir):
    """Test processing data without total_sales column."""
    # Load data and drop the column
    df = pd.read_csv(mock_raw_csv)
    df_no_sales = df.drop(columns=['total_sales'])
    
    missing_sales_path = os.path.join(temp_dir, 'no_sales.csv')
    df_no_sales.to_csv(missing_sales_path, index=False)
    
    processed_path = os.path.join(temp_dir, 'processed.csv')
    
    # Should not raise, but should add column with NaN
    df_result = process_draws(missing_sales_path, processed_path)
    
    assert 'total_sales' in df_result.columns
    assert df_result['total_sales'].isna().all()