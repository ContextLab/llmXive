"""
Unit tests for visualization module (T022).
"""
import os
import sys
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from visualizations import plot_correlation_heatmap, plot_variogram
from utils.logging import get_logger

logger = get_logger(__name__)


def test_plot_correlation_heatmap():
    """Test that correlation heatmap is generated and saved."""
    # Create dummy correlation data
    np.random.seed(42)
    data = np.random.rand(100, 4)
    df = pd.DataFrame(data, columns=['temp', 'building', 'tree', 'road'])
    corr_matrix = df.corr()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_corr.png"
        result_path = plot_correlation_heatmap(corr_matrix, output_path=output_path)

        assert result_path.exists(), f"Output file not created at {result_path}"
        assert result_path.stat().st_size > 0, "Output file is empty"


def test_plot_variogram_with_data():
    """Test that variogram plot is generated with valid data."""
    variogram_data = {
        'distances': np.linspace(10, 1000, 20),
        'semivariances': np.linspace(0.1, 2.5, 20)
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_variogram.png"
        result_path = plot_variogram(variogram_data, output_path=output_path)

        assert result_path.exists(), f"Output file not created at {result_path}"
        assert result_path.stat().st_size > 0, "Output file is empty"


def test_plot_variogram_empty_data():
    """Test that variogram plot handles empty data gracefully."""
    variogram_data = {
        'distances': [],
        'semivariances': []
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_variogram_empty.png"
        result_path = plot_variogram(variogram_data, output_path=output_path)

        assert result_path.exists(), f"Output file not created at {result_path}"
        # Should still create a placeholder or empty plot
        assert result_path.stat().st_size > 0, "Output file is empty"
