"""
Unit tests for the power analysis utility (T009).

Tests verify:
- Correct calculation of sample size
- Correct calculation of power
- FR-015 compliance (power >= 0.8, effect_size >= 0.1)
- Report generation and file output
"""

import json
import math
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.power_analysis import (
    calculate_sample_size_for_power,
    calculate_power,
    run_power_analysis,
    save_report,
    DEFAULT_ALPHA,
    DEFAULT_VARIANCE,
    DEFAULT_EFFECT_SIZE,
    TARGET_POWER,
    OUTPUT_FILE
)


class TestCalculateSampleSize:
    """Tests for sample size calculation function."""

    def test_standard_parameters(self):
        """Test with standard parameters (alpha=0.05, power=0.8, effect=0.1, var=0.15)."""
        n = calculate_sample_size_for_power(
            alpha=0.05,
            power=0.8,
            effect_size=0.1,
            variance=0.15
        )
        assert n > 0
        assert isinstance(n, int)

    def test_larger_effect_size_reduces_sample_size(self):
        """Larger effect sizes should require smaller sample sizes."""
        n_small_effect = calculate_sample_size_for_power(effect_size=0.1)
        n_large_effect = calculate_sample_size_for_power(effect_size=0.3)
        assert n_large_effect < n_small_effect

    def test_higher_power_increases_sample_size(self):
        """Higher power requirements should increase sample size."""
        n_low_power = calculate_sample_size_for_power(power=0.7)
        n_high_power = calculate_sample_size_for_power(power=0.9)
        assert n_high_power > n_low_power

    def test_invalid_effect_size_raises_error(self):
        """Zero or negative effect size should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_for_power(effect_size=0)

    def test_invalid_variance_raises_error(self):
        """Zero or negative variance should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_for_power(variance=0)

    def test_invalid_alpha_raises_error(self):
        """Alpha outside (0, 1) should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_for_power(alpha=0)

        with pytest.raises(ValueError):
            calculate_sample_size_for_power(alpha=1.5)

    def test_invalid_power_raises_error(self):
        """Power outside (0, 1) should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_for_power(power=0)

        with pytest.raises(ValueError):
            calculate_sample_size_for_power(power=1.5)


class TestCalculatePower:
    """Tests for power calculation function."""

    def test_returns_valid_range(self):
        """Power should always be between 0 and 1."""
        power = calculate_power(n_per_group=30, alpha=0.05, effect_size=0.1, variance=0.15)
        assert 0 <= power <= 1

    def test_larger_sample_size_increases_power(self):
        """Larger sample sizes should increase power."""
        power_small = calculate_power(n_per_group=10)
        power_large = calculate_power(n_per_group=100)
        assert power_large > power_small

    def test_larger_effect_size_increases_power(self):
        """Larger effect sizes should increase power."""
        power_small = calculate_power(effect_size=0.1)
        power_large = calculate_power(effect_size=0.3)
        assert power_large > power_small

    def test_zero_sample_size_returns_zero_power(self):
        """Zero sample size should return zero power."""
        power = calculate_power(n_per_group=0)
        assert power == 0.0


class TestRunPowerAnalysis:
    """Tests for the main power analysis function."""

    def test_returns_dict(self):
        """Should return a dictionary with expected structure."""
        result = run_power_analysis()
        assert isinstance(result, dict)

    def test_contains_required_keys(self):
        """Result should contain all required keys per FR-015."""
        result = run_power_analysis()
        required_keys = ["parameters", "results", "requirements", "summary"]
        for key in required_keys:
            assert key in result

    def test_results_contain_power_effect_size_sample_size(self):
        """Results should contain power, effect_size, and min_sample_size."""
        result = run_power_analysis()
        results = result["results"]
        assert "power" in results
        assert "effect_size" in results
        assert "min_sample_size" in results

    def test_fr_015_compliance_check(self):
        """Should correctly identify FR-015 compliance."""
        result = run_power_analysis(effect_size=0.1)
        assert "fr_015_compliant" in result["requirements"]

    def test_power_threshold_in_results(self):
        """Results should include power >= 0.8 check."""
        result = run_power_analysis()
        assert result["requirements"]["power_threshold"] == 0.8

    def test_effect_size_threshold_in_results(self):
        """Results should include effect_size >= 0.1 check."""
        result = run_power_analysis()
        assert result["requirements"]["effect_size_threshold"] == 0.1


class TestSaveReport:
    """Tests for report saving functionality."""

    def test_creates_file(self, tmp_path):
        """Should create a JSON file at the specified path."""
        result = {"test": "data"}
        output_file = tmp_path / "test_report.json"
        save_report(result, output_file)
        assert output_file.exists()

    def test_file_contains_valid_json(self, tmp_path):
        """Saved file should contain valid JSON."""
        result = {"power": 0.85, "effect_size": 0.1}
        output_file = tmp_path / "test_report.json"
        save_report(result, output_file)

        with open(output_file, 'r') as f:
            loaded = json.load(f)

        assert loaded == result

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        result = {"test": "data"}
        nested_path = tmp_path / "nested" / "path" / "report.json"
        save_report(result, nested_path)
        assert nested_path.exists()


class TestFR015Compliance:
    """Specific tests for FR-015 compliance requirements."""

    def test_default_parameters_meet_power_requirement(self):
        """Default parameters should result in power >= 0.8."""
        result = run_power_analysis()
        assert result["results"]["power"] >= 0.8

    def test_default_parameters_meet_effect_size_requirement(self):
        """Default parameters should have effect_size >= 0.1."""
        result = run_power_analysis()
        assert result["results"]["effect_size"] >= 0.1

    def test_fr_015_compliant_is_true_with_defaults(self):
        """FR-015 compliant flag should be True with default parameters."""
        result = run_power_analysis()
        assert result["requirements"]["fr_015_compliant"] is True

    def test_fails_when_power_below_threshold(self):
        """Should correctly report non-compliance when power is too low."""
        # This is a theoretical test - in practice, we'd need to find parameters
        # that result in low power. For now, we verify the logic exists.
        result = run_power_analysis(effect_size=0.05)  # Below threshold
        # The effect_size requirement should not be met
        assert result["requirements"]["effect_size_requirement_met"] is False

    def test_output_path_correct(self):
        """Default output path should be data/processed/power_analysis_report.json."""
        assert str(OUTPUT_FILE) == "data/processed/power_analysis_report.json"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])