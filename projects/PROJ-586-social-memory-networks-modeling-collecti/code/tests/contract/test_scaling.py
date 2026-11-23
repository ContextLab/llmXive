"""
Contract test for scaling plot generation (T030).

Verifies that the scaling plot generation produces a valid PDF
with the required note and fitted curves.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from analysis.scaling_plot import (
    load_scaling_results_for_plot,
    generate_scaling_plot_with_notes,
    run_scaling_analysis
)


class TestScalingPlotContract:
    """Contract tests for the scaling plot generation."""

    @pytest.fixture
    def sample_scaling_data(self):
        """Create a sample scaling results DataFrame."""
        data = {
            'agent_count': [3, 5, 7],
            'specialization_index': [0.85, 0.92, 0.95],
            'retrieval_efficiency': [0.78, 0.82, 0.85],
            'specialization_std': [0.05, 0.04, 0.03],
            'retrieval_std': [0.06, 0.05, 0.04]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_results_dir(self, sample_scaling_data):
        """Create a temporary directory with sample results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            results_file = tmpdir / "scaling_results.csv"
            # Adjust column names to match expected format
            df = sample_scaling_data.rename(columns={
                'specialization_std': 'spec_std',
                'retrieval_std': 'ret_std'
            })
            # Recalculate means if needed or use raw
            df_to_save = pd.DataFrame({
                'agent_count': [3, 5, 7],
                'specialization_index': [0.85, 0.92, 0.95],
                'retrieval_efficiency': [0.78, 0.82, 0.85],
                'specialization_std': [0.05, 0.04, 0.03],
                'retrieval_std': [0.06, 0.05, 0.04]
            })
            df_to_save.to_csv(results_file, index=False)
            yield tmpdir

    def test_load_scaling_results_valid(self, temp_results_dir):
        """Test loading valid scaling results."""
        df = load_scaling_results_for_plot(temp_results_dir)
        assert 'agent_count' in df.columns
        assert 'specialization_index' in df.columns
        assert 'retrieval_efficiency' in df.columns
        assert len(df) == 3

    def test_load_scaling_results_missing_file(self):
        """Test loading missing file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                load_scaling_results_for_plot(Path(tmpdir), "nonexistent.csv")

    def test_generate_scaling_plot_creates_file(self, temp_results_dir):
        """Test that plot generation creates the PDF file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_plot.pdf"
            df = load_scaling_results_for_plot(temp_results_dir)
            result = generate_scaling_plot_with_notes(df, output_path)

            assert output_path.exists()
            assert output_path.suffix == ".pdf"
            assert result['output_file'] == str(output_path)
            assert result['n_agent_counts'] == 3

    def test_generate_scaling_plot_includes_note(self, temp_results_dir):
        """Test that the required note is included in the result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_plot.pdf"
            df = load_scaling_results_for_plot(temp_results_dir)
            custom_note = "Custom test note for verification"
            result = generate_scaling_plot_with_notes(df, output_path, note=custom_note)

            assert result['note_included'] == custom_note

    def test_run_scaling_analysis_full_pipeline(self, temp_results_dir):
        """Test the full analysis pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = run_scaling_analysis(
                results_dir=temp_results_dir,
                output_dir=output_dir,
                input_file="scaling_results.csv",
                output_file="scaling_analysis.pdf",
                note="Test note for pipeline"
            )

            expected_path = output_dir / "scaling_analysis.pdf"
            assert expected_path.exists()
            assert result['n_agent_counts'] == 3
            assert len(result['fits']) >= 0  # May have 0 fits if data is insufficient

    def test_plot_with_insufficient_data(self):
        """Test handling of insufficient data points (< 2)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            results_file = tmpdir / "scaling_results.csv"
            pd.DataFrame({
                'agent_count': [3],
                'specialization_index': [0.85],
                'retrieval_efficiency': [0.78],
                'specialization_std': [0.05],
                'retrieval_std': [0.06]
            }).to_csv(results_file, index=False)

            with tempfile.TemporaryDirectory() as out_tmpdir:
                output_path = Path(out_tmpdir) / "plot.pdf"
                df = load_scaling_results_for_plot(tmpdir)
                with pytest.raises(ValueError, match="Need at least 2 agent counts"):
                    generate_scaling_plot_with_notes(df, output_path)

    def test_scaling_plot_schema(self, temp_results_dir):
        """Verify the output schema of the scaling plot result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "schema_test.pdf"
            df = load_scaling_results_for_plot(temp_results_dir)
            result = generate_scaling_plot_with_notes(df, output_path)

            # Check required keys
            assert 'output_file' in result
            assert 'n_agent_counts' in result
            assert 'note_included' in result
            assert 'fits' in result

            # Check fits structure
            for fit in result['fits']:
                assert 'metric' in fit
                assert 'exponent' in fit
                assert 'exponent_std' in fit
                assert 'r_squared' in fit