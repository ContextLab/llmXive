"""
Tests for UCI Downloader module.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.uci_downloader import (
    identify_continuous_columns,
    clean_and_process_dataset,
    download_dataset
)

class TestIdentifyContinuousColumns:
    def test_identify_mixed_types(self):
        """Test identification of continuous columns in mixed dataframe."""
        data = {
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'const_col': [5, 5, 5, 5, 5],
            'str_col': ['a', 'b', 'c', 'd', 'e']
        }
        df = pd.DataFrame(data)
        
        continuous = identify_continuous_columns(df)
        
        assert 'int_col' in continuous
        assert 'float_col' in continuous
        assert 'const_col' not in continuous # Variance is 0
        assert 'str_col' not in continuous

    def test_identify_empty_dataframe(self):
        """Test with empty dataframe."""
        df = pd.DataFrame()
        continuous = identify_continuous_columns(df)
        assert len(continuous) == 0

class TestCleanAndProcessDataset:
    def test_clean_and_calculate_variance(self, tmp_path):
        """Test cleaning and variance calculation."""
        data = {
            'col_0': [1.0, 2.0, 3.0, 4.0, 5.0],
            'col_1': [10.0, 20.0, 30.0, 40.0, 50.0],
            'col_2': [1.0, 1.0, 1.0, 1.0, 1.0] # Constant
        }
        df = pd.DataFrame(data)
        continuous_cols = ['col_0', 'col_1']
        
        output_file = tmp_path / "clean.csv"
        
        variance = clean_and_process_dataset(df, continuous_cols, output_file)
        
        # Check file exists
        assert output_file.exists()
        
        # Check variance values (approximate)
        assert 'col_0' in variance
        assert 'col_1' in variance
        assert abs(variance['col_0'] - 2.5) < 0.01 # Sample variance of [1,2,3,4,5]
        assert abs(variance['col_1'] - 250.0) < 0.1 # Sample variance of [10,20,30,40,50]

    def test_handles_missing_values(self, tmp_path):
        """Test that rows with NaN are dropped."""
        data = {
            'col_0': [1.0, np.nan, 3.0, 4.0, 5.0],
            'col_1': [10.0, 20.0, 30.0, 40.0, 50.0]
        }
        df = pd.DataFrame(data)
        continuous_cols = ['col_0', 'col_1']
        
        output_file = tmp_path / "clean_with_nan.csv"
        variance = clean_and_process_dataset(df, continuous_cols, output_file)
        
        # Re-read to check row count
        df_out = pd.read_csv(output_file)
        assert len(df_out) == 4 # One row dropped
        assert 'col_0' in variance

class TestDownloadDataset:
    def test_download_failure_invalid_url(self, tmp_path):
        """Test download failure with invalid URL."""
        output_file = tmp_path / "fail.csv"
        success = download_dataset("http://invalid-url-that-does-not-exist-12345.com/data.csv", output_file)
        assert success is False
        assert not output_file.exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])