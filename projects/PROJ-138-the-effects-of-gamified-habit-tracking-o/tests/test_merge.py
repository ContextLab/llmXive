"""
Tests for the merge functionality (T017).
"""
import os
import sys
import tempfile
import shutil
import pytest
import pandas as pd
from code.data.merge import merge_datasets

class TestMerge:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        # Create temporary directory structure for testing
        self.tmp_dir = tmp_path
        self.data_raw = self.tmp_dir / "data" / "raw"
        self.data_processed = self.tmp_dir / "data" / "processed"
        self.data_raw.mkdir(parents=True)
        self.data_processed.mkdir(parents=True)
        
        # Mock input files
        self.input_agg = self.data_processed / "weekly_aggregated.csv"
        self.input_users = self.data_processed / "user_traits.csv"
        self.output = self.data_processed / "merged_data.csv"
        
        # Create dummy weekly data
        df_weekly = pd.DataFrame({
            'User_ID': ['U1', 'U1', 'U2', 'U2'],
            'week_number': [1, 2, 1, 2],
            'weekly_adherence_flag': [1, 0, 1, 1]
        })
        self.input_agg.write_text(df_weekly.to_csv(index=False))
        
        # Create dummy user traits
        df_users = pd.DataFrame({
            'User_ID': ['U1', 'U2'],
            'gamified_status': [True, False],
            'conscientiousness_score': [3.5, 4.2],
            'need_for_achievement': [3.0, 4.5]
        })
        self.input_users.write_text(df_users.to_csv(index=False))

    def test_merge_creates_file(self, setup):
        # Temporarily override paths in the function scope if needed, 
        # but here we rely on the function reading from the fixed relative paths.
        # Since we can't easily override global constants in the module under test 
        # without patching, we assume the test environment has the files in the 
        # expected relative location OR we patch the constants.
        # For this unit test, we will verify the logic by checking the output file
        # exists after calling the function, assuming the working dir is set correctly.
        
        # Save original CWD
        original_cwd = os.getcwd()
        try:
            # Change to tmp_dir to simulate project root
            os.chdir(self.tmp_dir)
            
            # Run merge
            result = merge_datasets()
            
            # Assert output file exists
            assert self.output.exists(), "Output file merged_data.csv was not created."
            
            # Assert content
            df_out = pd.read_csv(self.output)
            assert 'User_ID' in df_out.columns
            assert 'Gamified' in df_out.columns
            assert 'Adherence' in df_out.columns
            assert 'Conscientiousness' in df_out.columns
            assert 'Need_for_Achievement' in df_out.columns
            assert 'week_number' in df_out.columns
            
            # Check row count (2 users * 2 weeks = 4 rows)
            assert len(df_out) == 4
            
            # Check specific values
            u1_row = df_out[df_out['User_ID'] == 'U1'].iloc[0]
            assert u1_row['Gamified'] == True
            assert u1_row['Conscientiousness'] == 3.5
            
        finally:
            os.chdir(original_cwd)

    def test_merge_missing_input_raises(self, setup):
        original_cwd = os.getcwd()
        try:
            os.chdir(self.tmp_dir)
            # Remove one input file
            self.input_agg.unlink()
            
            with pytest.raises(FileNotFoundError):
                merge_datasets()
        finally:
            os.chdir(original_cwd)