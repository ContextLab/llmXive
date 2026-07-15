"""
Unit tests for the viz module.
"""
import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from viz import plot_heatmap, plot_histogram, plot_primary_threshold_visualizations

def test_plot_heatmap_creates_file():
    """Test that plot_heatmap creates a valid PNG file."""
    # Create a random correlation matrix
    n = 5
    data = np.random.rand(n, n)
    corr_matrix = pd.DataFrame(data, columns=[f"var_{i}" for i in range(n)])
    # Make it symmetric
    corr_matrix = (corr_matrix + corr_matrix.T) / 2
    np.fill_diagonal(corr_matrix.values, 1.0)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_heatmap.png")
        plot_heatmap(corr_matrix, "Test Heatmap", output_path)
        
        assert os.path.exists(output_path), "Heatmap file was not created"
        assert os.path.getsize(output_path) > 0, "Heatmap file is empty"


def test_plot_histogram_creates_file():
    """Test that plot_histogram creates a valid PNG file."""
    null_dist = np.random.randn(1000).tolist()
    observed_val = 0.5

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_histogram.png")
        plot_histogram(null_dist, observed_val, "Test Histogram", output_path)
        
        assert os.path.exists(output_path), "Histogram file was not created"
        assert os.path.getsize(output_path) > 0, "Histogram file is empty"


def test_plot_primary_threshold_visualizations():
    """Test that plot_primary_threshold_visualizations creates both heatmap and histogram."""
    n = 5
    data = np.random.rand(n, n)
    corr_matrix = pd.DataFrame(data, columns=[f"var_{i}" for i in range(n)])
    corr_matrix = (corr_matrix + corr_matrix.T) / 2
    np.fill_diagonal(corr_matrix.values, 1.0)

    null_stats = np.random.randn(1000).tolist()
    observed_stat = 0.35
    dataset_id = "test_ds"

    with tempfile.TemporaryDirectory() as tmpdir:
        result = plot_primary_threshold_visualizations(
            corr_matrix=corr_matrix,
            null_stats=null_stats,
            observed_stat=observed_stat,
            dataset_id=dataset_id,
            output_dir=tmpdir
        )

        assert "heatmap" in result, "Heatmap path not in result"
        assert "histogram" in result, "Histogram path not in result"
        
        assert os.path.exists(result["heatmap"]), f"Heatmap file not found: {result['heatmap']}"
        assert os.path.exists(result["histogram"]), f"Histogram file not found: {result['histogram']}"
        
        assert os.path.getsize(result["heatmap"]) > 0, "Heatmap file is empty"
        assert os.path.getsize(result["histogram"]) > 0, "Histogram file is empty"


def test_plot_heatmap_raises_on_non_square():
    """Test that plot_heatmap raises ValueError for non-square matrix."""
    data = np.random.rand(3, 4)
    corr_matrix = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "fail.png")
        with pytest.raises(ValueError):
            plot_heatmap(corr_matrix, "Fail", output_path)


def test_plot_histogram_raises_on_empty():
    """Test that plot_histogram raises ValueError for empty null_dist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "fail.png")
        with pytest.raises(ValueError):
            plot_histogram([], 0.5, "Fail", output_path)