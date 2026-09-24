"""
Unit tests for visualize_results.py functions.
Verifies data loading and grid generation for visualization.
"""
import json
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from visualize_results import load_regression_summary, generate_surface_grid


class TestLoadRegressionSummary:
    """Tests for the load_regression_summary function."""

    def test_load_valid_json(self):
        """Should load valid JSON regression summary."""
        summary = {
            "coefficients": {"density": 0.5, "horizon": 0.3, "interaction": 0.2},
            "p_values": {"density": 0.01, "horizon": 0.02, "interaction": 0.03},
            "hypothesis_supported": True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(summary, f)
            temp_path = f.name

        try:
            result = load_regression_summary(temp_path)
            assert result == summary
        finally:
            os.unlink(temp_path)

    def test_load_missing_file(self):
        """Should raise FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            load_regression_summary("/nonexistent/path/file.json")

    def test_load_invalid_json(self):
        """Should raise JSONDecodeError for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = f.name

        try:
            with self.assertRaises(json.JSONDecodeError):
                load_regression_summary(temp_path)
        finally:
            os.unlink(temp_path)


class TestGenerateSurfaceGrid:
    """Tests for the generate_surface_grid function."""

    def test_grid_dimensions(self):
        """Grid should have correct dimensions."""
        horizon_range = (1, 10)
        density_range = (0.0, 1.0)
        n_horizon = 5
        n_density = 3

        grid = generate_surface_grid(horizon_range, density_range, n_horizon, n_density)
        
        assert len(grid) == n_horizon
        assert all(len(row) == n_density for row in grid)

    def test_grid_values_in_range(self):
        """Grid values should be within specified ranges."""
        horizon_range = (1, 10)
        density_range = (0.0, 1.0)
        n_horizon = 10
        n_density = 10

        grid = generate_surface_grid(horizon_range, density_range, n_horizon, n_density)
        
        for row in grid:
            for (h, d, _) in row:
                assert horizon_range[0] <= h <= horizon_range[1]
                assert density_range[0] <= d <= density_range[1]

    def test_grid_structure(self):
        """Grid should contain tuples of (horizon, density, success_rate)."""
        grid = generate_surface_grid((1, 5), (0.0, 1.0), 3, 3)
        
        for row in grid:
            for item in row:
                assert isinstance(item, tuple)
                assert len(item) == 3
                horizon, density, success_rate = item
                assert isinstance(horizon, (int, float))
                assert isinstance(density, (int, float))
                assert isinstance(success_rate, (int, float))
