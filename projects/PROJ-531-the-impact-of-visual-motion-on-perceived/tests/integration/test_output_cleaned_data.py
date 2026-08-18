import os
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import shutil

from preprocessing.output_cleaned_data import standardize_column, run_cleaning_pipeline


class TestStandardizeColumn:
    def test_minmax_standardization_range(self):
        """Test that standardization produces values in [0, 1]."""
        data = pd.Series([10, 20, 30, 40, 50])
        standardized = standardize_column(data)
        
        assert standardized.min() == 0.0
        assert standardized.max() == 1.0
        
    def test_constant_column_handling(self):
        """Test that constant columns are handled without division by zero."""
        data = pd.Series([5, 5, 5, 5])
        standardized = standardize_column(data)
        
        # Should return 0.5 for all values when min == max
        assert all(standardized == 0.5)
        
    def test_negative_values(self):
        """Test standardization with negative values."""
        data = pd.Series([-10, 0, 10])
        standardized = standardize_column(data)
        
        assert standardized.min() == 0.0
        assert standardized.max() == 1.0
        assert standardized.iloc[1] == 0.5  # Middle value

class TestRunCleaningPipeline:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    def test_pipeline_creates_output(self, temp_dir):
        """Test that the pipeline creates the output CSV file."""
        input_data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'latency': [100, 200, 300],
            'smoothness': [0.8, 0.9, 0.95],
            'agency_score': [3.5, 4.2, 4.8]
        }
        df = pd.DataFrame(input_data)
        
        input_path = os.path.join(temp_dir, 'input.csv')
        output_path = os.path.join(temp_dir, 'output.csv')
        
        df.to_csv(input_path, index=False)
        
        metadata = run_cleaning_pipeline(input_path, output_path)
        
        assert os.path.exists(output_path)
        assert metadata['n_rows_before'] == 3
        assert metadata['n_rows_after'] == 3
        
        # Verify output content
        output_df = pd.read_csv(output_path)
        assert 'latency' in output_df.columns
        assert 'smoothness' in output_df.columns
        assert 'agency_score' in output_df.columns
        
        # Verify standardization (latency should be 0, 0.5, 1.0)
        assert output_df['latency'].min() == 0.0
        assert output_df['latency'].max() == 1.0
        
    def test_pipeline_handles_missing_values(self, temp_dir):
        """Test that the pipeline handles missing values gracefully."""
        input_data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'latency': [100, np.nan, 300],
            'smoothness': [0.8, 0.9, 0.95],
            'agency_score': [3.5, 4.2, np.nan]
        }
        df = pd.DataFrame(input_data)
        
        input_path = os.path.join(temp_dir, 'input.csv')
        output_path = os.path.join(temp_dir, 'output.csv')
        
        df.to_csv(input_path, index=False)
        
        # Should not raise an error, but NaNs will remain in standardized columns
        # depending on pandas behavior (minmax with NaN usually propagates NaN)
        metadata = run_cleaning_pipeline(input_path, output_path)
        
        assert os.path.exists(output_path)
        
    def test_metadata_file_created(self, temp_dir):
        """Test that metadata JSON is created alongside output."""
        input_data = {
            'participant_id': ['P1'],
            'latency': [100],
            'smoothness': [0.8],
            'agency_score': [3.5]
        }
        df = pd.DataFrame(input_data)
        
        input_path = os.path.join(temp_dir, 'input.csv')
        output_path = os.path.join(temp_dir, 'output.csv')
        
        df.to_csv(input_path, index=False)
        
        run_cleaning_pipeline(input_path, output_path)
        
        metadata_path = output_path.replace('.csv', '.json')
        assert os.path.exists(metadata_path)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert 'standardization_method' in metadata
        assert metadata['standardization_method'] == 'minmax'
        assert 'scoring_method_documentation' in metadata