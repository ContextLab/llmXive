import json
import pytest
import numpy as np
from pathlib import Path
import sys
import tempfile
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.power_analysis import (
    load_metrics,
    calculate_noncentrality_parameter,
    calculate_power,
    run_power_analysis,
    save_power_analysis
)

class TestPowerAnalysis:
    """Unit tests for post-hoc power analysis functions."""

    def test_calculate_noncentrality_parameter(self):
        """Test non-centrality parameter calculation."""
        # Test with known values
        cohen_d = 0.5
        n = 100
        expected_ncp = 0.5 * np.sqrt(100 / 2)
        calculated_ncp = calculate_noncentrality_parameter(cohen_d, n)
        
        assert np.isclose(calculated_ncp, expected_ncp)
        
        # Test with small sample
        cohen_d = 0.8
        n = 20
        expected_ncp = 0.8 * np.sqrt(20 / 2)
        calculated_ncp = calculate_noncentrality_parameter(cohen_d, n)
        
        assert np.isclose(calculated_ncp, expected_ncp)

    def test_calculate_power(self):
        """Test power calculation with known parameters."""
        from scipy import stats
        
        # Large effect size should yield high power
        ncp = 3.0
        df = 99
        alpha = 0.05
        
        power = calculate_power(ncp, df, alpha)
        
        # Power should be high for large NCP
        assert power > 0.8
        assert 0 <= power <= 1.0

    def test_run_power_analysis(self):
        """Test complete power analysis workflow."""
        cohen_d = 0.5
        n = 100
        alpha = 0.05
        
        results = run_power_analysis(cohen_d, n, alpha)
        
        # Check required fields
        assert "power" in results
        assert "effect_size_cohen_d" in results
        assert "sample_size" in results
        assert "degrees_of_freedom" in results
        assert "alpha_level" in results
        assert "noncentrality_parameter" in results
        assert "interpretation" in results
        
        # Verify values
        assert results["effect_size_cohen_d"] == cohen_d
        assert results["sample_size"] == n
        assert results["alpha_level"] == alpha
        assert 0 <= results["power"] <= 1.0
        assert results["interpretation"] in ["Adequate", "Moderate", "Low"]

    def test_run_power_analysis_low_effect(self):
        """Test power analysis with small effect size."""
        cohen_d = 0.2  # Small effect
        n = 30  # Small sample
        
        results = run_power_analysis(cohen_d, n)
        
        # Should have low power
        assert results["interpretation"] == "Low"
        assert results["power"] < 0.6

    def test_run_power_analysis_large_sample(self):
        """Test power analysis with large sample size."""
        cohen_d = 0.3  # Small-medium effect
        n = 500  # Large sample
        
        results = run_power_analysis(cohen_d, n)
        
        # Should have adequate power
        assert results["interpretation"] == "Adequate"
        assert results["power"] >= 0.8

    def test_save_power_analysis(self):
        """Test saving power analysis results to file."""
        results = {
            "power": 0.85,
            "effect_size_cohen_d": 0.5,
            "sample_size": 100,
            "interpretation": "Adequate"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power.json"
            save_power_analysis(results, str(output_path))
            
            # Verify file exists
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded["power"] == results["power"]
            assert loaded["effect_size_cohen_d"] == results["effect_size_cohen_d"]

    def test_run_power_analysis_invalid_sample_size(self):
        """Test power analysis with invalid sample size."""
        with pytest.raises(ValueError):
            run_power_analysis(cohen_d=0.5, n=1)  # n must be >= 2

    def test_power_analysis_integration(self):
        """Integration test: verify power increases with sample size."""
        cohen_d = 0.5
        
        powers = []
        for n in [20, 50, 100, 200, 500]:
            result = run_power_analysis(cohen_d, n)
            powers.append(result["power"])
        
        # Power should increase with sample size
        assert all(powers[i] <= powers[i+1] for i in range(len(powers)-1))

    def test_power_analysis_effect_size_sensitivity(self):
        """Test that power is sensitive to effect size."""
        n = 100
        
        small_effect = run_power_analysis(0.2, n)["power"]
        medium_effect = run_power_analysis(0.5, n)["power"]
        large_effect = run_power_analysis(0.8, n)["power"]
        
        # Power should increase with effect size
        assert small_effect < medium_effect < large_effect

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
