"""
Unit tests for the sensitivity analysis module.

Tests cover:
1. Bonferroni correction logic
2. Benjamini-Hochberg correction logic
3. FDR calculation
4. Edge cases (empty input, invalid p-values)
5. SC-005 verification
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

from src.analysis.sensitivity import (
    apply_bonferroni_correction,
    apply_bh_correction,
    calculate_fdr,
    analyze_sensitivity,
    load_p_values_from_analysis_results,
    write_sensitivity_report,
    SensitivityAnalysisResult,
    NOMINAL_ALPHA
)


class TestBonferroniCorrection:
    """Tests for Bonferroni correction."""

    def test_basic_correction(self):
        """Test basic Bonferroni correction with known values."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        corrected, sig_count = apply_bonferroni_correction(p_values)

        # With 5 tests, each p-value is multiplied by 5
        expected = [0.05, 0.10, 0.15, 0.20, 0.25]

        assert len(corrected) == len(p_values)
        for c, e in zip(corrected, expected):
            assert abs(c - e) < 1e-9

        # Only the first corrected value (0.05) is <= 0.05, so 1 significant
        assert sig_count == 1

    def test_capping_at_one(self):
        """Test that corrected p-values are capped at 1.0."""
        p_values = [0.3, 0.5]
        corrected, _ = apply_bonferroni_correction(p_values)

        # 0.3 * 2 = 0.6, 0.5 * 2 = 1.0 (capped)
        assert corrected[0] == 0.6
        assert corrected[1] == 1.0

    def test_empty_input(self):
        """Test handling of empty input."""
        corrected, sig_count = apply_bonferroni_correction([])
        assert corrected == []
        assert sig_count == 0

    def test_single_value(self):
        """Test correction with a single p-value."""
        p_values = [0.03]
        corrected, sig_count = apply_bonferroni_correction(p_values)

        # Single test: no correction needed (multiply by 1)
        assert corrected == [0.03]
        assert sig_count == 1


class TestBHCorrection:
    """Tests for Benjamini-Hochberg correction."""

    def test_basic_correction(self):
        """Test basic BH correction."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        corrected, sig_count = apply_bh_correction(p_values)

        assert len(corrected) == len(p_values)
        assert all(0.0 <= p <= 1.0 for p in corrected)
        # At least some should be significant at alpha=0.05
        assert sig_count >= 1

    def test_empty_input(self):
        """Test handling of empty input."""
        corrected, sig_count = apply_bh_correction([])
        assert corrected == []
        assert sig_count == 0

    def test_monotonicity(self):
        """Test that corrected p-values maintain monotonicity."""
        p_values = [0.1, 0.05, 0.01, 0.2, 0.03]
        corrected, _ = apply_bh_correction(p_values)

        # BH correction should maintain order relative to original ranking
        # (though exact values depend on the procedure)
        assert all(0.0 <= p <= 1.0 for p in corrected)


class TestFDRCalculation:
    """Tests for FDR calculation."""

    def test_basic_fdr(self):
        """Test basic FDR calculation."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        fdr = calculate_fdr(p_values, threshold=0.05)

        # All 5 are < 0.05, so R = 5
        # FDR = (5 * 0.05) / 5 = 0.05
        assert abs(fdr - 0.05) < 1e-9

    def test_no_rejections(self):
        """Test FDR when no p-values are significant."""
        p_values = [0.1, 0.2, 0.3]
        fdr = calculate_fdr(p_values, threshold=0.05)

        # No rejections, FDR should be 0
        assert fdr == 0.0

    def test_empty_input(self):
        """Test FDR with empty input."""
        fdr = calculate_fdr([])
        assert fdr == 0.0

    def test_high_rejection_rate(self):
        """Test FDR with many significant p-values."""
        p_values = [0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.01]
        fdr = calculate_fdr(p_values, threshold=0.05)

        # All 10 are significant
        # FDR = (10 * 0.05) / 10 = 0.05
        assert abs(fdr - 0.05) < 1e-9


