"""
Integration test for Imputation Sensitivity Analysis (T075).

This test verifies that the sensitivity analysis script runs without crashing
and produces a valid output file with the expected structure.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.validation.imputation_sensitivity import run_sensitivity_analysis, THRESHOLDS_TO_TEST

@pytest.mark.integration
def test_imputation_sensitivity_structure():
    """
    Test that the sensitivity analysis produces a valid JSON structure.
    Note: This test assumes that the prerequisite data files (merged_data.csv) exist.
    If they don't, the test should handle the failure gracefully (e.g., log error).
    """
    # We cannot run the full pipeline in a unit test environment without data.
    # So we will test the structure of the result if the function returns something.
    # However, since the function relies on external files, we will mock the file existence
    # or check the output file structure if it was run.
    
    # For this test, we will assume the data exists (or is mocked in a real CI).
    # We will run the function and check the output.
    # If the function fails due to missing data, we check that it logs an error.
    
    # Since we cannot guarantee the data exists in the test environment,
    # we will test the logic of the threshold selection and strategy decision.
    
    # We will mock the `run_pipeline_with_threshold` logic to ensure it returns the expected structure.
    # But the function `run_sensitivity_analysis` is the one we are testing.
    
    # Let's test the structure of the output file if it exists.
    # If it doesn't exist, we skip or assert that it's expected to fail in a clean env.
    
    # For the purpose of this task, we will assume the data is present.
    # If not, the test will fail, which is acceptable in a real scenario if data is missing.
    
    # We will run the analysis and check the output file.
    # This might take a long time, so we might want to mock the heavy parts.
    # But the task requires real execution.
    
    # Let's just run it and check the output structure.
    try:
        results = run_sensitivity_analysis()
        assert results is not None
        assert "thresholds_tested" in results
        assert "results" in results
        assert len(results["results"]) == len(THRESHOLDS_TO_TEST)
        
        for res in results["results"]:
            assert "threshold" in res
            assert res["threshold"] in THRESHOLDS_TO_TEST
            # Either metrics or status
            assert "metrics" in res or "status" in res
    except Exception as e:
        # If the data is missing, we expect an error.
        # We will log it and pass the test if it's a data missing error.
        if "not found" in str(e).lower():
            pytest.skip("Data files not found. Skipping integration test.")
        else:
            raise
