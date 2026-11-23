"""
Unit tests for validate_harmonized_results.py (T070).
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import pandas as pd

# Mock the module to allow testing without full pipeline state
# We will test the logic functions directly by mocking file I/O

def test_compare_distributions_no_shared_keys():
    """Test behavior when no taxa pairs overlap."""
    from code.validate_harmonized_results import compare_distributions
    
    baseline = {"correlation_results": {"A_B": {"coefficient": 0.5, "q_value": 0.01}}}
    harmonized = {"correlations": {"X_Y": {"coefficient": 0.2, "q_value": 0.01}}}
    
    result = compare_distributions(baseline, harmonized)
    
    assert result["status"] == "WARNING"
    assert "No shared taxa pairs" in result["message"]
    assert result["overlap_count"] == 0
    assert result["correlation_of_coefficients"] is None

def test_compare_distributions_calculation():
    """Test calculation of correlation and overlap."""
    from code.validate_harmonized_results import compare_distributions
    
    # Create synthetic data with known correlation
    # Coefficients: [1.0, 2.0, 3.0] vs [1.1, 2.1, 3.1] -> High correlation
    baseline_keys = ["A_B", "C_D", "E_F"]
    harm_keys = ["A_B", "C_D", "E_F"]
    
    baseline_results = {
        k: {"coefficient": float(i+1), "q_value": 0.01} 
        for i, k in enumerate(baseline_keys)
    }
    harm_results = {
        k: {"coefficient": float(i+1) + 0.1, "q_value": 0.01} 
        for i, k in enumerate(harm_keys)
    }
    
    baseline = {"correlation_results": baseline_results}
    harmonized = {"correlations": harm_results}
    
    result = compare_distributions(baseline, harmonized)
    
    assert result["status"] == "PASS"
    assert result["metrics"]["correlation_of_coefficients"] > 0.99
    assert result["metrics"]["significant_overlap_ratio"] == 1.0

def test_run_validation_pipeline_file_not_found():
    """Test that the pipeline fails loudly if artifacts are missing."""
    from code.validate_harmonized_results import run_validation_pipeline
    import sys
    
    # This test assumes the files don't exist in the temp environment
    # In a real CI, we might mock the path existence
    with pytest.raises(SystemExit):
        run_validation_pipeline()