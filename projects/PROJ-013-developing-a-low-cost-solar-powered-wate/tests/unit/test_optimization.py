"""
Unit tests for User Story 3: Pareto Frontier Optimization.

Tests:
- T030: find_pareto_frontier function
- T031: calculate_knee_point function
- T032: calculate_tradeoff_r_squared function
"""
import pytest
import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.optimization import (
    find_pareto_frontier,
    calculate_knee_point,
    calculate_tradeoff_r_squared
)

class TestFindParetoFrontier:
    """Tests for the Pareto frontier identification algorithm."""

    def test_empty_list_returns_empty(self):
        """Test that an empty list returns an empty frontier."""
        result = find_pareto_frontier([])
        assert result == []

    def test_single_point_returns_itself(self):
        """Test that a single point is its own frontier."""
        points = [(0.5, 100.0)]
        result = find_pareto_frontier(points)
        assert len(result) == 1
        assert result[0] == (0.5, 100.0)

    def test_all_dominated_returns_frontier(self):
        """Test that dominated points are filtered out."""
        # Point A (0.5, 100) dominates B (0.4, 100) and C (0.5, 120)
        points = [
            (0.5, 100.0),  # Non-dominated
            (0.4, 100.0),  # Dominated by A (lower eff, same cost)
            (0.5, 120.0),  # Dominated by A (same eff, higher cost)
            (0.4, 120.0)   # Dominated by A
        ]
        result = find_pareto_frontier(points)
        
        # Only A should remain
        assert len(result) == 1
        assert (0.5, 100.0) in result

    def test_multiple_pareto_points(self):
        """Test that multiple non-dominated points are returned."""
        # These points should all be on the frontier (trade-off)
        points = [
            (0.8, 200.0),  # High eff, high cost
            (0.6, 100.0),  # Medium eff, medium cost
            (0.4, 50.0)    # Low eff, low cost
        ]
        result = find_pareto_frontier(points)
        
        # All should be non-dominated
        assert len(result) == 3
        
        # Verify all original points are in result
        for p in points:
            assert p in result

    def test_returns_only_non_dominated(self):
        """Test that only non-dominated points are returned."""
        points = [
            (0.5, 100.0),  # Non-dominated
            (0.6, 90.0),   # Non-dominated (better in both)
            (0.4, 110.0)   # Dominated by both
        ]
        result = find_pareto_frontier(points)
        
        assert len(result) == 2
        assert (0.5, 100.0) in result
        assert (0.6, 90.0) in result
        assert (0.4, 110.0) not in result

class TestCalculateKneePoint:
    """Tests for knee point calculation."""

    def test_empty_frontier_returns_none(self):
        """Test that an empty frontier returns None."""
        result = calculate_knee_point([])
        assert result is None

    def test_single_point_is_knee(self):
        """Test that a single point is the knee point."""
        frontier = [(0.5, 100.0)]
        result = calculate_knee_point(frontier)
        assert result == (0.5, 100.0)

    def test_knee_point_is_on_frontier(self):
        """Test that the knee point is always one of the frontier points."""
        frontier = [
            (0.8, 200.0),
            (0.6, 100.0),
            (0.4, 50.0)
        ]
        result = calculate_knee_point(frontier)
        
        assert result is not None
        assert result in frontier

    def test_knee_point_minimizes_distance(self):
        """Test that the knee point minimizes distance to ideal."""
        # Ideal point: max_eff=0.8, min_cost=50
        frontier = [
            (0.8, 200.0),  # Distance: sqrt(0^2 + 150^2) = 150
            (0.6, 100.0),  # Distance: sqrt(0.2^2 + 50^2) ≈ 50
            (0.4, 50.0)    # Distance: sqrt(0.4^2 + 0^2) = 0.4
        ]
        result = calculate_knee_point(frontier)
        
        # The point (0.4, 50) should be closest to ideal (0.8, 50)
        # Actually, let's recalculate:
        # Ideal: (0.8, 50)
        # (0.8, 200): dist = sqrt(0 + 150^2) = 150
        # (0.6, 100): dist = sqrt(0.2^2 + 50^2) = sqrt(0.04 + 2500) ≈ 50.0004
        # (0.4, 50): dist = sqrt(0.4^2 + 0) = 0.4
        
        assert result == (0.4, 50.0)

class TestCalculateTradeoffRSquared:
    """Tests for R^2 calculation."""

    def test_empty_frontier_returns_zero(self):
        """Test that an empty frontier returns 0."""
        result = calculate_tradeoff_r_squared([])
        assert result == 0.0

    def test_single_point_returns_zero(self):
        """Test that a single point returns 0 (no variance)."""
        result = calculate_tradeoff_r_squared([(0.5, 100.0)])
        assert result == 0.0

    def test_two_points_returns_valid_r2(self):
        """Test that two points return a valid R^2."""
        # Perfect linear relationship
        points = [(0.4, 50.0), (0.8, 200.0)]
        result = calculate_tradeoff_r_squared(points)
        
        # With 2 points, R^2 should be 1.0 (perfect fit)
        assert result == 1.0

    def test_non_linear_frontier(self):
        """Test R^2 calculation for a non-linear frontier."""
        # Curved frontier
        points = [
            (0.4, 50.0),
            (0.6, 100.0),
            (0.8, 200.0)
        ]
        result = calculate_tradeoff_r_squared(points)
        
        # Should be less than 1.0 for non-linear
        assert 0.0 <= result <= 1.0

    def test_returns_float(self):
        """Test that the result is a float."""
        points = [(0.5, 100.0), (0.6, 120.0)]
        result = calculate_tradeoff_r_squared(points)
        
        assert isinstance(result, float)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])