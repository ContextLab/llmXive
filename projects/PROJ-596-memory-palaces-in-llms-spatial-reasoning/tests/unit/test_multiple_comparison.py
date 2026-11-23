"""
Unit tests for multiple-comparison correction functions.
"""

import pytest
import json
import tempfile
from pathlib import Path

import numpy as np

from evaluation.multiple_comparison import (
    apply_bonferroni_correction,
    apply_holm_bonferroni_correction,
    run_multiple_comparison_correction
)


class TestBonferroniCorrection:
    def test_basic_bonferroni(self):
        """Test basic Bonferroni correction logic."""
        p_values = [0.01, 0.03, 0.05]
        num_tests = 3
        corrected = apply_bonferroni_correction(p_values, num_tests)

        # Expected: [0.03, 0.09, 0.15]
        expected = [0.03, 0.09, 0.15]

        assert len(corrected) == len(p_values)
        for c, e in zip(corrected, expected):
            assert abs(c - e) < 1e-6

    def test_capping_at_one(self):
        """Test that corrected p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.7]
        num_tests = 3
        corrected = apply_bonferroni_correction(p_values, num_tests)

        # Expected: [1.0, 1.0, 1.0] (all capped)
        assert all(c == 1.0 for c in corrected)

    def test_empty_list(self):
        """Test with empty list."""
        corrected = apply_bonferroni_correction([], 3)
        assert corrected == []


class TestHolmBonferroniCorrection:
    def test_basic_holm_bonferroni(self):
        """Test basic Holm-Bonferroni correction logic."""
        # Sorted p-values: 0.01, 0.03, 0.05
        # Adjustments:
        # i=0: 0.01 * 3 = 0.03
        # i=1: 0.03 * 2 = 0.06
        # i=2: 0.05 * 1 = 0.05 -> max(0.05, 0.06) = 0.06 (monotonicity)
        p_values = [0.01, 0.03, 0.05]
        corrected = apply_holm_bonferroni_correction(p_values)

        # Expected (after restoring order): [0.03, 0.06, 0.06]
        expected = [0.03, 0.06, 0.06]

        assert len(corrected) == len(p_values)
        for c, e in zip(corrected, expected):
            assert abs(c - e) < 1e-6

    def test_unordered_p_values(self):
        """Test with unsorted p-values."""
        p_values = [0.05, 0.01, 0.03]  # Unsorted
        corrected = apply_holm_bonferroni_correction(p_values)

        # Sorted: 0.01, 0.03, 0.05
        # Adjusted sorted: 0.03, 0.06, 0.06
        # Restored order: [0.06, 0.03, 0.06]
        expected = [0.06, 0.03, 0.06]

        assert len(corrected) == len(p_values)
        for c, e in zip(corrected, expected):
            assert abs(c - e) < 1e-6

    def test_capping_and_monotonicity(self):
        """Test that monotonicity is enforced and values capped at 1.0."""
        p_values = [0.4, 0.5, 0.6]
        corrected = apply_holm_bonferroni_correction(p_values)

        # Sorted: 0.4, 0.5, 0.6
        # Adjusted:
        # i=0: 0.4 * 3 = 1.2 -> 1.0
        # i=1: 0.5 * 2 = 1.0 -> max(1.0, 1.0) = 1.0
        # i=2: 0.6 * 1 = 0.6 -> max(0.6, 1.0) = 1.0
        # All should be 1.0
        assert all(c == 1.0 for c in corrected)

    def test_empty_list(self):
        """Test with empty list."""
        corrected = apply_holm_bonferroni_correction([])
        assert corrected == []


class TestRunMultipleComparisonCorrection:
    def test_full_workflow(self):
        """Test the full workflow of loading, correcting, and saving."""
        # Create a temporary analysis results file
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            analysis_path = tmpdir_path / "statistical_analysis.json"
            output_path = tmpdir_path / "multiple_comparison_correction.json"

            # Mock analysis data for 3 datasets
            mock_data = {
                "babi": {"p_value": 0.01, "statistic": 2.5},
                "lambada": {"p_value": 0.03, "statistic": 1.8},
                "story_cloze": {"p_value": 0.05, "statistic": 1.2}
            }

            with open(analysis_path, 'w') as f:
                json.dump(mock_data, f)

            # Run correction
            results = run_multiple_comparison_correction(
                analysis_path,
                output_path,
                correction_method='bonferroni'
            )

            # Verify results
            assert results['correction_method'] == 'bonferroni'
            assert results['num_tests'] == 3
            assert len(results['uncorrected_p_values']) == 3
            assert len(results['corrected_p_values']) == 3

            # Verify output file was created
            assert output_path.exists()

            with open(output_path, 'r') as f:
                saved_results = json.load(f)

            assert saved_results['correction_method'] == 'bonferroni'
            assert saved_results['num_tests'] == 3

    def test_holm_bonferroni_workflow(self):
        """Test Holm-Bonferroni workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            analysis_path = tmpdir_path / "statistical_analysis.json"
            output_path = tmpdir_path / "multiple_comparison_correction.json"

            mock_data = {
                "babi": {"p_value": 0.01},
                "lambada": {"p_value": 0.03},
                "story_cloze": {"p_value": 0.05}
            }

            with open(analysis_path, 'w') as f:
                json.dump(mock_data, f)

            results = run_multiple_comparison_correction(
                analysis_path,
                output_path,
                correction_method='holm-bonferroni'
            )

            assert results['correction_method'] == 'holm-bonferroni'
            assert results['num_tests'] == 3

    def test_missing_datasets(self):
        """Test error handling when not all datasets are present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            analysis_path = tmpdir_path / "statistical_analysis.json"
            output_path = tmpdir_path / "multiple_comparison_correction.json"

            # Only 2 datasets
            mock_data = {
                "babi": {"p_value": 0.01},
                "lambada": {"p_value": 0.03}
            }

            with open(analysis_path, 'w') as f:
                json.dump(mock_data, f)

            with pytest.raises(ValueError) as excinfo:
                run_multiple_comparison_correction(
                    analysis_path,
                    output_path,
                    correction_method='bonferroni'
                )

            assert "Expected p-values for 3 datasets" in str(excinfo.value)

    def test_invalid_correction_method(self):
        """Test error handling for invalid correction method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            analysis_path = tmpdir_path / "statistical_analysis.json"
            output_path = tmpdir_path / "multiple_comparison_correction.json"

            mock_data = {
                "babi": {"p_value": 0.01},
                "lambada": {"p_value": 0.03},
                "story_cloze": {"p_value": 0.05}
            }

            with open(analysis_path, 'w') as f:
                json.dump(mock_data, f)

            with pytest.raises(ValueError) as excinfo:
                run_multiple_comparison_correction(
                    analysis_path,
                    output_path,
                    correction_method='invalid_method'
                )

            assert "Unknown correction method" in str(excinfo.value)