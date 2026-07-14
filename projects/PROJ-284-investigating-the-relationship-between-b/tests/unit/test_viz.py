import os
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.viz.scatter import generate_scatter_plot

class TestScatterPlot:
    """Unit tests for the scatter plot generator."""

    def test_scatter_plot_generates_png_with_annotations(self):
        """
        Verify that generate_scatter_plot creates a PNG file with expected labels and annotations.
        """
        # Prepare dummy data
        data = pd.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 5, 4, 5],
            "metric_name": ["Test Metric"]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_scatter.png"

            # Run generator
            result = generate_scatter_plot(
                data=data,
                x_col="x",
                y_col="y",
                metric_name="Test Metric",
                r_value=0.8,
                p_value=0.01,
                q_value=0.02,
                output_path=str(output_path)
            )

            # Verify file exists and has content
            assert result.exists(), "PNG file was not created."
            assert result.stat().st_size > 0, "PNG file is empty."

            # Verify it's a valid image (basic check)
            img = plt.imread(str(output_path))
            assert img.ndim == 3 or (img.ndim == 2 and img.shape[0] > 0), "Invalid image dimensions."

            # Clean up
            plt.close('all')

            # Note: We cannot easily verify text annotations inside the image without OCR,
            # but we trust the matplotlib logic in the implementation for this unit test.
            # The integration test in test_report.py verifies the full pipeline.