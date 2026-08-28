import os
import tempfile
import numpy as np
import pytest
from pathlib import Path
import statsmodels.api as sm

# Import the functions to test
from viz.plots import (
    plot_flexibility_vs_creativity,
    plot_residuals,
    compress_image,
    OUTPUT_DIR
)

def test_plot_functions_exist():
    """
    Contract test asserting that the required plot functions exist and are callable.
    """
    assert callable(plot_flexibility_vs_creativity)
    assert callable(plot_residuals)
    assert callable(compress_image)

def test_plot_flexibility_vs_creativity_saves_file():
    """
    Test that plot_flexibility_vs_creativity creates the expected output file.
    """
    # Generate synthetic data for testing
    np.random.seed(42)
    flexibility = np.random.normal(0.5, 0.1, 100)
    creativity = 2 * flexibility + np.random.normal(0, 0.1, 100)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_flex_vs_creat.png")
        
        plot_flexibility_vs_creativity(flexibility, creativity, output_path=output_path)
        
        assert os.path.exists(output_path), f"Output file {output_path} was not created."
        assert os.path.getsize(output_path) > 0, f"Output file {output_path} is empty."

def test_plot_residuals_saves_files():
    """
    Test that plot_residuals creates the expected output files.
    """
    # Generate synthetic data and fit a model
    np.random.seed(42)
    X = np.random.normal(0, 1, 100)
    y = 2 * X + np.random.normal(0, 0.5, 100)
    X_with_const = sm.add_constant(X)
    model = sm.OLS(y, X_with_const).fit()

    with tempfile.TemporaryDirectory() as tmpdir:
        residuals_path = os.path.join(tmpdir, "test_residuals.png")
        qq_path = os.path.join(tmpdir, "test_qq.png")
        
        plot_residuals(model, residuals_path=residuals_path, qq_path=qq_path)
        
        assert os.path.exists(residuals_path), f"Residuals file {residuals_path} was not created."
        assert os.path.exists(qq_path), f"QQ file {qq_path} was not created."
        assert os.path.getsize(residuals_path) > 0, f"Residuals file {residuals_path} is empty."
        assert os.path.getsize(qq_path) > 0, f"QQ file {qq_path} is empty."

def test_compress_image():
    """
    Test that compress_image handles existing and non-existing files gracefully.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test with non-existing file (should warn but not raise)
        non_existing = os.path.join(tmpdir, "non_existing.png")
        compress_image(non_existing, max_mb=5.0)  # Should not raise

        # Test with existing file (create a dummy small file)
        dummy_path = os.path.join(tmpdir, "dummy.png")
        Path(dummy_path).touch()
        compress_image(dummy_path, max_mb=5.0)  # Should not raise
