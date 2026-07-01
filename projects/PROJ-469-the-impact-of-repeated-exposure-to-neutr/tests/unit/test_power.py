"""
Unit tests for power analysis module (T017a).
"""
import pytest
import pandas as pd
import os
import sys
from pathlib import Path

# Add code directory to path for imports
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from power import calculate_ncp, calculate_power_from_ncp, find_min_sample_size, LITERATURE_F2, POWER_TARGET

class TestPowerCalculations:
    def test_ncp_calculation(self):
        """Test non-centrality parameter calculation."""
        f2 = 0.15
        n = 100
        expected_ncp = 15.0
        assert calculate_ncp(f2, n) == expected_ncp

    def test_power_calculation_basic(self):
        """Test power calculation with known parameters."""
        # With large N, power should be high
        ncp = 10.0
        df_num = 1
        df_denom = 1000
        alpha = 0.05
        power = calculate_power_from_ncp(ncp, df_num, df_denom, alpha)
        assert 0.0 <= power <= 1.0
        assert power > 0.5  # Should have decent power with this NCP

    def test_power_calculation_low_ncp(self):
        """Test power calculation with low NCP (should be low power)."""
        ncp = 0.5
        df_num = 1
        df_denom = 100
        alpha = 0.05
        power = calculate_power_from_ncp(ncp, df_num, df_denom, alpha)
        assert 0.0 <= power <= 1.0
        assert power < 0.3  # Low NCP should yield low power

    def test_find_min_sample_size_small_effect(self):
        """Test finding minimum sample size for small effect."""
        required_n, power = find_min_sample_size(
            f2=0.02,  # Small effect
            alpha=0.05,
            power_target=0.80,
            max_n=10000,
            step=10
        )
        assert required_n is not None
        assert required_n > 0
        assert power >= 0.80

    def test_find_min_sample_size_medium_effect(self):
        """Test finding minimum sample size for medium effect."""
        required_n, power = find_min_sample_size(
            f2=0.15,  # Medium effect
            alpha=0.05,
            power_target=0.80,
            max_n=10000,
            step=10
        )
        assert required_n is not None
        assert required_n > 0
        assert power >= 0.80
        # Medium effect should require smaller N than small effect
        small_n, _ = find_min_sample_size(0.02, 0.05, 0.80, 10000, 10)
        assert required_n < small_n

    def test_find_min_sample_size_high_alpha(self):
        """Test sample size calculation with higher alpha (should be smaller N)."""
        n_005, _ = find_min_sample_size(0.15, 0.05, 0.80, 10000, 10)
        n_010, _ = find_min_sample_size(0.15, 0.10, 0.80, 10000, 10)
        assert n_010 <= n_005  # Higher alpha should require smaller sample

class TestPowerOutput:
    @pytest.fixture
    def temp_results_dir(self, tmp_path):
        """Create a temporary results directory."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        return results_dir

    def test_output_csv_structure(self, temp_results_dir, monkeypatch):
        """Test that the output CSV has the expected structure."""
        from power import run_power_analysis
        from config_manager import get_results_path, get_alpha_level, get_analysis_seed
        
        # Mock config functions to use temp directory
        def mock_get_results_path():
            return str(temp_results_dir)
        
        def mock_get_alpha_level():
            return 0.05
        
        def mock_get_analysis_seed():
            return 42

        monkeypatch.setattr("power.get_results_path", mock_get_results_path)
        monkeypatch.setattr("power.get_alpha_level", mock_get_alpha_level)
        monkeypatch.setattr("power.get_analysis_seed", mock_get_analysis_seed)
        
        df = run_power_analysis()
        
        # Check file exists
        output_path = temp_results_dir / "power_design.csv"
        assert output_path.exists()
        
        # Check columns
        expected_cols = ["effect_size_f2", "alpha_level", "target_power", "required_n", "achieved_power", "met_target"]
        assert all(col in df.columns for col in expected_cols)
        
        # Check required_n is positive
        assert df["required_n"].iloc[0] > 0
        
        # Check met_target is "Yes" or "No"
        assert df["met_target"].iloc[0] in ["Yes", "No"]