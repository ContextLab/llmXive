import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import tempfile
import os

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.sensitivity import run_sensitivity_analysis, save_sensitivity_report

class TestSensitivityAnalysis:
    """
    Unit tests for T020: Sensitivity analysis p-value sweep.
    Verifies that the output includes results for p-value thresholds {0.01, 0.05, 0.1}.
    """

    def test_run_sensitivity_analysis_returns_dict(self):
        """Test that the analysis function returns a dictionary."""
        # Generate synthetic p-values for testing the logic (not real data)
        # This is valid for unit testing the calculation logic of the sensitivity function.
        p_values = [0.005, 0.02, 0.04, 0.06, 0.09, 0.12, 0.15]
        
        result = run_sensitivity_analysis(p_values)
        
        assert isinstance(result, dict), "Result must be a dictionary"
        assert '0.01' in result, "Result must contain key '0.01'"
        assert '0.05' in result, "Result must contain key '0.05'"
        assert '0.1' in result, "Result must contain key '0.1'"

    def test_sensitivity_counts_correctness(self):
        """Test that counts and rates are calculated correctly for known p-values."""
        # Known p-values
        p_values = [0.005, 0.02, 0.04, 0.06, 0.09, 0.12, 0.15]
        # Total count = 7
        
        result = run_sensitivity_analysis(p_values)
        
        # For threshold 0.01: only 0.005 is significant -> count=1
        assert result['0.01']['count'] == 1, f"Expected count 1 for 0.01, got {result['0.01']['count']}"
        assert result['0.01']['rate'] == pytest.approx(1/7, rel=0.01), "Rate calculation for 0.01 is incorrect"
        
        # For threshold 0.05: 0.005, 0.02, 0.04 are significant -> count=3
        assert result['0.05']['count'] == 3, f"Expected count 3 for 0.05, got {result['0.05']['count']}"
        assert result['0.05']['rate'] == pytest.approx(3/7, rel=0.01), "Rate calculation for 0.05 is incorrect"
        
        # For threshold 0.1: 0.005, 0.02, 0.04, 0.06, 0.09 are significant -> count=5
        assert result['0.1']['count'] == 5, f"Expected count 5 for 0.1, got {result['0.1']['count']}"
        assert result['0.1']['rate'] == pytest.approx(5/7, rel=0.01), "Rate calculation for 0.1 is incorrect"

    def test_save_sensitivity_report_writes_json(self):
        """Test that the report is saved to a valid JSON file."""
        p_values = [0.005, 0.02, 0.04, 0.06, 0.09]
        result = run_sensitivity_analysis(p_values)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_test.json"
            save_sensitivity_report(result, str(output_path))
            
            assert output_path.exists(), "Output file was not created"
            
            with open(output_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert '0.01' in loaded_data
            assert '0.05' in loaded_data
            assert '0.1' in loaded_data
            assert loaded_data['0.01'] == result['0.01']
            assert loaded_data['0.05'] == result['0.05']
            assert loaded_data['0.1'] == result['0.1']

    def test_empty_p_values_handling(self):
        """Test behavior with an empty list of p-values."""
        result = run_sensitivity_analysis([])
        
        assert result['0.01']['count'] == 0
        assert result['0.01']['rate'] == 0.0
        assert result['0.05']['count'] == 0
        assert result['0.05']['rate'] == 0.0
        assert result['0.1']['count'] == 0
        assert result['0.1']['rate'] == 0.0

    def test_all_significant_p_values(self):
        """Test with all p-values below the highest threshold."""
        p_values = [0.001, 0.002, 0.003]
        result = run_sensitivity_analysis(p_values)
        
        # All should be significant for all thresholds
        assert result['0.01']['count'] == 3
        assert result['0.05']['count'] == 3
        assert result['0.1']['count'] == 3
        assert result['0.01']['rate'] == pytest.approx(1.0)
        assert result['0.05']['rate'] == pytest.approx(1.0)
        assert result['0.1']['rate'] == pytest.approx(1.0)

    def test_no_significant_p_values(self):
        """Test with all p-values above the highest threshold."""
        p_values = [0.2, 0.3, 0.5]
        result = run_sensitivity_analysis(p_values)
        
        # None should be significant
        assert result['0.01']['count'] == 0
        assert result['0.05']['count'] == 0
        assert result['0.1']['count'] == 0
        assert result['0.01']['rate'] == 0.0
        assert result['0.05']['rate'] == 0.0
        assert result['0.1']['rate'] == 0.0