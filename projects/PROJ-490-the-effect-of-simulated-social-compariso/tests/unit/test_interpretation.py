"""
Unit tests for the dynamic interpretation logic (T020).
"""
import pytest
import json
import tempfile
from pathlib import Path

from analysis.interpretation import (
    determine_interpretation_label,
    generate_interpretation_summary,
    run_interpretation
)


class TestDetermineInterpretationLabel:
    """Tests for determine_interpretation_label function."""

    def test_real_data_label(self):
        """Real data should return 'Empirical Association'."""
        label = determine_interpretation_label("real")
        assert label == "Empirical Association"

    def test_synthetic_data_label(self):
        """Synthetic data should return 'Simulated Causal Effect'."""
        label = determine_interpretation_label("synthetic")
        assert label == "Simulated Causal Effect"

    def test_invalid_data_type_raises(self):
        """Invalid data type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown data_source_type"):
            determine_interpretation_label("unknown")


class TestGenerateInterpretationSummary:
    """Tests for generate_interpretation_summary function."""

    def test_summary_structure_real(self):
        """Check summary structure for real data."""
        results = {"coefficient": 0.5, "p_value": 0.01}
        summary = generate_interpretation_summary(results, "real")

        assert summary["interpretation_label"] == "Empirical Association"
        assert summary["data_source_type"] == "real"
        assert summary["results"] == results

    def test_summary_structure_synthetic(self):
        """Check summary structure for synthetic data."""
        results = {"coefficient": 0.5, "p_value": 0.01}
        summary = generate_interpretation_summary(results, "synthetic")

        assert summary["interpretation_label"] == "Simulated Causal Effect"
        assert summary["data_source_type"] == "synthetic"
        assert summary["results"] == results

    def test_summary_includes_coefficients(self):
        """Check that highlighted coefficients are included if provided."""
        results = {"coefficient": 0.5}
        coeffs = {"avatar_condition": 0.2}
        summary = generate_interpretation_summary(results, "real", coeffs)

        assert summary["highlighted_coefficients"] == coeffs


class TestRunInterpretation:
    """Tests for run_interpretation function."""

    def test_run_interpretation_creates_file(self):
        """Verify that run_interpretation creates the output file."""
        results = {"coefficient": 0.5, "p_value": 0.01}

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_path = tmpdir_path / "results.json"
            output_path = tmpdir_path / "interpreted_results.json"

            with open(input_path, 'w') as f:
                json.dump(results, f)

                summary = run_interpretation(input_path, "real", output_path)

                assert output_path.exists()
                assert summary["interpretation_label"] == "Empirical Association"

                with open(output_path, 'r') as f:
                    saved_data = json.load(f)

                assert saved_data["interpretation_label"] == "Empirical Association"

    def test_run_interpretation_missing_file_raises(self):
        """Verify that run_interpretation raises FileNotFoundError for missing input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.json"
            output_path = Path(tmpdir) / "output.json"

            with pytest.raises(FileNotFoundError):
                run_interpretation(input_path, "real", output_path)