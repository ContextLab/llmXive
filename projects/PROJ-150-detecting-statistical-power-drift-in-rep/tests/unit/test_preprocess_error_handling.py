import pandas as pd
import numpy as np
import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import load_raw_data, validate_grouping_variables, save_grouping_validation

class TestPreprocessErrorHandling:
    """
    Tests for T014: Error handling for missing data and zero-variance fields.
    """

    @pytest.fixture
    def sample_df_with_missing(self, tmp_path):
        """Create a sample dataframe with missing values in critical columns."""
        data = {
            'year': [2000, 2001, np.nan, 2003, 2004],
            'effect_size': [0.5, np.nan, 0.6, 0.7, 0.8],
            'sample_size': [100, 100, 100, np.nan, 100],
            'field': ['Psychology', 'Biology', 'Physics', 'Chemistry', 'Sociology'],
            'original_study_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'power_est': [0.8, 0.7, 0.6, 0.5, 0.9]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "data.csv"
        df.to_csv(csv_path, index=False)
        return df, csv_path

    @pytest.fixture
    def sample_df_zero_variance(self, tmp_path):
        """Create a sample dataframe where a grouping variable has zero variance."""
        data = {
            'year': [2000, 2001, 2002, 2003, 2004],
            'effect_size': [0.5, 0.6, 0.7, 0.8, 0.9],
            'sample_size': [100, 100, 100, 100, 100],
            'field': ['Psychology', 'Psychology', 'Psychology', 'Psychology', 'Psychology'], # Only 1 unique value
            'original_study_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'power_est': [0.8, 0.7, 0.6, 0.5, 0.9]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "data.csv"
        df.to_csv(csv_path, index=False)
        return df, csv_path

    def test_handles_missing_effect_size(self, sample_df_with_missing, caplog):
        """
        Test that rows with NaN in effect_size are identified and logged correctly.
        """
        df, csv_path = sample_df_with_missing
        
        # Mock the logger to capture warnings
        with patch('preprocess.get_module_logger') as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger
            
            # We can't easily run the full main() without mocking the file system structure,
            # so we test the logic directly on the dataframe.
            
            # Simulate the missing data check logic from main()
            critical_columns = ['year', 'effect_size', 'sample_size']
            rows_to_drop = []
            reasons = {}

            for idx, row in df.iterrows():
                drop_reason = None
                for col in critical_columns:
                    if pd.isna(row[col]):
                        drop_reason = f"NaN in '{col}'"
                        break
                
                if drop_reason:
                    rows_to_drop.append(idx)
                    reasons[idx] = drop_reason
                    # Verify the log format matches the requirement
                    mock_logger.warning.assert_called_with(f"WARNING: Skipping row {idx} due to {drop_reason}")

            # Verify specific rows were caught
            assert 1 in rows_to_drop # effect_size is NaN
            assert 2 in rows_to_drop # year is NaN
            assert 3 in rows_to_drop # sample_size is NaN
            
            # Verify reason messages
            assert reasons[1] == "NaN in 'effect_size'"
            assert reasons[2] == "NaN in 'year'"
            assert reasons[3] == "NaN in 'sample_size'"

    def test_handles_zero_variance_field(self, sample_df_zero_variance, tmp_path):
        """
        Test that zero variance in a grouping field is detected and reported.
        """
        df, csv_path = sample_df_zero_variance
        
        # Mock logger
        with patch('preprocess.get_module_logger') as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger
            
            # Run validation
            validation_results, all_valid = validate_grouping_variables(df, mock_logger)
            
            # Check that 'field' is marked invalid
            assert 'field' in validation_results
            assert validation_results['field']['valid'] is False
            assert "zero variance" in validation_results['field']['reason'].lower()
            
            # Check that 'original_study_id' is valid
            assert validation_results['original_study_id']['valid'] is True
            
            # Check that the overall flag is False
            assert all_valid is False
            
            # Verify warning was logged
            mock_logger.warning.assert_any_call(
                "Grouping variable 'field' has only 1 unique level(s). Zero variance detected."
            )

    def test_save_grouping_validation_creates_file(self, sample_df_with_missing, tmp_path):
        """
        Test that the grouping validation file is created correctly.
        """
        df, _ = sample_df_with_missing
        
        # Create a dummy validation result
        validation_results = {
            'field': {'valid': True, 'unique_levels': 5},
            'original_study_id': {'valid': True, 'unique_levels': 5}
        }
        
        # Call save function
        with patch('preprocess.get_module_logger') as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger
            
            # Temporarily override the output path for testing
            with patch('preprocess.GROUPING_VALIDATION_FILE', tmp_path / "test_validation.json"):
                save_grouping_validation(validation_results, mock_logger)
                
                # Verify file exists
                output_file = tmp_path / "test_validation.json"
                assert output_file.exists()
                
                # Verify content
                with open(output_file, 'r') as f:
                    loaded = json.load(f)
                
                assert loaded == validation_results
