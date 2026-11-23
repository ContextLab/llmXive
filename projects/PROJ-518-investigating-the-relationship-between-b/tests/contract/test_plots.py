import pytest
import os
import tempfile
import numpy as np
from unittest.mock import Mock

# Import the function under test
from viz.plots import plot_residuals, plot_flexibility_vs_creativity

class TestPlotFunctionsExist:
    """Contract tests to ensure plot functions exist and have correct signatures."""

    def test_plot_residuals_exists(self):
        """Assert that plot_residuals function exists."""
        assert callable(plot_residuals)

    def test_plot_flexibility_vs_creativity_exists(self):
        """Assert that plot_flexibility_vs_creativity function exists."""
        assert callable(plot_flexibility_vs_creativity)

    def test_plot_residuals_signature(self):
        """Assert that plot_residuals has the expected signature."""
        import inspect
        sig = inspect.signature(plot_residuals)
        params = list(sig.parameters.keys())
        assert 'model' in params
        assert 'residuals_path' in params
        assert 'qq_path' in params

    def test_plot_residuals_creates_files(self):
        """Test that plot_residuals creates the expected output files."""
        # Create a mock RegressionResult
        mock_model = Mock()
        mock_model.fitted_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mock_model.residuals = np.array([0.1, -0.2, 0.3, -0.1, 0.2])

        with tempfile.TemporaryDirectory() as tmpdir:
            residuals_path = os.path.join(tmpdir, 'model_residuals.png')
            qq_path = os.path.join(tmpdir, 'model_qq.png')

            # Call the function
            plot_residuals(mock_model, residuals_path, qq_path)

            # Assert files were created
            assert os.path.exists(residuals_path), f"Residuals plot not created at {residuals_path}"
            assert os.path.exists(qq_path), f"QQ plot not created at {qq_path}"

            # Assert files are not empty
            assert os.path.getsize(residuals_path) > 0
            assert os.path.getsize(qq_path) > 0

    def test_plot_flexibility_vs_creativity_creates_file(self):
        """Test that plot_flexibility_vs_creativity creates the expected output file."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_scatter.png')
            plot_flexibility_vs_creativity(x, y, output_path)

            assert os.path.exists(output_path), f"Scatter plot not created at {output_path}"
            assert os.path.getsize(output_path) > 0