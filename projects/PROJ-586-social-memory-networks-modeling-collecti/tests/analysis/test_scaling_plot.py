"""
Tests for T030: Scaling Plot Generation.
"""
import json
import tempfile
from pathlib import Path

import pytest

from analysis.scaling_plot_generator import generate_scaling_plot_with_notes


class TestScalingPlotGeneration:
    """Test suite for the scaling plot generator."""

    @pytest.fixture
    def sample_data(self):
        """Sample scaling data for testing."""
        return [
            {"agent_count": 3, "specialization_index": 1.1, "retrieval_efficiency": 0.85},
            {"agent_count": 5, "specialization_index": 1.4, "retrieval_efficiency": 0.78},
            {"agent_count": 7, "specialization_index": 1.6, "retrieval_efficiency": 0.72}
        ]

    @pytest.fixture
    def temp_input_file(self, sample_data):
        """Create a temporary input JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_data, f)
            return Path(f.name)

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary output file path."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            path = Path(f.name)
        return path

    def test_plot_generation_creates_file(self, temp_input_file, temp_output_file):
        """Test that the plot generation creates the output file."""
        result = generate_scaling_plot_with_notes(
            input_data_path=temp_input_file,
            output_path=temp_output_file,
            note_text="Test note"
        )
        assert temp_output_file.exists(), "Output PDF file was not created."
        assert result["data_points"] == 3
        assert "specialization_fit" in result
        assert "retrieval_fit" in result

    def test_plot_generation_with_note(self, temp_input_file, temp_output_file):
        """Test that the note text is included in the result metadata."""
        note_text = "3 data points limit power-law reliability"
        result = generate_scaling_plot_with_notes(
            input_data_path=temp_input_file,
            output_path=temp_output_file,
            note_text=note_text
        )
        assert result["note"] == note_text

    def test_plot_generation_with_filtered_agents(self, temp_input_file, temp_output_file):
        """Test filtering agent counts."""
        result = generate_scaling_plot_with_notes(
            input_data_path=temp_input_file,
            output_path=temp_output_file,
            agent_counts=[3, 5]
        )
        assert result["data_points"] == 2
        assert 7 not in result["agent_counts"]

    def test_plot_generation_insufficient_data(self, temp_output_file):
        """Test that insufficient data raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"agent_count": 3, "specialization_index": 1.1, "retrieval_efficiency": 0.85}], f)
            input_file = Path(f.name)

        with pytest.raises(ValueError, match="Insufficient data points"):
            generate_scaling_plot_with_notes(
                input_data_path=input_file,
                output_path=temp_output_file
            )
        input_file.unlink()

    def test_plot_generation_invalid_input(self, temp_output_file):
        """Test that missing input file raises an error."""
        with pytest.raises(FileNotFoundError):
            generate_scaling_plot_with_notes(
                input_data_path=Path("non_existent.json"),
                output_path=temp_output_file
            )

    def test_plot_file_size(self, temp_input_file, temp_output_file):
        """Test that the generated PDF has a reasonable size."""
        result = generate_scaling_plot_with_notes(
            input_data_path=temp_input_file,
            output_path=temp_output_file,
            note_text="Test"
        )
        assert temp_output_file.stat().st_size > 1000, "Generated PDF is too small."