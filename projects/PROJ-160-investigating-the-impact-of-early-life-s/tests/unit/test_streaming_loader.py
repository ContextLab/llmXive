"""
Unit tests for the streaming data loader.

Tests verify that:
1. Column selection works correctly
2. Chunked loading yields correct row counts
3. Memory optimization functions as expected
4. Error handling for missing files/columns works
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from code.data.streaming_loader import (
    load_cleaned_dataset_chunked,
    load_cleaned_dataset_full_optimized,
    get_required_columns,
    process_and_save_subset,
    REQUIRED_COLUMNS
)
from code.config import get_processed_dir

@pytest.fixture
def mock_csv_data(tmp_path):
    """Create a temporary CSV file with mock data for testing."""
    # Create a mock cleaned_dataset.csv
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = data_dir / "cleaned_dataset.csv"
    
    # Create sample data
    n_rows = 100
    data = {
        'ACE': np.random.randn(n_rows),
        'Age': np.random.randint(9, 11, n_rows),
        'Sex': np.random.choice(['M', 'F'], n_rows),
        'Site': np.random.choice(['Site1', 'Site2'], n_rows),
        'FamilyID': np.random.randint(1, 20, n_rows),
        'CA3': np.random.randn(n_rows),
        'DG': np.random.randn(n_rows),
        'Subiculum': np.random.randn(n_rows),
        'ICV': np.random.randn(n_rows) * 1000 + 1500,
        'ExtraColumn': np.random.randn(n_rows)  # Column that should be ignored
    }
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    
    return file_path, tmp_path

def test_get_required_columns():
    """Test that required columns are returned correctly."""
    cols = get_required_columns()
    assert isinstance(cols, list)
    assert 'ACE' in cols
    assert 'CA3' in cols
    assert 'ExtraColumn' not in cols

def test_load_full_optimized_missing_columns(mock_csv_data):
    """Test loading with specific columns excludes unnecessary ones."""
    file_path, _ = mock_csv_data
    
    # Patch get_processed_dir to return our temp dir
    with patch('code.data.streaming_loader.get_processed_dir', return_value=file_path.parent):
        df = load_cleaned_dataset_full_optimized(columns=['ACE', 'Age'])
        
        assert list(df.columns) == ['ACE', 'Age']
        assert 'ExtraColumn' not in df.columns
        assert len(df) == 100

def test_load_chunked_correct_count(mock_csv_data):
    """Test that chunked loading yields correct total row count."""
    file_path, _ = mock_csv_data
    
    with patch('code.data.streaming_loader.get_processed_dir', return_value=file_path.parent):
        total_rows = 0
        chunk_count = 0
        
        for chunk in load_cleaned_dataset_chunked(chunk_size=20):
            chunk_count += 1
            total_rows += len(chunk)
        
        assert total_rows == 100
        assert chunk_count == 5  # 100 / 20

def test_load_missing_file():
    """Test that FileNotFoundError is raised when file is missing."""
    with patch('code.data.streaming_loader.get_processed_dir') as mock_dir:
        mock_dir.return_value = Path("/nonexistent/path")
        
        with pytest.raises(FileNotFoundError):
            load_cleaned_dataset_full_optimized()

def test_load_missing_columns(mock_csv_data):
    """Test that ValueError is raised when requested columns don't exist."""
    file_path, _ = mock_csv_data
    
    with patch('code.data.streaming_loader.get_processed_dir', return_value=file_path.parent):
        with pytest.raises(ValueError, match="Requested columns"):
            load_cleaned_dataset_full_optimized(columns=['NonExistentColumn'])

def test_memory_optimization(mock_csv_data):
    """Test that data types are optimized for memory."""
    file_path, _ = mock_csv_data
    
    with patch('code.data.streaming_loader.get_processed_dir', return_value=file_path.parent):
        df = load_cleaned_dataset_full_optimized()
        
        # Check that float64 is converted to float32
        for col in ['ACE', 'CA3', 'DG', 'Subiculum', 'ICV']:
            if col in df.columns:
                assert df[col].dtype == np.float32

def test_process_and_save_subset(mock_csv_data):
    """Test creating an optimized subset file."""
    file_path, temp_path = mock_csv_data
    
    with patch('code.data.streaming_loader.get_processed_dir', return_value=file_path.parent):
        output_path = process_and_save_subset("test_subset.csv")
        
        assert os.path.exists(output_path)
        
        # Verify the file content
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 100
        assert 'ExtraColumn' not in saved_df.columns