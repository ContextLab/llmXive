"""
Tests for the data_loader module.

These tests verify that the data loader:
1. Correctly downloads datasets from OpenML
2. Raises appropriate errors for missing datasets
3. Enforces minimum dataset size requirements
4. Saves data to the correct location
"""

import os
import tempfile
import pytest
import pandas as pd

from code.data_loader import (
    get_openml_dataset,
    load_dataset_as_dataframe,
    validate_rct_dataset,
    DataLoadError
)


class TestDataLoader:
    """Test cases for data loading functionality."""
    
    def test_get_openml_dataset_valid_id(self):
        """Test downloading a valid dataset from OpenML."""
        # Using a well-known dataset that should be available
        dataset_id = 42164  # A synthetic RCT dataset
        
        dataset = get_openml_dataset(dataset_id)
        
        assert dataset is not None
        assert dataset.dataset_id == dataset_id
        assert dataset.name is not None
        
    def test_get_openml_dataset_invalid_id(self):
        """Test that invalid dataset IDs raise DataLoadError."""
        invalid_id = 999999999  # Very high ID that likely doesn't exist
        
        with pytest.raises(DataLoadError):
            get_openml_dataset(invalid_id)
            
    def test_load_dataset_as_dataframe(self):
        """Test loading a dataset and saving to CSV."""
        dataset_id = 42164
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_dataset.csv")
            
            df = load_dataset_as_dataframe(dataset_id, output_path)
            
            # Verify file was created
            assert os.path.exists(output_path)
            
            # Verify DataFrame properties
            assert isinstance(df, pd.DataFrame)
            assert len(df) >= 100  # Minimum threshold
            assert len(df.columns) >= 2
            
            # Verify data can be read back
            df_read = pd.read_csv(output_path)
            assert len(df_read) == len(df)
            
    def test_load_dataset_small_dataset(self):
        """Test that datasets with < 100 samples raise DataLoadError."""
        # Using a very small dataset ID if available, or simulating the check
        # For now, we test the validation logic directly
        
        # Create a small DataFrame
        small_df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6]
        })
        
        with pytest.raises(DataLoadError, match="below the minimum threshold"):
            validate_rct_dataset(small_df, 123)
            
    def test_validate_rct_dataset_empty(self):
        """Test validation of empty datasets."""
        empty_df = pd.DataFrame()
        
        with pytest.raises(DataLoadError, match="is empty"):
            validate_rct_dataset(empty_df, 123)
            
    def test_validate_rct_dataset_insufficient_columns(self):
        """Test validation of datasets with insufficient columns."""
        single_col_df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5]
        })
        
        with pytest.raises(DataLoadError, match="only 1 column"):
            validate_rct_dataset(single_col_df, 123)
            
    def test_load_dataset_creates_output_directory(self):
        """Test that output directory is created if it doesn't exist."""
        dataset_id = 42164
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "nested", "path", "dataset.csv")
            
            df = load_dataset_as_dataframe(dataset_id, nested_path)
            
            assert os.path.exists(nested_path)
            assert os.path.isdir(os.path.dirname(nested_path))