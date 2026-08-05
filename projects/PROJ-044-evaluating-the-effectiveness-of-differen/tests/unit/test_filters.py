"""
Unit tests for data filtering utilities (T035).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function under test
# Note: Using relative import path based on project structure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.filters import filter_utility_collapse, run_filter_pipeline


class TestFilterUtilityCollapse:
    """Tests for filter_utility_collapse function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_path = Path(self.temp_dir.name) / "raw_logs.csv"
        self.output_path = Path(self.temp_dir.name) / "filtered_data.csv"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_filter_removes_utility_collapse_rows(self):
        """Test that rows with is_utility_collapse=True are removed."""
        # Create test data
        data = {
            'seed': [1, 2, 3, 4, 5],
            'alpha': [0.1, 0.1, 0.5, 1.0, 0.1],
            'epsilon': [0.1, 0.5, 1.0, 5.0, 0.1],
            'global_accuracy': [0.45, 0.65, 0.72, 0.81, 0.42],
            'is_utility_collapse': [True, False, False, False, True],
            'is_time_limited': [False, False, False, False, False]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.input_path, index=False)
        
        # Run filter
        result = filter_utility_collapse(self.input_path, self.output_path)
        
        # Load filtered data
        filtered_df = pd.read_csv(self.output_path)
        
        # Assertions
        assert len(filtered_df) == 3  # 5 total - 2 collapsed
        assert all(~filtered_df['is_utility_collapse'].astype(bool))
        assert result['total_rows'] == 5
        assert result['filtered_rows'] == 2
        assert result['remaining_rows'] == 3
    
    def test_filter_preserves_valid_rows(self):
        """Test that rows with is_utility_collapse=False are preserved."""
        data = {
            'seed': [1, 2, 3],
            'alpha': [0.1, 0.5, 1.0],
            'epsilon': [0.1, 0.5, 1.0],
            'global_accuracy': [0.65, 0.72, 0.81],
            'is_utility_collapse': [False, False, False],
            'is_time_limited': [False, False, False]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.input_path, index=False)
        
        result = filter_utility_collapse(self.input_path, self.output_path)
        filtered_df = pd.read_csv(self.output_path)
        
        assert len(filtered_df) == 3
        assert result['filtered_rows'] == 0
        assert result['remaining_rows'] == 3
    
    def test_filter_handles_missing_column(self):
        """Test that appropriate error is raised when column is missing."""
        data = {
            'seed': [1, 2, 3],
            'alpha': [0.1, 0.5, 1.0],
            'epsilon': [0.1, 0.5, 1.0],
            'global_accuracy': [0.65, 0.72, 0.81]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.input_path, index=False)
        
        with pytest.raises(KeyError):
            filter_utility_collapse(self.input_path, self.output_path)
    
    def test_filter_handles_missing_file(self):
        """Test that appropriate error is raised when input file is missing."""
        non_existent_path = Path(self.temp_dir.name) / "non_existent.csv"
        
        with pytest.raises(FileNotFoundError):
            filter_utility_collapse(non_existent_path, self.output_path)
    
    def test_filter_handles_empty_file(self):
        """Test that appropriate error is raised when input file is empty."""
        self.input_path.touch()  # Create empty file
        
        with pytest.raises(ValueError):
            filter_utility_collapse(self.input_path, self.output_path)
    
    def test_filter_with_nan_values(self):
        """Test filtering when is_utility_collapse has NaN values."""
        data = {
            'seed': [1, 2, 3, 4],
            'alpha': [0.1, 0.5, 1.0, 0.1],
            'epsilon': [0.1, 0.5, 1.0, 5.0],
            'global_accuracy': [0.65, 0.72, 0.81, 0.42],
            'is_utility_collapse': [True, False, np.nan, False],
            'is_time_limited': [False, False, False, False]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.input_path, index=False)
        
        result = filter_utility_collapse(self.input_path, self.output_path)
        filtered_df = pd.read_csv(self.output_path)
        
        # NaN values should be treated as False (kept)
        # Only True values should be removed
        assert len(filtered_df) == 3
        assert result['filtered_rows'] == 1
    
    def test_filter_output_directory_creation(self):
        """Test that output directory is created if it doesn't exist."""
        data = {
            'seed': [1],
            'alpha': [0.1],
            'epsilon': [0.1],
            'global_accuracy': [0.65],
            'is_utility_collapse': [False],
            'is_time_limited': [False]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.input_path, index=False)
        
        # Output path in non-existent directory
        nested_output = Path(self.temp_dir.name) / "nested" / "dir" / "output.csv"
        
        result = filter_utility_collapse(self.input_path, nested_output)
        
        assert nested_output.exists()
        assert result['remaining_rows'] == 1


class TestRunFilterPipeline:
    """Tests for run_filter_pipeline function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_logs_path = Path(self.temp_dir.name) / "raw_logs.csv"
        self.filtered_path = Path(self.temp_dir.name) / "filtered_data.csv"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_pipeline_creates_filtered_output(self):
        """Test that pipeline creates the filtered output file."""
        data = {
            'seed': [1, 2, 3],
            'alpha': [0.1, 0.5, 1.0],
            'epsilon': [0.1, 0.5, 1.0],
            'global_accuracy': [0.65, 0.72, 0.81],
            'is_utility_collapse': [True, False, False],
            'is_time_limited': [False, False, False]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.raw_logs_path, index=False)
        
        result = run_filter_pipeline(self.raw_logs_path, self.filtered_path)
        
        assert self.filtered_path.exists()
        assert result['remaining_rows'] == 2
        assert result['filtered_rows'] == 1
    
    def test_pipeline_with_custom_column(self):
        """Test pipeline with custom column name."""
        data = {
            'seed': [1, 2, 3],
            'custom_collapse': [True, False, False]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.raw_logs_path, index=False)
        
        result = run_filter_pipeline(
            self.raw_logs_path, 
            self.filtered_path,
            column_name="custom_collapse"
        )
        
        assert self.filtered_path.exists()
        assert result['remaining_rows'] == 2
        assert result['filter_column'] == "custom_collapse"
