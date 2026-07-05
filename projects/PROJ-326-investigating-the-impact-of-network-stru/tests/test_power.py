"""
Unit tests for the statistical power analysis module (T044).
"""
import json
import math
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from code.src.analysis.power import (
    calculate_effect_size_r_to_cohen_d,
    calculate_power_t_test_two_tailed,
    compute_power_analysis,
    generate_power_report,
    TARGET_CORRELATION_R,
    TARGET_POWER,
    MIN_SAMPLE_SIZE
)


class TestEffectSizeConversion:
    """Tests for converting Pearson's r to Cohen's d."""

    def test_r_to_d_positive(self):
        """Test conversion for positive correlation."""
        r = 0.5
        expected_d = (2 * r) / math.sqrt(1 - r**2)
        calculated_d = calculate_effect_size_r_to_cohen_d(r)
        assert abs(calculated_d - expected_d) < 1e-6

    def test_r_to_d_negative(self):
        """Test conversion for negative correlation."""
        r = -0.5
        expected_d = (2 * abs(r)) / math.sqrt(1 - r**2) # d is usually magnitude for power
        calculated_d = calculate_effect_size_r_to_cohen_d(r)
        # Our function returns magnitude for power calc context, or signed?
        # The implementation uses abs(r) for d calculation in power context usually, 
        # but let's check the function logic: it uses 2*r. 
        # If r is negative, d is negative. Power calculation uses abs(d) implicitly via ncp logic?
        # Actually, our implementation: ncp = effect_size * sqrt(n/2). 
        # If effect_size is negative, ncp is negative. 
        # Power is 1 - cdf(t_crit) + cdf(-t_crit). 
        # For negative ncp, the distribution shifts left. 
        # Let's just test the formula.
        expected = (2 * r) / math.sqrt(1 - r**2)
        assert abs(calculated_d - expected) < 1e-6

    def test_r_to_d_invalid(self):
        """Test that r=1.0 raises an error."""
        with pytest.raises(ValueError):
            calculate_effect_size_r_to_cohen_d(1.0)

        with pytest.raises(ValueError):
            calculate_effect_size_r_to_cohen_d(-1.0)


class TestPowerCalculation:
    """Tests for the power calculation logic."""

    def test_power_high_effect_size(self):
        """Test that high effect size yields high power."""
        # Large effect size d=0.8, n=100 -> Power should be high (> 0.9)
        power = calculate_power_t_test_two_tailed(0.8, 100)
        assert power > 0.9

    def test_power_low_effect_size(self):
        """Test that low effect size yields lower power."""
        # Small effect size d=0.2, n=100 -> Power should be moderate (~0.29)
        power = calculate_power_t_test_two_tailed(0.2, 100)
        # Roughly 0.29 for d=0.2, n=100
        assert power < 0.5

    def test_power_small_sample(self):
        """Test power with very small sample size."""
        power = calculate_power_t_test_two_tailed(0.5, 5)
        assert power < 0.5

    def test_power_zero_effect(self):
        """Test power when effect size is zero."""
        power = calculate_power_t_test_two_tailed(0.0, 100)
        # Power should be equal to alpha (0.05)
        assert abs(power - 0.05) < 0.01


class TestPowerAnalysisIntegration:
    """Integration tests for the full power analysis pipeline."""

    def test_compute_power_analysis_regression_only(self):
        """Test power calculation with only regression results."""
        reg_results = [
            {"r": 0.5, "n": 100},
            {"r": 0.3, "n": 100}
        ]
        anova_results = []
        
        metrics = compute_power_analysis(reg_results, anova_results, sample_size=100)
        
        assert metrics["sample_size"] == 100
        assert len(metrics["regression_power_analysis"]) == 2
        assert metrics["overall_achieved_power"] < 1.0 # Should be the minimum of the two
        
        # Check validation
        # Target r is 0.3. Max observed is 0.5. Sample size 100.
        # Power for r=0.5 (d ~ 1.15) with n=100 is very high.
        # Power for r=0.3 (d ~ 0.63) with n=100 is ~0.78 (close to 0.8).
        # The minimum power determines the overall.
        assert "design_validation" in metrics
        # If the minimum power is < 0.8, it might fail depending on the exact calculation.
        # r=0.3 -> d=0.636. n=100. Power ~ 0.78.
        # So it might fail the power target.
        if metrics["overall_achieved_power"] < 0.8:
            assert not metrics["design_validation"]["passed"]
            assert any("below target" in reason for reason in metrics["design_validation"]["reasons"])

    def test_compute_power_analysis_failed_design(self):
        """Test power calculation with a design that fails validation."""
        # Low sample size
        reg_results = [{"r": 0.2, "n": 50}]
        anova_results = []
        
        metrics = compute_power_analysis(reg_results, anova_results, sample_size=50)
        
        assert metrics["sample_size"] == 50
        assert not metrics["design_validation"]["passed"]
        assert any("below minimum threshold" in reason for reason in metrics["design_validation"]["reasons"])

    def test_generate_power_report(self):
        """Test that the report file is generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_report.json"
            
            metrics = {
                "sample_size": 100,
                "target_correlation_r": 0.3,
                "significance_level": 0.05,
                "target_power": 0.8,
                "regression_power_analysis": [],
                "anova_power_analysis": [],
                "overall_achieved_power": 0.75,
                "design_validation": {
                    "passed": False,
                    "reasons": ["Power below target"]
                }
            }
            
            generate_power_report(output_path, metrics)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "generated_at" in data
            assert data["validation_summary"]["passed"] == False
            assert "Power below target" in data["validation_summary"]["details"]

class TestPowerAnalysisEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_results(self):
        """Test power analysis with empty results."""
        metrics = compute_power_analysis([], [], sample_size=100)
        assert metrics["overall_achieved_power"] == 0.0
        assert not metrics["design_validation"]["passed"]
        assert any("No valid effect sizes" in reason for reason in metrics["design_validation"]["reasons"])

    def test_invalid_correlation_in_results(self):
        """Test handling of invalid correlation values in results."""
        reg_results = [{"r": 1.5, "n": 100}] # Invalid r > 1
        metrics = compute_power_analysis(reg_results, [], sample_size=100)
        # Should handle gracefully, likely resulting in 0 power for that entry
        # and potentially failing validation.
        assert len(metrics["regression_power_analysis"]) == 1
        # The function logs a warning and sets d=0, so power will be low.
        assert metrics["regression_power_analysis"][0]["achieved_power"] == 0.0