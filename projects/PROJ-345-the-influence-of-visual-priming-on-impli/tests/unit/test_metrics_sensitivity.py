import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from code.models.metrics import calculate_sensitivity_analysis, run_sensitivity_analysis

class TestSensitivityAnalysis:
    def test_calculate_sensitivity_analysis_basic(self):
        """Test basic sensitivity analysis calculation."""
        # Create dummy data with known p-values
        data = {
            'p_value': [0.005, 0.015, 0.025, 0.035, 0.045, 0.055, 0.065, 0.075, 0.085, 0.095, 0.150]
        }
        df = pd.DataFrame(data)
        
        result = calculate_sensitivity_analysis(df)
        
        assert 'alpha' in result.columns
        assert 'significance_rate' in result.columns
        assert len(result) == 10
        
        # Check specific values
        # alpha=0.01: 1/11 significant (0.005) -> 0.0909
        # alpha=0.05: 5/11 significant (0.005..0.045) -> 0.4545
        # alpha=0.10: 10/11 significant (all except 0.150) -> 0.9090
        
        assert list(result['alpha']) == [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
        
        # Verify rates
        assert abs(result.loc[result['alpha'] == 0.01, 'significance_rate'].values[0] - 1/11) < 0.01
        assert abs(result.loc[result['alpha'] == 0.05, 'significance_rate'].values[0] - 5/11) < 0.01
        assert abs(result.loc[result['alpha'] == 0.10, 'significance_rate'].values[0] - 10/11) < 0.01

    def test_calculate_sensitivity_analysis_empty(self):
        """Test with empty dataframe."""
        df = pd.DataFrame(columns=['p_value'])
        result = calculate_sensitivity_analysis(df)
        
        assert len(result) == 10
        assert all(result['significance_rate'] == 0.0)

    def test_run_sensitivity_analysis_writes_file(self):
        """Test that run_sensitivity_analysis writes the CSV file."""
        data = {
            'p_value': [0.001, 0.05, 0.10, 0.20]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sensitivity.csv"
            
            result = run_sensitivity_analysis(df, output_path)
            
            assert output_path.exists()
            assert result is not None
            assert len(result) == 10
            
            # Verify content
            loaded = pd.read_csv(output_path)
            assert 'alpha' in loaded.columns
            assert 'significance_rate' in loaded.columns
            assert list(loaded['alpha']) == [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]

    def test_missing_p_value_column(self):
        """Test behavior when p_value column is missing."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        result = calculate_sensitivity_analysis(df)
        
        # Should return zeros
        assert all(result['significance_rate'] == 0.0)
        assert len(result) == 10