"""
Unit tests for data loading utilities.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from data_utils import (
    load_csv_chunked,
    get_file_info,
    validate_csv_structure,
    load_csv_with_dtypes
)
from config import SAMPLE_LIMIT


@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a sample CSV file for testing."""
    file_path = tmp_path / "test_data.csv"
    
    # Create a sample dataset
    data = {
        'id': range(1, 101),
        'value': [float(i) for i in range(1, 101)],
        'category': ['A'] * 50 + ['B'] * 50
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    
    return file_path


@pytest.fixture
def large_csv_file(tmp_path):
    """Create a large CSV file for chunked reading tests."""
    file_path = tmp_path / "large_data.csv"
    
    # Create a larger dataset
    n_rows = 15000
    data = {
        'id': range(1, n_rows + 1),
        'value': np.random.rand(n_rows),
        'category': np.random.choice(['A', 'B', 'C'], n_rows)
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    
    return file_path


class TestLoadCSVChunked:
    """Tests for load_csv_chunked function."""
    
    def test_load_small_file(self, sample_csv_file):
        """Test loading a small file that fits in one chunk."""
        result = load_csv_chunked(sample_csv_file, chunk_size=1000)
        
        assert len(result) == 100
        assert 'id' in result.columns
        assert 'value' in result.columns
        assert 'category' in result.columns
    
    def test_load_limited_rows(self, large_csv_file):
        """Test loading with max_rows limit."""
        max_rows = 5000
        result = load_csv_chunked(large_csv_file, chunk_size=1000, max_rows=max_rows)
        
        assert len(result) == max_rows
        assert len(result) <= SAMPLE_LIMIT
    
    def test_load_with_usecols(self, sample_csv_file):
        """Test loading with specific columns."""
        result = load_csv_chunked(sample_csv_file, usecols=['id', 'value'])
        
        assert 'id' in result.columns
        assert 'value' in result.columns
        assert 'category' not in result.columns
        assert len(result) == 100
    
    def test_load_with_dtypes(self, sample_csv_file):
        """Test loading with specified data types."""
        dtype_dict = {'id': 'int32', 'value': 'float32'}
        result = load_csv_chunked(sample_csv_file, dtype_dict=dtype_dict)
        
        assert result['id'].dtype == np.int32
        assert result['value'].dtype == np.float32
    
    def test_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_csv_chunked("nonexistent.csv")
    
    def test_empty_file(self, tmp_path):
        """Test error handling for empty file."""
        empty_file = tmp_path / "empty.csv"
        empty_file.touch()
        
        with pytest.raises(ValueError):
            load_csv_chunked(empty_file)


class TestGetFileInfo:
    """Tests for get_file_info function."""
    
    def test_get_info(self, sample_csv_file):
        """Test getting file information."""
        info = get_file_info(sample_csv_file)
        
        assert 'file_path' in info
        assert 'num_rows' in info
        assert 'num_columns' in info
        assert 'columns' in info
        assert 'size_mb' in info
        
        assert info['num_rows'] == 100
        assert info['num_columns'] == 3
        assert 'id' in info['columns']
    
    def test_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            get_file_info("nonexistent.csv")


class TestValidateCSVStructure:
    """Tests for validate_csv_structure function."""
    
    def test_validate_success(self, sample_csv_file):
        """Test successful validation."""
        assert validate_csv_structure(sample_csv_file) is True
        assert validate_csv_structure(sample_csv_file, required_columns=['id', 'value']) is True
    
    def test_validate_missing_columns(self, sample_csv_file):
        """Test validation failure for missing columns."""
        with pytest.raises(ValueError):
            validate_csv_structure(sample_csv_file, required_columns=['id', 'nonexistent'])
    
    def test_validate_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            validate_csv_structure("nonexistent.csv")


class TestLoadCSVWithDtypes:
    """Tests for load_csv_with_dtypes function."""
    
    def test_load_with_dtypes(self, sample_csv_file):
        """Test loading with specified data types."""
        dtype_dict = {'id': 'int32', 'value': 'float32'}
        result = load_csv_with_dtypes(sample_csv_file, dtype_dict=dtype_dict)
        
        assert result['id'].dtype == np.int32
        assert result['value'].dtype == np.float32
        assert len(result) == 100
    
    def test_load_with_usecols(self, sample_csv_file):
        """Test loading with specific columns."""
        result = load_csv_with_dtypes(sample_csv_file, usecols=['id', 'category'])
        
        assert 'id' in result.columns
        assert 'category' in result.columns
        assert 'value' not in result.columns
        assert len(result) == 100
    
    def test_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_csv_with_dtypes("nonexistent.csv")