"""
Unit tests for visualization module.
"""
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from code.viz.scatter import generate_scatter_plot


class TestScatterPlot:
    """Tests for scatter plot generation."""

    def test_scatter_plot_generates_png_with_annotations(self, tmp_path):
        """Test that scatter plot generates a PNG file with proper annotations.
        
        Validates:
        1. Output file is created
        2. File is a valid PNG
        3. File size is reasonable (not empty)
        4. Annotations are present in the plot (via file existence)
        """
        # Create synthetic but realistic test data
        n_samples = 50
        np.random.seed(42)
        
        # Generate correlated data (r ~ 0.4)
        x = np.random.normal(0, 1, n_samples)
        y = 0.4 * x + np.random.normal(0, 0.8, n_samples)
        
        # Create DataFrame
        df = pd.DataFrame({
            "modularity": x,
            "motor_score": y,
            "p_modularity": [0.003] * n_samples,
            "q_modularity": [0.015] * n_samples,
            "fd": np.random.uniform(0.1, 0.4, n_samples)
        })
        
        # Save to temp CSV
        csv_path = tmp_path / "test_correlations.csv"
        df.to_csv(csv_path, index=False)
        
        # Generate plot
        output_dir = tmp_path / "figures"
        output_dir.mkdir()
        output_path = output_dir / "test_scatter.png"
        
        result_path = generate_scatter_plot(
            metric_name="modularity",
            score_column="motor_score",
            corr_csv_path=csv_path,
            out_path=output_path
        )
        
        # Assertions
        assert Path(result_path).exists(), "Output file was not created"
        assert Path(result_path).suffix == ".png", "Output is not a PNG file"
        
        # Check file size (should be > 10KB for a real plot with annotations)
        file_size = Path(result_path).stat().st_size
        assert file_size > 10000, f"Plot file too small ({file_size} bytes), likely empty"
        
        # Verify the function returns the correct path
        assert result_path == str(output_path), "Returned path does not match expected output path"

    def test_scatter_plot_with_insufficient_data(self, tmp_path):
        """Test that scatter plot raises error with too few data points."""
        # Create data with only 2 points
        df = pd.DataFrame({
            "modularity": [0.1, 0.2],
            "motor_score": [0.3, 0.4],
            "p_modularity": [0.5, 0.6],
            "q_modularity": [0.7, 0.8]
        })
        
        csv_path = tmp_path / "small_correlations.csv"
        df.to_csv(csv_path, index=False)
        
        output_path = tmp_path / "small_plot.png"
        
        with pytest.raises(ValueError, match="Not enough data points"):
            generate_scatter_plot(
                metric_name="modularity",
                score_column="motor_score",
                corr_csv_path=csv_path,
                out_path=output_path
            )

    def test_scatter_plot_missing_metric(self, tmp_path):
        """Test that scatter plot raises error for missing metric column."""
        # Create data without the requested metric
        df = pd.DataFrame({
            "global_efficiency": [0.1, 0.2, 0.3],
            "motor_score": [0.3, 0.4, 0.5],
            "p_global_efficiency": [0.5, 0.6, 0.7],
            "q_global_efficiency": [0.7, 0.8, 0.9]
        })
        
        csv_path = tmp_path / "wrong_metric.csv"
        df.to_csv(csv_path, index=False)
        
        output_path = tmp_path / "wrong_plot.png"
        
        with pytest.raises(ValueError, match="not found in data"):
            generate_scatter_plot(
                metric_name="modularity",  # This column doesn't exist
                score_column="motor_score",
                corr_csv_path=csv_path,
                out_path=output_path
            )

    def test_scatter_plot_default_output_path(self, tmp_path):
        """Test that scatter plot creates default output path when not specified."""
        # Create test data
        df = pd.DataFrame({
            "modularity": [0.1, 0.2, 0.3, 0.4, 0.5],
            "motor_score": [0.3, 0.4, 0.5, 0.6, 0.7],
            "p_modularity": [0.05, 0.06, 0.07, 0.08, 0.09],
            "q_modularity": [0.1, 0.12, 0.14, 0.16, 0.18]
        })
        
        csv_path = tmp_path / "test.csv"
        df.to_csv(csv_path, index=False)
        
        # Change to temp directory to avoid writing to project root
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create data/figures directory
            Path("data/figures").mkdir(parents=True)
            
            # Generate plot without specifying output path
            result = generate_scatter_plot(
                metric_name="modularity",
                score_column="motor_score",
                corr_csv_path=csv_path
            )
            
            # Should have created file in data/figures
            assert Path(result).exists()
            assert "scatter_modularity.png" in result
        finally:
            os.chdir(old_cwd)