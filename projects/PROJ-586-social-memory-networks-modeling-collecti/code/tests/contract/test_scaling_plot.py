"""
Contract test for the scaling plot generation.

Verifies that the scaling plot generator produces a valid PDF with
the expected structure and content, including the reliability note.
"""
import os
import tempfile
from pathlib import Path

import pytest
import pandas as pd

from analysis.scaling_plot_generator import (
    generate_scaling_plot_with_notes,
    ScalingPlotResult
)


def test_scaling_plot_generation():
    """Test that the scaling plot is generated correctly."""
    # Create a temporary directory for test outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a minimal synthetic dataset for testing
        # (In production, this would be the real experimental data)
        test_data = {
            'agent_count': [3, 5, 7],
            'specialization_index': [0.65, 0.72, 0.78],
            'retrieval_efficiency': [0.85, 0.82, 0.80]
        }
        df = pd.DataFrame(test_data)
        data_path = tmpdir_path / "test_scaling_data.csv"
        df.to_csv(data_path, index=False)

        output_path = tmpdir_path / "test_scaling_plot.pdf"

        # Generate the plot
        result = generate_scaling_plot_with_notes(
            data_path=data_path,
            output_path=output_path
        )

        # Verify the result object
        assert isinstance(result, ScalingPlotResult)
        assert result.plot_path.exists()
        assert result.plot_path.suffix == ".pdf"

        # Verify the note text is present in the result
        assert "3 data points" in result.note_text
        assert "power-law" in result.note_text.lower()
        assert "limit" in result.note_text.lower()

        # Verify exponents are reasonable (not NaN or Inf)
        assert not (result.exponent_specialization != result.exponent_specialization)  # Not NaN
        assert not (result.extraction_exponent != result.extraction_exponent)  # Not NaN
        assert isinstance(result.exponent_specialization, float)
        assert isinstance(result.exponent_retrieval, float)

        # Verify confidence intervals are valid tuples
        assert len(result.confidence_interval_specialization) == 2
        assert len(result.confidence_interval_retrieval) == 2
        assert result.confidence_interval_specialization[0] <= result.confidence_interval_specialization[1]
        assert result.confidence_interval_retrieval[0] <= result.confidence_interval_retrieval[1]

        # Verify the file size is non-zero (actual content was written)
        assert result.plot_path.stat().st_size > 1000  # PDFs should be at least a few KB


def test_scaling_plot_with_insufficient_data():
    """Test behavior with insufficient data points."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create data with only 2 points
        test_data = {
            'agent_count': [3, 5],
            'specialization_index': [0.65, 0.72],
            'retrieval_efficiency': [0.85, 0.82]
        }
        df = pd.DataFrame(test_data)
        data_path = tmpdir_path / "test_scaling_data.csv"
        df.to_csv(data_path, index=False)

        output_path = tmpdir_path / "test_scaling_plot.pdf"

        # Should still generate a plot, but with a warning
        # (The function handles this gracefully by using conservative CI)
        result = generate_scaling_plot_with_notes(
            data_path=data_path,
            output_path=output_path
        )

        assert result.plot_path.exists()


def test_scaling_plot_missing_file():
    """Test that an error is raised when data file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        missing_path = tmpdir_path / "nonexistent.csv"
        output_path = tmpdir_path / "output.pdf"

        with pytest.raises(FileNotFoundError):
            generate_scaling_plot_with_notes(
                data_path=missing_path,
                output_path=output_path
            )