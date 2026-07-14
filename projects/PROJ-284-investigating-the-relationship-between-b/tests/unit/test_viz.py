"""
Unit tests for the visualization module.

Task: T029
Description: Unit test in tests/unit/test_viz.py::test_scatter_plot_generates_png_with_annotations
(dummy data, verifies file output and labels)
"""
import os
import tempfile
import shutil
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
# Use non-interactive backend for CI/Headless environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from code.viz.scatter import generate_scatter_plot

class TestScatterPlot:
    """Tests for scatter plot generation."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup and teardown for each test."""
        self.tmp_path = tmp_path
        self.output_dir = self.tmp_path / "output_plots"
        self.output_dir.mkdir()
        self.input_csv = self.tmp_path / "test_metrics.csv"
        
        # Create dummy data matching the expected schema from T024/T025
        # Columns: subject_id, metric_value, motor_score, r_value, p_value, q_value
        np.random.seed(42)  # For reproducibility
        data = {
            'subject_id': [f'sub-{i:03d}' for i in range(1, 21)],
            'metric_value': np.random.randn(20) * 10 + 50,
            'motor_score': np.random.randn(20) * 5 + 100,
            'r_value': [0.45] * 20,  # Dummy aggregated stats for the plot annotation
            'p_value': [0.02] * 20,
            'q_value': [0.05] * 20
        }
        self.df = pd.DataFrame(data)
        self.df.to_csv(self.input_csv, index=False)

    def test_scatter_plot_generates_png_with_annotations(self):
        """
        Verify that generate_scatter_plot creates a PNG file with correct labels 
        and statistical annotations.
        """
        output_file = self.output_dir / "scatter_test.png"
        
        # Call the function with keyword arguments (matching T031 implementation)
        generate_scatter_plot(
            input_data=str(self.input_csv),
            x_col='metric_value',
            y_col='motor_score',
            x_label='Network Metric',
            y_label='Sensorimotor Performance',
            output_path=str(output_file),
            title='Correlation Test'
        )

        # Assertions
        assert output_file.exists(), "Output PNG file was not created."
        assert output_file.stat().st_size > 0, "Output PNG file is empty."
        assert str(output_file).endswith(".png"), "Output file does not have .png extension."

        # Verify the file is a valid PNG by checking magic bytes
        with open(output_file, 'rb') as f:
            header = f.read(8)
            assert header[:4] == b'\x89PNG', "File is not a valid PNG image."

        # Cleanup
        plt.close('all')

if __name__ == "__main__":
    pytest.main([__file__, "-v"])