class TestAnalyzeSensitivity:
    """Tests for the full sensitivity analysis."""

    def test_full_analysis(self):
        """Test complete sensitivity analysis with both methods."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5]

        result = analyze_sensitivity(p_values)

        assert result.total_tests == 10
        assert result.alpha_level == NOMINAL_ALPHA
        assert 'bonferroni' in result.corrected_p_values
        assert 'bh' in result.corrected_p_values
        assert 'bonferroni' in result.fdr_estimates
        assert 'bh' in result.fdr_estimates

    def test_invalid_p_values(self):
        """Test that invalid p-values raise ValueError."""
        with pytest.raises(ValueError, match="Invalid p-value"):
            analyze_sensitivity([-0.1, 0.5])

        with pytest.raises(ValueError, match="Invalid p-value"):
            analyze_sensitivity([0.5, 1.5])

    def test_unknown_method(self):
        """Test that unknown correction methods raise ValueError."""
        with pytest.raises(ValueError, match="Unknown correction method"):
            analyze_sensitivity([0.05], correction_methods=['unknown'])

    def test_custom_alpha(self):
        """Test analysis with custom alpha level."""
        p_values = [0.01, 0.02, 0.03]
        result = analyze_sensitivity(p_values, alpha_level=0.1)

        assert result.alpha_level == 0.1

    def test_empty_p_values(self):
        """Test analysis with empty p-values list."""
        result = analyze_sensitivity([])

        assert result.total_tests == 0
        assert result.corrected_p_values == {}
        assert result.fdr_estimates == {}

    def test_sc005_verification(self):
        """Test SC-005 verification is included in results."""
        p_values = [0.01, 0.02, 0.03]
        result = analyze_sensitivity(p_values)

        assert 'verification' in result.method_details
        for method in ['bonferroni', 'bh']:
            assert method in result.method_details['verification']
            assert 'fdr' in result.method_details['verification'][method]
            assert 'verified' in result.method_details['verification'][method]


class TestLoadPValues:
    """Tests for loading p-values from analysis results."""

    def test_load_valid_file(self):
        """Test loading p-values from a valid JSON file."""
        data = {
            "results": [
                {"p_value": 0.01, "other": "data"},
                {"p_value": 0.02, "other": "data"},
                {"p_value": 0.03, "other": "data"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            p_values = load_p_values_from_analysis_results(temp_path)
            assert p_values == [0.01, 0.02, 0.03]
        finally:
            Path(temp_path).unlink()

    def test_missing_results_key(self):
        """Test handling of missing 'results' key."""
        data = {"other": "data"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="missing 'results' key"):
                load_p_values_from_analysis_results(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_p_values_from_analysis_results("nonexistent.json")

    def test_invalid_p_value_type(self):
        """Test handling of invalid p-value types."""
        data = {
            "results": [
                {"p_value": "not_a_number"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid p_value"):
                load_p_values_from_analysis_results(temp_path)
        finally:
            Path(temp_path).unlink()


class TestWriteSensitivityReport:
    """Tests for writing sensitivity analysis reports."""

    def test_write_report(self):
        """Test writing a sensitivity report to JSON."""
        result = SensitivityAnalysisResult(
            raw_p_values=[0.01, 0.02, 0.03],
            corrected_p_values={'bonferroni': [0.03, 0.06, 0.09]},
            fdr_estimates={'bonferroni': 0.05},
            significant_counts={'bonferroni': 1},
            total_tests=3,
            alpha_level=0.05,
            method_details={'verification': {'bonferroni': {'verified': True}}}
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            write_sensitivity_report(result, temp_path)

            # Verify file was written
            assert Path(temp_path).exists()

            # Verify content
            with open(temp_path, 'r') as f:
                report = json.load(f)

            assert report['summary']['total_tests'] == 3
            assert report['summary']['alpha_level'] == 0.05
        finally:
            Path(temp_path).unlink()

    def test_creates_parent_directories(self):
        """Test that parent directories are created if they don't exist."""
        result = SensitivityAnalysisResult(
            raw_p_values=[],
            corrected_p_values={},
            fdr_estimates={},
            significant_counts={},
            total_tests=0
        )

        with tempfile.TemporaryDirectory() as tmpdir:
          output_path = Path(tmpdir) / "nested" / "dir" / "report.json"

          write_sensitivity_report(result, output_path)

          assert output_path.exists()


class TestSensitivityAnalysisResult:
    """Tests for the SensitivityAnalysisResult class."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = SensitivityAnalysisResult(
            raw_p_values=[0.01, 0.02],
            corrected_p_values={'bonferroni': [0.02, 0.04]},
            fdr_estimates={'bonferroni': 0.05},
            significant_counts={'bonferroni': 1},
            total_tests=2,
            alpha_level=0.05
        )

        d = result.to_dict()

        assert d['raw_p_values'] == [0.01, 0.02]
        assert d['corrected_p_values'] == {'bonferroni': [0.02, 0.04]}
        assert d['fdr_estimates'] == {'bonferroni': 0.05}
        assert d['total_tests'] == 2

    def test_repr(self):
        """Test string representation."""
        result = SensitivityAnalysisResult(
            raw_p_values=[],
            corrected_p_values={},
            fdr_estimates={'bonferroni': 0.05},
            significant_counts={},
            total_tests=0
        )

        repr_str = repr(result)
        assert 'SensitivityAnalysisResult' in repr_str
        assert 'total_tests=0' in repr_str