import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from diagnostics import calculate_power, generate_diagnostics_report

class TestPowerAnalysis:
    """Tests for power analysis functionality in T084."""

    def test_calculate_power_basic(self):
        """Test basic power calculation with known parameters."""
        result = calculate_power(observed_n=100, target_r=0.3)
        
        assert result["observed_n"] == 100
        assert result["target_r"] == 0.3
        assert "required_n" in result
        assert "observed_power" in result
        assert "underpowered" in result
        assert result["message"] in ["Underpowered", "Adequately powered"]

    def test_calculate_power_underpowered(self):
        """Test power calculation when observed N is too small."""
        # For r=0.3, power=0.8, alpha=0.05, required N is approximately 85
        # So N=50 should be underpowered
        result = calculate_power(observed_n=50, target_r=0.3)
        
        assert result["underpowered"] is True
        assert result["observed_n"] < result["required_n"]

    def test_calculate_power_adequate(self):
        """Test power calculation when observed N is sufficient."""
        # N=200 should be adequate for r=0.3
        result = calculate_power(observed_n=200, target_r=0.3)
        
        assert result["underpowered"] is False
        assert result["observed_n"] >= result["required_n"]

    def test_calculate_power_zero_correlation(self):
        """Test power calculation with zero correlation (edge case)."""
        result = calculate_power(observed_n=100, target_r=0.0)
        
        assert result["observed_power"] == 0.0
        assert "Cannot calculate power for zero correlation" in result["message"]

    def test_calculate_power_small_sample(self):
        """Test power calculation with very small sample size."""
        result = calculate_power(observed_n=2, target_r=0.3)
        
        assert result["observed_power"] == 0.0
        assert result["underpowered"] is True

    def test_calculate_power_high_correlation(self):
        """Test power calculation with high correlation (easier to detect)."""
        result = calculate_power(observed_n=30, target_r=0.7)
        
        # High correlation requires smaller sample
        assert result["required_n"] < 100
        assert result["underpowered"] is False

    def test_calculate_power_output_structure(self):
        """Test that power analysis output matches expected schema for T084."""
        result = calculate_power(observed_n=150)
        
        required_keys = [
            "observed_n", 
            "required_n", 
            "observed_power", 
            "target_power", 
            "target_r", 
            "alpha", 
            "underpowered", 
            "message"
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

    def test_generate_diagnostics_report_includes_power(self):
        """Test that the full diagnostics report includes power analysis section."""
        # Create mock data
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            'taxon_A': np.random.normal(0, 1, n),
            'taxon_B': np.random.normal(0, 1, n),
            'sleep_metric': np.random.normal(0, 1, n)
        })
        
        correlation_results = {
            'pairs': [['taxon_A', 'sleep_metric']],
            'p_values': [0.03]
        }
        
        report = generate_diagnostics_report(data, ['taxon_A', 'taxon_B'], correlation_results)
        
        assert "power" in report
        assert report["power"]["observed_n"] == n
        assert "underpowered" in report["power"]

    def test_power_analysis_json_serialization(self):
        """Test that power analysis results can be serialized to JSON."""
        result = calculate_power(observed_n=100)
        
        # Should not raise
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        
        assert parsed["observed_n"] == 100

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
