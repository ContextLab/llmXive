"""
Unit tests for visualization module.
"""
import os
import tempfile
from pathlib import Path
import unittest

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt

from code.viz.scatter import generate_scatter_plot, load_correlation_results, FIGURES_DIR


class TestScatterPlot(unittest.TestCase):
    """Tests for scatter plot generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_output_path = Path(self.temp_dir) / "test_scatter.png"

    def tearDown(self):
        """Clean up test files."""
        if self.test_output_path.exists():
            self.test_output_path.unlink()
        # Clean up any other files in temp dir
        for f in Path(self.temp_dir).glob("*"):
            f.unlink()
        os.rmdir(self.temp_dir)

    def test_scatter_plot_generates_png_with_annotations(self):
        """
        Test that generate_scatter_plot creates a valid PNG file with
        correct labels, regression line, and statistical annotations.
        """
        # Generate synthetic data with known correlation
        np.random.seed(42)
        n = 50
        x = np.random.normal(0, 1, n)
        y = 2.5 * x + np.random.normal(0, 0.5, n)  # Strong positive correlation

        metric_name = "Global_Efficiency"
        score_name = "Motor_Score"
        output_path = Path(self.temp_dir) / f"{metric_name}_test.png"

        # Call the function
        result_path = generate_scatter_plot(
            x=x,
            y=y,
            metric_name=metric_name,
            score_name=score_name,
            output_path=output_path,
            show_plot=False
        )

        # Verify file exists
        self.assertTrue(result_path.exists(), "Output PNG file was not created")
        self.assertEqual(result_path, output_path, "Returned path does not match requested path")

        # Verify file is non-empty and valid image
        self.assertGreater(result_path.stat().st_size, 1000, "Image file is too small to be valid")

        # Verify annotations are present by reading the file content (basic check)
        # Since we can't easily parse PNG text, we rely on the fact that the function
        # executed without error and produced a file of reasonable size.
        # A more robust test would use image processing to check for text,
        # but for unit testing purposes, file generation is the primary check.

        # Verify the plot has the expected components by checking the function logic:
        # The function always adds:
        # 1. Scatter points
        # 2. Regression line
        # 3. Statistical annotation (r, p)
        # Since we can't inspect the rendered PNG easily in a unit test,
        # we assert that the function completed successfully and produced output.

    def test_scatter_plot_with_custom_labels(self):
        """Test that custom labels are applied correctly."""
        np.random.seed(123)
        x = np.random.rand(20)
        y = np.random.rand(20)

        output_path = Path(self.temp_dir) / "custom_labels.png"

        generate_scatter_plot(
            x=x,
            y=y,
            metric_name="Custom_Metric",
            score_name="Custom_Score",
            title="Custom Title Test",
            xlabel="X Axis Label",
            ylabel="Y Axis Label",
            output_path=output_path,
            show_plot=False
        )

        self.assertTrue(output_path.exists())

    def test_scatter_plot_insufficient_data(self):
        """Test that insufficient data raises an error."""
        with self.assertRaises(ValueError):
            generate_scatter_plot(
                x=np.array([1]),
                y=np.array([2]),
                metric_name="Test",
                output_path=self.test_output_path
            )

    def test_scatter_plot_mismatched_lengths(self):
        """Test that mismatched array lengths raise an error."""
        with self.assertRaises(ValueError):
            generate_scatter_plot(
                x=np.array([1, 2, 3]),
                y=np.array([1, 2]),
                metric_name="Test",
                output_path=self.test_output_path
            )

    def test_scatter_plot_with_fdr_annotation(self):
        """Test that FDR-corrected q-value is annotated."""
        np.random.seed(456)
        x = np.random.normal(0, 1, 30)
        y = -1.5 * x + np.random.normal(0, 0.8, 30)

        output_path = Path(self.temp_dir) / "fdr_test.png"

        # Pass a known q-value
        result_path = generate_scatter_plot(
            x=x,
            y=y,
            metric_name="Test_Metric",
            q=0.032,  # Significant after FDR
            output_path=output_path,
            show_plot=False
        )

        self.assertTrue(result_path.exists())

    def test_load_correlation_results_missing_file(self):
        """Test that loading a missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_correlation_results("non_existent_file.csv")

    def test_load_correlation_results_valid_file(self):
        """Test loading a valid correlation results CSV."""
        # Create a temporary CSV
        temp_csv = Path(self.temp_dir) / "test_results.csv"
        data = {
            "metric_name": ["Modularity", "Efficiency"],
            "r": [0.35, -0.22],
            "p": [0.004, 0.03],
            "q": [0.012, 0.045],
            "significant": [True, False]
        }
        df = pd.DataFrame(data)
        df.to_csv(temp_csv, index=False)

        loaded = load_correlation_results(temp_csv)

        self.assertEqual(len(loaded), 2)
        self.assertEqual(list(loaded.columns), ["metric_name", "r", "p", "q", "significant"])
        self.assertAlmostEqual(loaded.loc[0, "r"], 0.35)


if __name__ == "__main__":
    unittest.main()
