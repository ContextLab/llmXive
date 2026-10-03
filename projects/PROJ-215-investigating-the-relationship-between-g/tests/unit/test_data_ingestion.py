import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to test
from code.data_ingestion import run_ingestion, check_feasibility, load_agp_data_from_mirror

class TestDataIngestion:
    @pytest.fixture
    def sample_df(self):
        """Create a sample dataframe with some missing PHQ-9/GAD-7 values."""
        data = {
            'sample_id': ['s1', 's2', 's3', 's4', 's5'],
            'phq9': [10.0, np.nan, 5.0, 15.0, np.nan],
            'gad7': [8.0, 12.0, np.nan, 20.0, 5.0],
            'other_col': ['a', 'b', 'c', 'd', 'e']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_df_complete(self):
        """Create a sample dataframe with no missing PHQ-9/GAD-7 values."""
        data = {
            'sample_id': ['s1', 's2', 's3'],
            'phq9': [10.0, 5.0, 15.0],
            'gad7': [8.0, 12.0, 20.0],
            'other_col': ['a', 'b', 'c']
        }
        return pd.DataFrame(data)

    def test_check_feasibility_pass(self, sample_df_complete):
        """Test that feasibility check passes when required columns exist."""
        assert check_feasibility(sample_df_complete) is True

    def test_check_feasibility_fail(self, sample_df):
        """Test that feasibility check fails when required columns are missing."""
        # Remove a required column
        df_missing = sample_df.drop(columns=['phq9'])
        assert check_feasibility(df_missing) is False

    def test_run_ingestion_filters_missing_values(self, sample_df):
        """Test that run_ingestion correctly filters rows with missing PHQ-9/GAD-7."""
        # We need to mock load_agp_data_from_mirror to return our sample_df
        # Since we can't easily mock the dataset loader in a unit test without side effects,
        # we will test the logic by creating a temporary file and simulating the flow.
        # However, run_ingestion calls load_agp_data_from_mirror which fetches real data.
        # To test the filtering logic specifically, we can test the filtering step directly
        # or mock the loader.
        
        # Let's mock the loader for this test
        import code.data_ingestion as di_module
        
        original_loader = di_module.load_agp_data_from_mirror
        
        def mock_loader(study_id):
            return sample_df

        di_module.load_agp_data_from_mirror = mock_loader

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test_output.csv")
                result = run_ingestion("10317", output_path)
                
                # Check that the output file exists
                assert os.path.exists(output_path)
                
                # Check the exclusion rate
                # Original: 5 rows. Missing: s2 (phq9), s3 (gad7), s5 (phq9).
                # Valid: s1, s4. So 2 valid rows.
                # Exclusion rate = (5-2)/5 = 0.6
                assert result.raw_rows == 5
                assert result.filtered_rows == 2
                assert abs(result.exclusion_rate - 0.6) < 0.01

                # Check the content of the output file
                output_df = pd.read_csv(output_path)
                assert len(output_df) == 2
                assert 'phq9' in output_df.columns
                assert 'gad7' in output_df.columns
                # Ensure no NaN in phq9 or gad7
                assert output_df['phq9'].isna().sum() == 0
                assert output_df['gad7'].isna().sum() == 0
        finally:
            di_module.load_agp_data_from_mirror = original_loader

    def test_run_ingestion_no_missing_values(self, sample_df_complete):
        """Test that run_ingestion keeps all rows when no values are missing."""
        import code.data_ingestion as di_module
        
        original_loader = di_module.load_agp_data_from_mirror
        
        def mock_loader(study_id):
            return sample_df_complete

        di_module.load_agp_data_from_mirror = mock_loader

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test_output.csv")
                result = run_ingestion("10317", output_path)
                
                assert result.raw_rows == 3
                assert result.filtered_rows == 3
                assert result.exclusion_rate == 0.0
        finally:
            di_module.load_agp_data_from_mirror = original_loader