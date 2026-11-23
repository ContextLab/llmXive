"""
Unit tests for PowerCalculator in code/analysis/power_analysis.py.
"""

import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

from code.analysis.power_analysis import PowerCalculator

class TestPowerCalculator:
    """Tests for PowerCalculator class methods."""

    @pytest.fixture
    def calculator(self):
        return PowerCalculator(alpha=0.05, power_target=0.80)

    def test_compute_effect_size_etasquared(self, calculator):
        """Test eta-squared calculation from F-stat and df."""
        # Example: F=5.0, df_num=1, df_denom=20
        # eta^2 = (5 * 1) / (5 * 1 + 20) = 5 / 25 = 0.2
        f_stat = 5.0
        df_num = 1
        df_denom = 20
        expected = 0.2
        
        result = calculator.compute_effect_size_etasquared(f_stat, df_num, df_denom)
        assert np.isclose(result, expected, atol=1e-6)

    def test_compute_effect_size_zero_f(self, calculator):
        """Test eta-squared when F is 0."""
        result = calculator.compute_effect_size_etasquared(0.0, 1, 20)
        assert result == 0.0

    def test_compute_power_basic(self, calculator):
        """Test power calculation with known parameters."""
        # Large effect should yield high power with sufficient N
        f_stat = 10.0
        df_num = 1
        df_denom = 29 # N=30, k=2
        n_subjects = 30
        n_conditions = 2
        
        power = calculator.compute_power(f_stat, df_num, df_denom, n_subjects, n_conditions)
        assert 0.0 <= power <= 1.0
        # With F=10 and N=30, power should be reasonably high (> 0.5)
        assert power > 0.5

    def test_analyze_creates_file(self, calculator):
        """Test that analyze() creates the output JSON file with correct keys."""
        # Create a temporary CSV
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "metrics_summary.csv")
            output_path = os.path.join(tmpdir, "power_flags.json")
            
            # Create dummy metrics_summary.csv
            df = pd.DataFrame({
                'metric': ['completion_time', 'error_count', 'sus_score'],
                'F_stat': [5.0, 3.5, 8.0],
                'p_val': [0.03, 0.07, 0.001],
                'df_num': [1, 1, 1],
                'df_denom': [29, 29, 29],
                'n_subjects': [30, 30, 30],
                'n_conditions': [2, 2, 2]
            })
            df.to_csv(input_path, index=False)
            
            result = calculator.analyze(input_path, output_path)
            
            # Check file exists
            assert os.path.exists(output_path)
            
            # Check JSON content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert 'power' in data
            assert 'required_N' in data
            assert 'effect_size' in data
            assert 'flag' in data
            assert 'details' in data
            
            # Check types
            assert isinstance(data['power'], float)
            assert isinstance(data['required_N'], int)
            assert isinstance(data['effect_size'], float)
            assert isinstance(data['flag'], str)

    def test_analyze_underpowered_flag(self, calculator):
        """Test that underpowered results get the correct flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "metrics_summary.csv")
            output_path = os.path.join(tmpdir, "power_flags.json")
            
            # Create data with small N (10) -> likely underpowered
            df = pd.DataFrame({
                'metric': ['completion_time'],
                'F_stat': [1.5], # Small effect
                'p_val': [0.25],
                'df_num': [1],
                'df_denom': [9], # N=10
                'n_subjects': [10],
                'n_conditions': [2]
            })
            df.to_csv(input_path, index=False)
            
            result = calculator.analyze(input_path, output_path)
            
            # With N=10 and small F, flag should be underpowered or sample_too_small
            assert result['flag'] in ['underpowered', 'sample_too_small']
            assert result['observed_N'] == 10

if __name__ == "__main__":
    pytest.main([__file__, "-v"])