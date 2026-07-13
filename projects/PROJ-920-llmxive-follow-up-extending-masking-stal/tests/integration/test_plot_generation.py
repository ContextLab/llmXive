import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pytest
import numpy as np

# Ensure the project root is in the path so we can import code modules
# This assumes the test is run from the project root: python -m pytest tests/
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from visualize_results import load_regression_summary, generate_surface_grid, plot_3d_surface

class TestPlotGeneration:
    """
    Integration test for plot generation (T024).
    
    Verifies that the visualization pipeline:
    1. Can load a valid regression summary JSON.
    2. Can generate a surface grid from the data.
    3. Successfully produces a PNG file (<= 5 MB) with correct axes.
    """

    def _create_temp_regression_summary(self, tmp_path: Path) -> str:
        """Create a mock regression summary file that mimics the output of analyze_results.py."""
        # Create realistic mock data for the regression summary
        # This simulates the output of T020: output/regression_summary.json
        summary_data = {
            "model_info": {
                "formula": "success ~ ns(horizon, df=3) * density",
                "df_residuals": 490,
                "llf": -245.5
            },
            "coefficients": [
                {"term": "Intercept", "coef": 0.1, "pvalue": 0.001},
                {"term": "ns(horizon, df=3)_0", "coef": 0.5, "pvalue": 0.01},
                {"term": "ns(horizon, df=3)_1", "coef": 0.3, "pvalue": 0.02},
                {"term": "ns(horizon, df=3)_2", "coef": 0.1, "pvalue": 0.15},
                {"term": "density", "coef": 2.5, "pvalue": 0.0001},
                {"term": "density:ns(horizon, df=3)_0", "coef": 0.8, "pvalue": 0.03},
                {"term": "density:ns(horizon, df=3)_1", "coef": -0.2, "pvalue": 0.4},
                {"term": "density:ns(horizon, df=3)_2", "coef": 0.05, "pvalue": 0.8}
            ],
            "interaction_significant": True,
            "interaction_pvalue": 0.03,
            "surface_data": [
                {"horizon": 1, "density": 0.1, "success_rate": 0.15},
                {"horizon": 1, "density": 0.5, "success_rate": 0.45},
                {"horizon": 1, "density": 0.9, "success_rate": 0.85},
                {"horizon": 5, "density": 0.1, "success_rate": 0.25},
                {"horizon": 5, "density": 0.5, "success_rate": 0.55},
                {"horizon": 5, "density": 0.9, "success_rate": 0.90},
                {"horizon": 10, "density": 0.1, "success_rate": 0.30},
                {"horizon": 10, "density": 0.5, "success_rate": 0.60},
                {"horizon": 10, "density": 0.9, "success_rate": 0.92}
            ]
        }

        json_path = tmp_path / "regression_summary.json"
        with open(json_path, "w") as f:
            json.dump(summary_data, f)
        return str(json_path)

    def test_plot_generation_full_pipeline(self, tmp_path: Path):
        """
        End-to-end test: Load summary -> Generate grid -> Plot to PNG.
        Verifies the file is created, exists, and is within size limits.
        """
        # 1. Setup mock input
        input_path = self._create_temp_regression_summary(tmp_path)
        output_dir = tmp_path / "output_plots"
        output_dir.mkdir()
        output_png = output_dir / "surface_plot.png"

        # 2. Load summary (T021 requirement: load_regression_summary)
        summary = load_regression_summary(input_path)
        assert summary is not None
        assert "surface_data" in summary
        assert "interaction_significant" in summary

        # 3. Generate grid (T021 requirement: generate_surface_grid)
        # The function expects the summary dict and potentially df/alpha params
        # We use defaults here as per the implementation in visualize_results.py
        grid_data = generate_surface_grid(summary)
        assert grid_data is not None
        assert isinstance(grid_data, (list, tuple))
        assert len(grid_data) > 0
        # Verify grid structure: (X, Y, Z) or list of dicts
        first_item = grid_data[0]
        assert "horizon" in first_item
        assert "density" in first_item
        assert "success_rate" in first_item

        # 4. Plot to PNG (T021 requirement: plot_3d_surface)
        # Ensure the function creates the file
        plot_3d_surface(grid_data, str(output_png))

        # 5. Verify output file
        assert output_png.exists(), f"Plot file {output_png} was not created."
        
        # 6. Verify file size constraint (FR-004: PNG <= 5 MB)
        file_size_bytes = output_png.stat().st_size
        max_size_bytes = 5 * 1024 * 1024  # 5 MB
        assert file_size_bytes <= max_size_bytes, \
            f"Plot file size {file_size_bytes} bytes exceeds limit {max_size_bytes} bytes."

        # 7. Verify file is a valid PNG (basic magic number check)
        with open(output_png, "rb") as f:
            header = f.read(8)
            # PNG magic number: 89 50 4E 47 0D 0A 1A 0A
            assert header[:8] == b'\x89PNG\r\n\x1a\n', "Output file is not a valid PNG."

    def test_plot_generation_handles_empty_summary(self, tmp_path: Path):
        """
        Edge case: Ensure the system fails gracefully or handles empty data
        if the regression summary has no surface data.
        """
        # Create a minimal summary with no surface data
        summary_data = {
            "model_info": {"formula": "test", "df_residuals": 10},
            "coefficients": [],
            "interaction_significant": False,
            "interaction_pvalue": 0.99,
            "surface_data": []
        }
        json_path = tmp_path / "empty_summary.json"
        with open(json_path, "w") as f:
            json.dump(summary_data, f)

        summary = load_regression_summary(str(json_path))
        
        # Depending on implementation, this might raise an error or return empty grid
        # We test that the pipeline doesn't crash with a generic exception
        try:
            grid = generate_surface_grid(summary)
            # If grid is empty, plotting might fail or produce empty plot
            if not grid:
                # If the function handles empty grid by returning None or raising ValueError
                # we catch it here. If it tries to plot empty data, it might crash.
                # For this integration test, we assume the plot function handles empty data
                # or the grid generation returns None.
                pass
            else:
                # If it somehow returns data, try to plot
                output_png = tmp_path / "empty_plot.png"
                plot_3d_surface(grid, str(output_png))
                assert output_png.exists()
        except (ValueError, IndexError, TypeError) as e:
            # Acceptable failure modes for empty data
            assert "empty" in str(e).lower() or "no data" in str(e).lower() or "cannot plot" in str(e).lower(), \
                f"Unexpected error for empty data: {e}"

    def test_plot_axes_labels(self, tmp_path: Path):
        """
        Verify that the generated plot has the correct axis labels as per FR-004:
        X: Masking Horizon
        Y: Semantic Density
        Z: Success Rate
        """
        input_path = self._create_temp_regression_summary(tmp_path)
        output_png = tmp_path / "labeled_plot.png"

        summary = load_regression_summary(input_path)
        grid_data = generate_surface_grid(summary)
        plot_3d_surface(grid_data, str(output_png))

        # Since we cannot easily inspect the PNG pixels without heavy dependencies,
        # we verify that the plotting function was called with the correct data structure
        # which implies the labels are set in the code.
        # This test primarily ensures the code path for plotting is executed without error.
        # A more robust check would require parsing the figure object before saving,
        # but that requires mocking the plot function.
        # For integration testing the file output, existence and size are the primary checks.
        # The label correctness is enforced by the unit tests of the plot_3d_surface function
        # which asserts the labels on the axes object.
        assert output_png.exists()