"""
Tests for the ingestion module, specifically focusing on T012 edge case handling.
"""
import os
import sys
import tempfile
import json
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.ingestion import process_draws, load_config
from code.exceptions import LotteryDataError

@pytest.fixture
def mock_config():
    """Create a mock configuration file."""
    config = {
        "source_name": "Test Lottery",
        "url": "http://example.com/lottery.csv"
    }
    return config

@pytest.fixture
def temp_csv_with_missing_sales():
    """Create a temporary CSV file with missing total_sales values."""
    data = {
        'draw_date': ['2023-01-01', '2023-01-08', '2023-01-15', '2023-01-22'],
        'numbers': [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12], [13, 14, 15, 16, 17, 18], [19, 20, 21, 22, 23, 24]],
        'jackpot_amount': [1000000, 2000000, 5000000, 1500000],
        'total_sales': [100000, None, 300000, None]  # Two missing values
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)

@pytest.fixture
def temp_csv_without_sales_column():
    """Create a temporary CSV file without total_sales column."""
    data = {
        'draw_date': ['2023-01-01', '2023-01-08'],
        'numbers': [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]],
        'jackpot_amount': [1000000, 2000000]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)

def test_process_draws_with_missing_sales(temp_csv_with_missing_sales, caplog):
    """Test that process_draws handles missing total_sales correctly (T012)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, 'processed.csv')
        
        # Process the data
        df = process_draws(temp_csv_with_missing_sales, output_path)
        
        # Verify warnings were logged
        assert any("missing 'total_sales'" in record.message for record in caplog.records)
        
        # Verify the output file exists
        assert os.path.exists(output_path)
        
        # Verify all rows are retained
        assert len(df) == 4
        
        # Verify missing sales are NaN
        assert df['total_sales'].isna().sum() == 2
        
        # Verify rows with missing sales are still present (for frequency analysis)
        assert not df.empty

def test_process_draws_without_sales_column(temp_csv_without_sales_column, caplog):
    """Test that process_draws handles missing column gracefully (T012)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, 'processed.csv')
        
        # Process the data
        df = process_draws(temp_csv_without_sales_column, output_path)
        
        # Verify warning was logged
        assert any("Column 'total_sales' not found" in record.message for record in caplog.records)
        
        # Verify the output file exists
        assert os.path.exists(output_path)
        
        # Verify all rows are retained
        assert len(df) == 2
        
        # Verify total_sales column was added with NaN
        assert 'total_sales' in df.columns
        assert df['total_sales'].isna().all()

def test_process_draws_empty_data():
    """Test that process_draws raises error for empty data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, 'empty.csv')
        output_path = os.path.join(temp_dir, 'processed.csv')
        
        # Create empty CSV
        pd.DataFrame(columns=['draw_date']).to_csv(input_path, index=False)
        
        with pytest.raises(LotteryDataError, match="Loaded data is empty"):
            process_draws(input_path, output_path)

def test_process_draws_preserves_data_integrity(temp_csv_with_missing_sales):
    """Test that process_draws preserves non-sales data integrity."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, 'processed.csv')
        
        df = process_draws(temp_csv_with_missing_sales, output_path)
        
        # Verify original columns are preserved
        assert 'draw_date' in df.columns
        assert 'numbers' in df.columns
        assert 'jackpot_amount' in df.columns
        
        # Verify data types are correct
        assert df['draw_date'].dtype == 'object'
        assert df['jackpot_amount'].dtype in ['int64', 'float64']

def test_output_file_format(temp_csv_with_missing_sales):
    """Test that output file is a valid CSV."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, 'processed.csv')
        
        process_draws(temp_csv_with_missing_sales, output_path)
        
        # Try to load the output file
        output_df = pd.read_csv(output_path)
        
        # Verify it can be loaded and has correct structure
        assert len(output_df) == 4
        assert 'total_sales' in output_df.columns