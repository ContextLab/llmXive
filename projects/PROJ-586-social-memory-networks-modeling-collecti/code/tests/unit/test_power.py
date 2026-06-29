"""Unit tests for power analysis module."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.power import (
    PowerAnalysisResult,
    compute_effect_size,
    compute_power,
    compute_detectable_effect_size,
    run_power_analysis,
    generate_power_report
)


class TestPowerAnalysisResult:
    """Test PowerAnalysisResult dataclass."""

    def test_creation_with_limitation_flag(self):
        """Test creation with power limitation flag."""
        result = PowerAnalysisResult(
            power=0.65,
            effect_size=0.5,
            sample_size=2000,
            alpha=0.05,
            detectable_effect_size=0.3,
            power_limitation_flag="Power limitation detected"
        )
        assert result.power < 0.70
        assert result.power_limitation_flag is not None

    def test_creation_without_limitation_flag(self):
        """Test creation without power limitation flag."""
        result = PowerAnalysisResult(
            power=0.85,
            effect_size=0.5,
            sample_size=2000,
            alpha=0.05,
            detectable_effect_size=0.3,
            power_limitation_flag=None
        )
        assert result.power >= 0.70
        assert result.power_limitation_flag is None

    def test_to_dict(self):
        """Test dictionary conversion."""
        result = PowerAnalysisResult(
            power=0.75,
            effect_size=0.4,
            sample_size=1000,
            alpha=0.05,
            detectable_effect_size=0.25,
            power_limitation_flag=None
        )
        d = result.to_dict()
        assert 'power' in d
        assert 'effect_size' in d
        assert 'sample_size' in d
        assert 'alpha' in d
        assert 'detectable_effect_size' in d
        assert 'power_limitation_flag' in d


class TestComputeEffectSize:
    """Test effect size computation."""

    def test_large_effect(self):
        """Test computation with large effect."""
        es = compute_effect_size(
            mean_1=10.0, mean_2=5.0,
            std_1=2.0, std_2=2.0,
            n_1=100, n_2=100
        )
        assert es > 1.0  # Large effect

    def test_small_effect(self):
        """Test computation with small effect."""
        es = compute_effect_size(
            mean_1=10.0, mean_2=9.5,
            std_1=2.0, std_2=2.0,
            n_1=100, n_2=100
        )
        assert es < 0.3  # Small effect

    def test_zero_std(self):
        """Test handling of zero standard deviation."""
        es = compute_effect_size(
            mean_1=10.0, mean_2=5.0,
            std_1=0.0, std_2=0.0,
            n_1=100, n_2=100
        )
        assert es == 0.0


class TestComputePower:
    """Test power computation."""

    def test_high_power_with_large_effect(self):
        """Test that large effect yields high power."""
        power = compute_power(effect_size=1.5, sample_size=500, alpha=0.05)
        assert power > 0.9

    def test_low_power_with_small_effect(self):
        """Test that small effect yields low power."""
        power = compute_power(effect_size=0.2, sample_size=100, alpha=0.05)
        assert power < 0.5

    def test_power_increases_with_sample_size(self):
        """Test that power increases with sample size."""
        power_small = compute_power(effect_size=0.5, sample_size=100, alpha=0.05)
        power_large = compute_power(effect_size=0.5, sample_size=500, alpha=0.05)
        assert power_large > power_small


class TestComputeDetectableEffectSize:
    """Test detectable effect size computation."""

    def test_larger_sample_small_effect(self):
        """Test that larger sample allows smaller detectable effect."""
        es_small = compute_detectable_effect_size(sample_size=1000, power=0.80)
        es_large = compute_detectable_effect_size(sample_size=2000, power=0.80)
        assert es_large < es_small

    def test_returns_positive_value(self):
        """Test that detectable effect size is positive."""
        es = compute_detectable_effect_size(sample_size=1000, power=0.80)
        assert es > 0


class TestRunPowerAnalysis:
    """Test power analysis workflow."""

    def test_returns_power_result(self):
        """Test that function returns PowerAnalysisResult."""
        results_full = pd.DataFrame({
            'specialization_index': np.random.normal(1.5, 0.3, 1000),
            'retrieval_efficiency': np.random.normal(0.7, 0.1, 1000)
        })
        results_limited = pd.DataFrame({
            'specialization_index': np.random.normal(1.2, 0.4, 1000),
            'retrieval_efficiency': np.random.normal(0.6, 0.15, 1000)
        })

        result = run_power_analysis(results_full, results_limited)

        assert isinstance(result, PowerAnalysisResult)
        assert 0 <= result.power <= 1
        assert result.effect_size > 0
        assert result.sample_size == 2000

    def test_power_limitation_flag_set_when_low_power(self):
        """Test that power limitation flag is set when power < 0.70."""
        # Create data with very small effect to ensure low power
        results_full = pd.DataFrame({
            'specialization_index': np.random.normal(1.5, 0.1, 1000),
            'retrieval_efficiency': np.random.normal(0.7, 0.02, 1000)
        })
        results_limited = pd.DataFrame({
            'specialization_index': np.random.normal(1.5, 0.1, 1000),  # Same mean
            'retrieval_efficiency': np.random.normal(0.7, 0.02, 1000)  # Same mean
        })

        result = run_power_analysis(results_full, results_limited)

        # With identical means, effect size should be near zero, leading to low power
        if result.power < 0.70:
            assert result.power_limitation_flag is not None
            assert "Power limitation" in result.power_limitation_flag

    def test_power_limitation_flag_not_set_when_adequate_power(self):
        """Test that power limitation flag is not set when power >= 0.70."""
        # Create data with substantial effect to ensure adequate power
        results_full = pd.DataFrame({
            'specialization_index': np.random.normal(1.5, 0.3, 1000),
            'retrieval_efficiency': np.random.normal(0.7, 0.1, 1000)
        })
        results_limited = pd.DataFrame({
            'specialization_index': np.random.normal(1.0, 0.3, 1000),  # Different mean
            'retrieval_efficiency': np.random.normal(0.5, 0.1, 1000)  # Different mean
        })

        result = run_power_analysis(results_full, results_limited)

        # If power is adequate, flag should be None
        if result.power >= 0.70:
            assert result.power_limitation_flag is None


class TestGeneratePowerReport:
    """Test power report generation."""

    def test_creates_report_file(self):
        """Test that report file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_report.md'

            result = PowerAnalysisResult(
                power=0.75,
                effect_size=0.5,
                sample_size=2000,
                alpha=0.05,
                detectable_effect_size=0.3,
                power_limitation_flag=None
            )

            generate_power_report(result, output_path)

            assert output_path.exists()

    def test_includes_power_limitation_in_report(self):
        """Test that power limitation flag appears in report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_report.md'

            result = PowerAnalysisResult(
                power=0.65,
                effect_size=0.5,
                sample_size=2000,
                alpha=0.05,
                detectable_effect_size=0.3,
                power_limitation_flag="WARNING: Power limitation detected"
            )

            generate_power_report(result, output_path)

            content = output_path.read_text()
            assert "Power limitation" in content
            assert "WARNING" in content

    def test_includes_adequate_power_statement(self):
        """Test that adequate power statement appears in report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_report.md'

            result = PowerAnalysisResult(
                power=0.85,
                effect_size=0.5,
                sample_size=2000,
                alpha=0.05,
                detectable_effect_size=0.3,
                power_limitation_flag=None
            )

            generate_power_report(result, output_path)

            content = output_path.read_text()
            assert "adequately powered" in content.lower() or "support" in content.lower()

    def test_report_contains_required_sections(self):
        """Test that report contains all required sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_report.md'

            result = PowerAnalysisResult(
                power=0.75,
                effect_size=0.5,
                sample_size=2000,
                alpha=0.05,
                detectable_effect_size=0.3,
                power_limitation_flag=None
            )

            generate_power_report(result, output_path)

            content = output_path.read_text()
            assert "# Power Analysis Report" in content
            assert "## Methodology" in content
            assert "## Sample Size" in content
            assert "## Effect Size Estimation" in content
            assert "## Power Analysis Results" in content
            assert "## Recommendations" in content
            assert "## Conclusion" in content
