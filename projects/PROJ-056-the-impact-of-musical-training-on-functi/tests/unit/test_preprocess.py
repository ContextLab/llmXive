import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import shutil

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.preprocess import (
    filter_by_training_years,
    remove_missing_data,
    calculate_dataset_validity,
    write_validity_report,
    preprocess_subjects
)

class TestDatasetValidity:
    """Tests for dataset validity calculation and reporting."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample dataframe with mixed valid/invalid data."""
        data = {
            'subject_id': [f'sub_{i}' for i in range(100)],
            'group': ['musician'] * 50 + ['non_musician'] * 50,
            'years_of_training': [5.0] * 45 + [None] * 5 + [0.0] * 50,
            'age': [20.0] * 100,
            'sex': ['M'] * 50 + ['F'] * 50,
            'motion_score': [0.1] * 100,
            'ses_score': [5.0] * 100
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def empty_dataframe(self):
        """Create an empty dataframe."""
        return pd.DataFrame(columns=['subject_id', 'group', 'years_of_training'])

    def test_calculate_validity_perfect_data(self, sample_dataframe):
        """Test validity calculation with all valid data."""
        # Modify to have all valid data
        df = sample_dataframe.copy()
        df['years_of_training'] = 5.0  # All valid
        
        metrics = calculate_dataset_validity(df)
        
        assert 'metric' in metrics.columns
        assert 'value' in metrics.columns
        
        total = metrics[metrics['metric'] == 'total_subjects']['value'].values[0]
        valid = metrics[metrics['metric'] == 'valid_subjects']['value'].values[0]
        percentage = metrics[metrics['metric'] == 'valid_subjects_percentage']['value'].values[0]
        
        assert total == 100
        assert valid == 100
        assert percentage == 100.0

    def test_calculate_validity_with_missing(self, sample_dataframe):
        """Test validity calculation with missing data."""
        metrics = calculate_dataset_validity(sample_dataframe)
        
        total = metrics[metrics['metric'] == 'total_subjects']['value'].values[0]
        valid = metrics[metrics['metric'] == 'valid_subjects']['value'].values[0]
        percentage = metrics[metrics['metric'] == 'valid_subjects_percentage']['value'].values[0]
        
        assert total == 100
        # 5 subjects have None for years_of_training, so 95 should be valid
        assert valid == 95
        assert abs(percentage - 95.0) < 0.01

    def test_calculate_validity_empty_dataframe(self, empty_dataframe):
        """Test validity calculation with empty dataframe."""
        metrics = calculate_dataset_validity(empty_dataframe)
        
        total = metrics[metrics['metric'] == 'total_subjects']['value'].values[0]
        percentage = metrics[metrics['metric'] == 'valid_subjects_percentage']['value'].values[0]
        
        assert total == 0
        assert percentage == 0.0

    def test_write_validity_report_creates_file(self, sample_dataframe, tmp_path):
        """Test that write_validity_report creates the expected file."""
        metrics = calculate_dataset_validity(sample_dataframe)
        output_path = str(tmp_path / 'dataset_validity_report.csv')
        
        write_validity_report(metrics, output_path)
        
        assert os.path.exists(output_path)
        
        # Verify file contents
        result_df = pd.read_csv(output_path)
        assert 'metric' in result_df.columns
        assert 'value' in result_df.columns
        assert len(result_df) > 0

    def test_preprocess_subjects_outputs_validity_report(self, sample_dataframe, tmp_path):
        """Test that preprocess_subjects writes the validity report to the correct location."""
        output_dir = str(tmp_path / 'processed')
        
        cleaned_df, metrics = preprocess_subjects(
            sample_dataframe, 
            output_dir=output_dir,
            threshold_years=1.0
        )
        
        expected_path = os.path.join(output_dir, 'dataset_validity_report.csv')
        assert os.path.exists(expected_path), f"File {expected_path} was not created"
        
        # Verify the file contains the correct percentage
        result_df = pd.read_csv(expected_path)
        percentage_value = result_df[result_df['metric'] == 'valid_subjects_percentage']['value'].values[0]
        
        # With 5 missing values out of 100, percentage should be 95.0
        assert abs(percentage_value - 95.0) < 0.1, f"Expected 95.0, got {percentage_value}"

    def test_validity_report_columns(self, sample_dataframe, tmp_path):
        """Test that validity report has the correct columns."""
        output_dir = str(tmp_path / 'processed')
        preprocess_subjects(sample_dataframe, output_dir=output_dir)
        
        report_path = os.path.join(output_dir, 'dataset_validity_report.csv')
        df = pd.read_csv(report_path)
        
        assert 'metric' in df.columns
        assert 'value' in df.columns
        
        # Check for expected metrics
        metrics_list = df['metric'].tolist()
        assert 'valid_subjects_percentage' in metrics_list
        assert 'total_subjects' in metrics_list
        assert 'valid_subjects' in metrics_list

    def test_validity_percentage_calculation_accuracy(self, tmp_path):
        """Test accuracy of percentage calculation with known values."""
        # Create dataframe with exactly 80 valid out of 100
        data = {
            'subject_id': [f'sub_{i}' for i in range(100)],
            'group': ['musician'] * 100,
            'years_of_training': [5.0] * 80 + [None] * 20,
            'age': [20.0] * 100,
            'sex': ['M'] * 100,
            'motion_score': [0.1] * 100,
            'ses_score': [5.0] * 100
        }
        df = pd.DataFrame(data)
        
        output_dir = str(tmp_path / 'processed')
        preprocess_subjects(df, output_dir=output_dir)
        
        report_path = os.path.join(output_dir, 'dataset_validity_report.csv')
        result_df = pd.read_csv(report_path)
        
        percentage = result_df[result_df['metric'] == 'valid_subjects_percentage']['value'].values[0]
        assert abs(percentage - 80.0) < 0.01, f"Expected 80.0, got {percentage}"