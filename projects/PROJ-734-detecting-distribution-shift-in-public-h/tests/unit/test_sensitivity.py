"""
Unit tests for sensitivity analysis grid generation (User Story 3).

Tests the logic for generating parameter grids for bandwidth and window size,
and tolerance sweeps, as implemented in code/sensitivity.py.
"""
import pytest
import numpy as np
from typing import List, Dict, Any, Tuple
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sensitivity import generate_grid_parameters, generate_tolerance_grid


class TestGridGeneration:
    """Tests for sensitivity grid generation functions."""

    def test_generate_grid_parameters_basic(self):
        """Test basic grid generation with explicit lists."""
        # Define test parameters
        bandwidths = [1.0, 2.0, 3.0]
        windows = [8, 12, 16]
        
        # Generate grid
        grid = generate_grid_parameters(bandwidths, windows)
        
        # Verify grid structure
        assert isinstance(grid, list)
        assert len(grid) == len(bandwidths) * len(windows)
        
        # Verify all combinations exist
        combinations = set()
        for item in grid:
            assert isinstance(item, dict)
            assert 'bandwidth' in item
            assert 'window_size' in item
            combinations.add((item['bandwidth'], item['window_size']))
        
        expected_combinations = set((bw, win) for bw in bandwidths for win in windows)
        assert combinations == expected_combinations

    def test_generate_grid_parameters_with_median_cv(self):
        """Test grid generation using 'median' and 'cv' special values."""
        # In a real scenario, these would be computed from data.
        # Here we test that the function accepts them as values.
        bandwidths = ['median', 'cv', 5.0]
        windows = [10, 15]
        
        grid = generate_grid_parameters(bandwidths, windows)
        
        assert len(grid) == len(bandwidths) * len(windows)
        
        # Verify 'median' and 'cv' are present in the grid
        bw_values = [item['bandwidth'] for item in grid]
        assert 'median' in bw_values
        assert 'cv' in bw_values
        assert 5.0 in bw_values

    def test_generate_grid_parameters_empty_lists(self):
        """Test behavior with empty input lists."""
        with pytest.raises(ValueError):
            generate_grid_parameters([], [1, 2])
        
        with pytest.raises(ValueError):
            generate_grid_parameters([1, 2], [])

    def test_generate_grid_parameters_single_values(self):
        """Test grid generation with single values."""
        grid = generate_grid_parameters([2.0], [12])
        
        assert len(grid) == 1
        assert grid[0]['bandwidth'] == 2.0
        assert grid[0]['window_size'] == 12

    def test_generate_tolerance_grid_basic(self):
        """Test tolerance grid generation."""
        tolerances = [1, 2, 3]
        
        grid = generate_tolerance_grid(tolerances)
        
        assert isinstance(grid, list)
        assert len(grid) == len(tolerances)
        
        # Verify structure
        for item in grid:
            assert isinstance(item, dict)
            assert 'tolerance' in item
            assert 'label' in item
        
        # Verify values
        tolerance_values = [item['tolerance'] for item in grid]
        assert set(tolerance_values) == set(tolerances)

    def test_generate_tolerance_grid_with_labels(self):
        """Test that labels are generated correctly."""
        tolerances = [1, 2]
        
        grid = generate_tolerance_grid(tolerances)
        
        # Check that labels follow expected pattern
        labels = [item['label'] for item in grid]
        assert f"tol_{tolerances[0]}" in labels
        assert f"tol_{tolerances[1]}" in labels

    def test_generate_tolerance_grid_empty(self):
        """Test tolerance grid generation with empty list."""
        with pytest.raises(ValueError):
            generate_tolerance_grid([])

    def test_grid_parameter_types(self):
        """Test that grid parameters maintain correct types."""
        bandwidths = [1.5, 2.5]
        windows = [8, 12]
        
        grid = generate_grid_parameters(bandwidths, windows)
        
        for item in grid:
            # Bandwidth should be float
            assert isinstance(item['bandwidth'], (int, float))
            # Window size should be int
            assert isinstance(item['window_size'], int)

    def test_grid_determinism(self):
        """Test that grid generation is deterministic."""
        bandwidths = [1.0, 2.0, 3.0]
        windows = [8, 12, 16]
        
        grid1 = generate_grid_parameters(bandwidths, windows)
        grid2 = generate_grid_parameters(bandwidths, windows)
        
        assert grid1 == grid2

    def test_grid_ordering(self):
        """Test that grid is generated in expected order (outer loop: bandwidth)."""
        bandwidths = [1.0, 2.0]
        windows = [8, 12]
        
        grid = generate_grid_parameters(bandwidths, windows)
        
        # Expected order: (1.0, 8), (1.0, 12), (2.0, 8), (2.0, 12)
        expected = [
            {'bandwidth': 1.0, 'window_size': 8},
            {'bandwidth': 1.0, 'window_size': 12},
            {'bandwidth': 2.0, 'window_size': 8},
            {'bandwidth': 2.0, 'window_size': 12}
        ]
        
        assert grid == expected

    def test_generate_combined_grid(self):
        """Test generating a combined grid of parameters and tolerances."""
        # This tests the logical combination of two grids
        param_grid = generate_grid_parameters([1.0, 2.0], [8, 12])
        tol_grid = generate_tolerance_grid([1, 2])
        
        # Simulate combining them (as would be done in sensitivity.py)
        combined = []
        for p in param_grid:
            for t in tol_grid:
                entry = p.copy()
                entry['tolerance'] = t['tolerance']
                entry['tolerance_label'] = t['label']
                combined.append(entry)
        
        expected_size = len(param_grid) * len(tol_grid)
        assert len(combined) == expected_size
        
        # Verify all combinations exist
        for item in combined:
            assert 'bandwidth' in item
            assert 'window_size' in item
            assert 'tolerance' in item
            assert 'tolerance_label' in item