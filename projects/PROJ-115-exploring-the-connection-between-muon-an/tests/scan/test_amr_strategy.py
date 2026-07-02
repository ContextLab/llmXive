"""
Tests for the Adaptive Mesh Refinement (AMR) Strategy.

Verifies that the grid generator correctly identifies high-sensitivity regions
and refines them, while maintaining the base grid elsewhere.
"""
import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.scan.amr_strategy import AdaptiveGridGenerator, AMRConfig, GridPoint

class TestAMRStrategy:
    """Test suite for AdaptiveGridGenerator."""

    def test_initial_grid_generation(self):
        """Test that the initial coarse grid is generated correctly."""
        config = AMRConfig(
            initial_steps_chi=5,
            initial_steps_V=5,
            initial_steps_g=2,
            max_refinement_depth=0 # No refinement for this test
        )
        generator = AdaptiveGridGenerator(config)
        
        grid = generator.generate_initial_grid(
            m_chi_range=(10.0, 20.0),
            m_V_range=(20.0, 40.0),
            g_range=(1e-3, 1e-2)
        )
        
        expected_points = 5 * 5 * 2
        assert len(grid) == expected_points, f"Expected {expected_points} points, got {len(grid)}"
        
        # Verify ranges
        assert min(p.m_chi for p in grid) == 10.0
        assert max(p.m_chi for p in grid) == 20.0
        assert min(p.m_V for p in grid) == 20.0
        assert max(p.m_V for p in grid) == 40.0

    def test_refinement_trigger_on_sensitivity(self):
        """Test that refinement is triggered when sensitivity threshold is exceeded."""
        # Config with very low threshold to force refinement
        config = AMRConfig(
            initial_steps_chi=3,
            initial_steps_V=3,
            initial_steps_g=2,
            max_refinement_depth=2,
            sensitivity_threshold=0.001 # Extremely low to trigger
        )
        generator = AdaptiveGridGenerator(config)
        
        # Run strategy
        grid = generator.run_convergence_strategy(
            m_chi_range=(10.0, 20.0),
            m_V_range=(20.0, 40.0),
            g_range=(1e-3, 1e-2)
        )
        
        # The grid should have more points than the initial coarse grid due to refinement
        initial_expected = 3 * 3 * 2
        assert len(grid) > initial_expected, "Refinement did not increase grid size"

    def test_max_refinement_depth_enforced(self):
        """Test that points do not exceed the maximum refinement depth."""
        config = AMRConfig(
            initial_steps_chi=2,
            initial_steps_V=2,
            initial_steps_g=2,
            max_refinement_depth=1, # Strict limit
            sensitivity_threshold=0.0001
        )
        generator = AdaptiveGridGenerator(config)
        
        grid = generator.run_convergence_strategy(
            m_chi_range=(10.0, 20.0),
            m_V_range=(20.0, 40.0),
            g_range=(1e-3, 1e-2)
        )
        
        for p in grid:
            assert p.refinement_level <= config.max_refinement_depth, \
                f"Point refinement level {p.refinement_level} exceeds max {config.max_refinement_depth}"

    def test_min_cell_size_constraint(self):
        """Test that refinement stops when cell size becomes too small."""
        config = AMRConfig(
            initial_steps_chi=2,
            initial_steps_V=2,
            initial_steps_g=2,
            max_refinement_depth=10, # High depth allowed
            sensitivity_threshold=0.0001,
            min_cell_size_chi=1.0, # Large minimum size to stop refinement quickly
            min_cell_size_V=1.0,
            min_cell_size_g=0.001
        )
        generator = AdaptiveGridGenerator(config)
        
        grid = generator.run_convergence_strategy(
            m_chi_range=(10.0, 20.0), # Range is 10, min size 1.0 -> max 10 splits theoretically
            m_V_range=(20.0, 40.0),
            g_range=(1e-3, 1e-2)
        )
        
        # Verify that we didn't refine infinitely (which would crash or take forever)
        # The grid size should be finite and reasonable
        assert len(grid) < 10000, "Refinement did not stop at min cell size"

    def test_statistics_calculation(self):
        """Test that grid statistics are calculated correctly."""
        config = AMRConfig(
            initial_steps_chi=5,
            initial_steps_V=5,
            initial_steps_g=2,
            max_refinement_depth=1
        )
        generator = AdaptiveGridGenerator(config)
        
        grid = generator.run_convergence_strategy(
            m_chi_range=(10.0, 20.0),
            m_V_range=(20.0, 40.0),
            g_range=(1e-3, 1e-2)
        )
        
        stats = generator.get_grid_statistics(grid)
        
        assert stats["total_points"] == len(grid)
        assert "max_refinement_level" in stats
        assert "avg_refinement_level" in stats
        assert "chi_range" in stats
        assert "V_range" in stats
        assert "g_range" in stats
        
        # Verify ranges match input
        assert stats["chi_range"] == (10.0, 20.0)
        assert stats["V_range"] == (20.0, 40.0)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])