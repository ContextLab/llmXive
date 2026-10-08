"""
Tests for the data loading module.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.load_data import (
    normalize_columns,
    save_to_csv,
    _read_csv_file,
    process_single_file
)

class TestDataLoading:
    """Test cases for data loading functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_normalize_columns(self):
        """Test that normalize_columns correctly processes a DataFrame."""
        # Create test data
        data = {
            'timestamp': [1.0, 2.0, 3.0],
            'x': [10.0, 20.0, 30.0],
            'y': [15.0, 25.0, 35.0],
            'pupil_diameter': [3.5, 3.6, 3.7]
        }
        df = pd.DataFrame(data)
        
        # Normalize
        normalized = normalize_columns(df)
        
        # Check columns exist
        assert 'timestamp' in normalized.columns
        assert 'x' in normalized.columns
        assert 'y' in normalized.columns
        assert 'pupil_diameter' in normalized.columns
        
        # Check types
        assert normalized['timestamp'].dtype in [np.float64, np.float32]
        assert normalized['x'].dtype in [np.float64, np.float32]
        assert normalized['y'].dtype in [np.float64, np.float32]
        assert normalized['pupil_diameter'].dtype in [np.float64, np.float32]
        
        # Check values
        assert len(normalized) == 3
        assert normalized['timestamp'].iloc[0] == 1000.0  # Converted to ms
    
    def test_normalize_columns_missing_column(self):
        """Test that normalize_columns raises error for missing columns."""
        data = {
            'timestamp': [1.0, 2.0],
            'x': [10.0, 20.0],
            'y': [15.0, 25.0]
            # Missing pupil_diameter
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError):
            normalize_columns(df)
    
    def test_save_to_csv(self):
        """Test that save_to_csv creates a valid CSV file."""
        data = {
            'timestamp': [1000.0, 2000.0, 3000.0],
            'x': [10.0, 20.0, 30.0],
            'y': [15.0, 25.0, 35.0],
            'pupil_diameter': [3.5, 3.6, 3.7]
        }
        df = pd.DataFrame(data)
        
        output_path = Path(self.test_dir) / 'test_output.csv'
        save_to_csv(df, output_path)
        
        # Check file exists
        assert output_path.exists()
        
        # Check content
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ['timestamp', 'x', 'y', 'pupil_diameter']
    
    def test_read_csv_file(self):
        """Test reading a CSV file."""
        # Create test CSV
        csv_path = Path(self.test_dir) / 'test_data.csv'
        data = {
            'time': [1.0, 2.0, 3.0],
            'x_pos': [10.0, 20.0, 30.0],
            'y_pos': [15.0, 25.0, 35.0],
            'pupil_size': [3.5, 3.6, 3.7]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        # Read file
        df = _read_csv_file(csv_path)
        
        # Check result
        assert df is not None
        assert len(df) == 3
        assert 'timestamp' in df.columns
        assert 'x' in df.columns
        assert 'y' in df.columns
        assert 'pupil_diameter' in df.columns
    
    def test_process_single_file(self):
        """Test processing a single file end-to-end."""
        # Create test CSV
        input_path = Path(self.test_dir) / 'input.csv'
        data = {
            'timestamp': [1.0, 2.0, 3.0],
            'x': [10.0, 20.0, 30.0],
            'y': [15.0, 25.0, 35.0],
            'pupil_diameter': [3.5, 3.6, 3.7]
        }
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        output_path = Path(self.test_dir) / 'output.csv'
        
        # Process file
        result_df = process_single_file(input_path, output_path)
        
        # Check result
        assert result_df is not None
        assert len(result_df) == 3
        assert output_path.exists()
        
        # Check output content
        loaded_df = pd.read_csv(output_path)
        assert list(loaded_df.columns) == ['timestamp', 'x', 'y', 'pupil_diameter']