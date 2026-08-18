import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import matplotlib
# Force non-interactive backend for testing
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pytest

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from visualize import generate_boxplot, save_boxplot


class TestBoxplotGeneration:
    """Unit tests for boxplot generation parameters (DPI, labels)."""

    @pytest.fixture
    def sample_data(self):
        """Create sample turnaround time data for AI and non-AI groups."""
        return {
            'ai_group': [12.5, 14.2, 11.8, 15.0, 13.1, 10.5, 16.2, 12.0, 14.5, 13.8],
            'non_ai_group': [24.5, 28.2, 21.8, 25.0, 31.1, 20.5, 26.2, 22.0, 24.5, 23.8, 29.0, 27.5]
        }

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_boxplot_labels(self, sample_data):
        """Test that the boxplot has correct axis labels."""
        fig, ax = generate_boxplot(sample_data['ai_group'], sample_data['non_ai_group'])

        # Check X-axis label
        xlabel = ax.get_xlabel()
        assert 'PR Type' in xlabel or 'Group' in xlabel, f"Expected 'PR Type' or 'Group' in x-label, got: {xlabel}"

        # Check Y-axis label
        ylabel = ax.get_ylabel()
        assert 'Turnaround Time' in ylabel or 'Hours' in ylabel, f"Expected 'Turnaround Time' or 'Hours' in y-label, got: {ylabel}"

    def test_boxplot_dpi_parameter(self, sample_data, temp_output_dir):
        """Test that the boxplot is saved with the correct DPI (>= 300)."""
        output_path = os.path.join(temp_output_dir, 'test_boxplot.png')

        # Call the save function which should handle DPI
        save_boxplot(sample_data['ai_group'], sample_data['non_ai_group'], output_path, dpi=300)

        # Verify file exists
        assert os.path.exists(output_path), f"Output file not created at {output_path}"

        # Verify file size is reasonable (a 300 DPI plot should be > 50KB)
        file_size = os.path.getsize(output_path)
        assert file_size > 50000, f"File size {file_size} is too small for 300 DPI image"

        # Open and verify DPI metadata
        from PIL import Image
        img = Image.open(output_path)
        dpi_x, dpi_y = img.info.get('dpi', (0, 0))
        assert dpi_x >= 300 and dpi_y >= 300, f"Expected DPI >= 300, got ({dpi_x}, {dpi_y})"

    def test_boxplot_title(self, sample_data):
        """Test that the boxplot has a descriptive title."""
        fig, ax = generate_boxplot(sample_data['ai_group'], sample_data['non_ai_group'])

        title = ax.get_title()
        assert len(title) > 0, "Boxplot should have a title"
        assert 'Turnaround Time' in title or 'Comparison' in title, f"Title should describe the plot, got: {title}"

    def test_boxplot_data_groups(self, sample_data):
        """Test that both AI and non-AI groups are represented in the plot."""
        fig, ax = generate_boxplot(sample_data['ai_group'], sample_data['non_ai_group'])

        # Get the collections (boxes) from the plot
        collections = ax.collections

        # There should be at least 2 boxplot elements (one for each group)
        # Note: This is a heuristic check; exact number depends on matplotlib version
        assert len(collections) >= 2, f"Expected at least 2 boxplot elements, got {len(collections)}"

    def test_boxplot_outlier_handling(self, sample_data):
        """Test that outliers are handled correctly (IQR method)."""
        # Add extreme outliers to test IQR handling
        ai_with_outliers = sample_data['ai_group'] + [100.0, -50.0]
        non_ai_with_outliers = sample_data['non_ai_group'] + [200.0, -30.0]

        fig, ax = generate_boxplot(ai_with_outliers, non_ai_with_outliers)

        # The plot should not crash and should render
        assert fig is not None
        assert ax is not None

    def test_save_boxplot_file_format(self, sample_data, temp_output_dir):
        """Test that the saved file is a valid PNG."""
        output_path = os.path.join(temp_output_dir, 'test_output.png')
        save_boxplot(sample_data['ai_group'], sample_data['non_ai_group'], output_path, dpi=300)

        # Check file extension
        assert output_path.endswith('.png'), "Output file should have .png extension"

        # Verify it's a valid image
        from PIL import Image
        try:
            img = Image.open(output_path)
            img.verify()  # Verify it's a valid image
            assert img.format == 'PNG', f"Expected PNG format, got {img.format}"
        except Exception as e:
            pytest.fail(f"Invalid image file: {e}")

    def test_boxplot_consistency(self, sample_data):
        """Test that running generate_boxplot multiple times produces consistent results."""
        fig1, ax1 = generate_boxplot(sample_data['ai_group'], sample_data['non_ai_group'])
        fig2, ax2 = generate_boxplot(sample_data['ai_group'], sample_data['non_ai_group'])

        # Check that the structure is the same
        assert len(ax1.collections) == len(ax2.collections), "Number of boxplot elements should be consistent"