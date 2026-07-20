import os
import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add code to path if not running as package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.status_writer import write_data_status

@pytest.fixture
def temp_csv(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_path = tmp_path / "test_data.csv"
    df = pd.DataFrame({
        'yield_strength': [100, 200, 300],
        'delta': [1.0, 2.0, 3.0]
    })
    df.to_csv(csv_path, index=False)
    return str(csv_path)

def test_write_data_status_normal(tmp_path, temp_csv):
    """Test writing status when N >= 500 (simulated with mock data count)"""
    # Create a mock dataframe with 600 rows
    with patch('pandas.read_csv') as mock_read:
        mock_df = pd.DataFrame({'col': range(600)})
        mock_read.return_value = mock_df
        
        json_path = str(tmp_path / "status.json")
        status = write_data_status(temp_csv, json_path)
        
        assert status['n_samples'] == 600
        assert status['count_warning'] is False
        assert status['power_status'] == 'sufficient'
        assert os.path.exists(json_path)

def test_write_data_status_warning(tmp_path, temp_csv):
    """Test writing status when N < 500"""
    with patch('pandas.read_csv') as mock_read:
        mock_df = pd.DataFrame({'col': range(100)})
        mock_read.return_value = mock_df
        
        json_path = str(tmp_path / "status.json")
        status = write_data_status(temp_csv, json_path)
        
        assert status['n_samples'] == 100
        assert status['count_warning'] is True
        assert status['power_status'] == 'sufficient'

def test_write_data_status_insufficient_power(tmp_path, temp_csv):
    """Test writing status when N < 50"""
    with patch('pandas.read_csv') as mock_read:
        mock_df = pd.DataFrame({'col': range(20)})
        mock_read.return_value = mock_df
        
        json_path = str(tmp_path / "status.json")
        status = write_data_status(temp_csv, json_path)
        
        assert status['n_samples'] == 20
        assert status['count_warning'] is True
        assert status['power_status'] == 'insufficient_power'

def test_file_not_found(tmp_path):
    """Test error handling for missing CSV"""
    json_path = str(tmp_path / "status.json")
    with pytest.raises(FileNotFoundError):
        write_data_status("non_existent.csv", json_path)