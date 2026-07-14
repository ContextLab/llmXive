"""
Unit tests for the power analysis module.
"""
import json
import math
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.power_analysis import calculate_minimum_sample_size, _inverse_normal_cdf

class TestInverseNormalCdf:
    """Tests for the inverse normal CDF approximation."""

    def test_median_is_zero(self):
        assert abs(_inverse_normal_cdf(0.5)) < 1e-6

    def test_extreme_values(self):
        # Z for 0.975 is approx 1.96
        assert abs(_inverse_normal_cdf(0.975) - 1.96) < 0.05
        # Z for 0.025 is approx -1.96
        assert abs(_inverse_normal_cdf(0.025) - (-1.96)) < 0.05

    def test_invalid_input(self):
        with pytest.raises(ValueError):
            _inverse_normal_cdf(0.0)
        with pytest.raises(ValueError):
            _inverse_normal_cdf(1.0)

class TestCalculateMinimumSampleSize:
    """Tests for the minimum sample size calculation."""

    def test_default_parameters(self):
        # Default: power=0.8, alpha=0.05, effect_size=0.5
        # Z_alpha/2 (0.05) ~ 1.96
        # Z_beta (0.8) ~ 0.84
        # n = 2 * ((1.96 + 0.84) / 0.5)^2 = 2 * (2.8 / 0.5)^2 = 2 * 5.6^2 = 2 * 31.36 = 62.72 -> 63
        result = calculate_minimum_sample_size(power=0.8, alpha=0.05, effect_size=0.5)
        assert result >= 60 and result <= 70  # Allow small approximation variance

    def test_higher_power_requires_more_samples(self):
        base_n = calculate_minimum_sample_size(power=0.8, alpha=0.05, effect_size=0.5)
        higher_n = calculate_minimum_sample_size(power=0.9, alpha=0.05, effect_size=0.5)
        assert higher_n > base_n

    def test_smaller_effect_size_requires_more_samples(self):
        base_n = calculate_minimum_sample_size(power=0.8, alpha=0.05, effect_size=0.5)
        smaller_effect_n = calculate_minimum_sample_size(power=0.8, alpha=0.05, effect_size=0.2)
        assert smaller_effect_n > base_n

    def test_invalid_power(self):
        with pytest.raises(ValueError):
            calculate_minimum_sample_size(power=1.5)
        with pytest.raises(ValueError):
            calculate_minimum_sample_size(power=0.0)

    def test_invalid_alpha(self):
        with pytest.raises(ValueError):
            calculate_minimum_sample_size(alpha=1.5)
        with pytest.raises(ValueError):
            calculate_minimum_sample_size(alpha=0.0)

    def test_invalid_effect_size(self):
        with pytest.raises(ValueError):
            calculate_minimum_sample_size(effect_size=0.0)
        with pytest.raises(ValueError):
            calculate_minimum_sample_size(effect_size=-0.5)

class TestPowerAnalysisIntegration:
    """Integration tests for the power analysis script."""

    def test_main_creates_output_file(self, tmp_path, monkeypatch):
        """Test that main() creates the expected output file."""
        from code import config, power_analysis

        # Mock the METRICS_DIR to use a temporary directory
        monkeypatch.setattr(config, "METRICS_DIR", tmp_path)
        
        # Run main
        power_analysis.main()

        # Verify file exists
        output_file = tmp_path / "power_analysis_report.json"
        assert output_file.exists()

        # Verify content is valid JSON
        with open(output_file) as f:
            data = json.load(f)

        assert "analysis_type" in data
        assert "parameters" in data
        assert "results" in data
        assert "minimum_sample_size_per_group" in data["results"]
        assert data["results"]["minimum_sample_size_per_group"] > 0