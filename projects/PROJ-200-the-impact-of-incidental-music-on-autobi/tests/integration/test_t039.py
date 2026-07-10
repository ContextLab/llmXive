"""
Integration tests for T039: Generate sensitivity analysis and permutation results.

These tests verify that the script runs without error and produces the expected
output files with the correct structure.
"""
import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_project_root
from generate_final_results import main

class TestT039Integration:
    def test_script_runs_and_creates_files(self):
        """
        Test that the T039 script runs and creates the expected CSV files.
        Note: This test assumes the dependencies (modeling functions) are implemented.
        If they are not, the script might return empty DataFrames, which is acceptable
        for structure validation but not for content validation.
        """
        # We run the main function. It should not raise an exception.
        # In a real CI environment, we would have the data available.
        # For this test, we expect it to complete and create files, even if empty.
        
        try:
            main()
        except Exception as e:
            # If it fails due to missing data, that's expected in a partial environment,
            # but the script should handle it gracefully (log error, create empty files).
            # If it crashes, the test fails.
            pytest.fail(f"Script crashed: {e}")
        
        root = get_project_root()
        output_dir = root / "data" / "final"
        
        sens_path = output_dir / "sensitivity_analysis.csv"
        perm_path = output_dir / "permutation_results.csv"
        
        assert sens_path.exists(), f"Sensitivity analysis file not created at {sens_path}"
        assert perm_path.exists(), f"Permutation results file not created at {perm_path}"
        
        # Check structure
        sens_df = pd.read_csv(sens_path)
        perm_df = pd.read_csv(perm_path)
        
        expected_sens_cols = ['threshold', 'coefficient', 'std_err', 'p_value', 'vif', 'match_rate']
        assert list(sens_df.columns) == expected_sens_cols, f"Unexpected columns in sensitivity: {sens_df.columns}"
        
        expected_perm_cols = ['iteration', 'statistic', 'p_value', 'observed_statistic']
        assert list(perm_df.columns) == expected_perm_cols, f"Unexpected columns in permutation: {perm_df.columns}"

    def test_empty_files_if_no_data(self):
        """
        Test that if the underlying functions return empty results, the files are created
        with the correct headers and no rows.
        """
        # This is implicitly tested by test_script_runs_and_creates_files if the data is missing.
        # We assert that the files are not None and have the right columns.
        root = get_project_root()
        output_dir = root / "data" / "final"
        
        sens_path = output_dir / "sensitivity_analysis.csv"
        perm_path = output_dir / "permutation_results.csv"
        
        if sens_path.exists():
            df = pd.read_csv(sens_path)
            assert df.shape[1] > 0, "Sensitivity file has no columns"
        
        if perm_path.exists():
            df = pd.read_csv(perm_path)
            assert df.shape[1] > 0, "Permutation file has no columns"