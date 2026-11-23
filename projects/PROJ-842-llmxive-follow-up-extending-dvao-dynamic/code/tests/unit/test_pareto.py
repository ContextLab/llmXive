"""
Unit tests for the Pareto frontier analysis module.
"""
import pytest
import numpy as np
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from src.analysis.pareto import (
    calculate_pareto_frontier,
    distance_to_frontier,
    compute_pareto_metrics
)

class TestParetoFrontierCalculation:
    def test_simple_dominance(self):
        """Test basic dominance logic."""
        # Point A dominates B
        points = np.array([
            [10, 10],  # A
            [5, 5],    # B (dominated by A)
            [10, 5]    # C (not dominated by A, A not dominated by C)
        ])
        
        frontier = calculate_pareto_frontier(points)
        
        # A and C should be on the frontier. B should not.
        assert len(frontier) == 2
        
        # Check if A and C are present (order may vary)
        frontier_list = [tuple(p) for p in frontier]
        assert (10.0, 10.0) in frontier_list
        assert (10.0, 5.0) in frontier_list

    def test_identical_points(self):
        """Test handling of identical points."""
        points = np.array([
            [10, 10],
            [10, 10],
            [5, 5]
        ])
        
        frontier = calculate_pareto_frontier(points)
        # Should keep one instance of the dominant point
        assert len(frontier) == 1
        assert np.allclose(frontier[0], [10, 10])

    def test_empty_input(self):
        """Test handling of empty input."""
        points = np.empty((0, 2))
        frontier = calculate_pareto_frontier(points)
        assert frontier.shape == (0, 2)

    def test_single_point(self):
        """Test single point input."""
        points = np.array([[5, 5]])
        frontier = calculate_pareto_frontier(points)
        assert len(frontier) == 1
        assert np.allclose(frontier[0], [5, 5])

class TestDistanceToFrontier:
    def test_point_on_frontier(self):
        """Test distance is zero if point is on frontier."""
        returns_matrix = np.array([
            [10, 10],
            [5, 5],
            [10, 5]
        ])
        achieved = np.array([10, 10])
        
        dist = distance_to_frontier(achieved, returns_matrix=returns_matrix)
        assert np.isclose(dist, 0.0)

    def test_point_off_frontier(self):
        """Test distance is positive if point is off frontier."""
        returns_matrix = np.array([
            [10, 10],
            [10, 5],
            [5, 10]
        ])
        achieved = np.array([5, 5])
        
        dist = distance_to_frontier(achieved, returns_matrix=returns_matrix)
        # Distance to (10, 10) is sqrt(5^2 + 5^2) = sqrt(50) approx 7.07
        # Distance to (10, 5) is 5
        # Distance to (5, 10) is 5
        # Min distance should be 5.0
        assert np.isclose(dist, 5.0)

    def test_multiple_achieved_points(self):
        """Test distance calculation for multiple achieved points."""
        returns_matrix = np.array([
            [10, 10],
            [10, 5],
            [5, 10]
        ])
        achieved = np.array([
            [5, 5],
            [10, 10]
        ])
        
        dist = distance_to_frontier(achieved, returns_matrix=returns_matrix)
        # Min distance of [5,5] is 5.0, [10,10] is 0.0. Overall min is 0.0.
        assert np.isclose(dist, 0.0)

    def test_precomputed_frontier(self):
        """Test using pre-computed frontier."""
        frontier = np.array([[10, 10], [10, 5]])
        achieved = np.array([5, 5])
        
        dist = distance_to_frontier(achieved, frontier_points=frontier)
        # Closest is (10, 5) -> dist 5.0
        assert np.isclose(dist, 5.0)

class TestComputeParetoMetrics:
    def test_metrics_calculation(self):
        """Test comprehensive metrics output."""
        returns_matrix = np.array([
            [10, 10],
            [10, 5],
            [5, 10],
            [5, 5]
        ])
        policy_returns = np.array([5, 5])
        
        metrics = compute_pareto_metrics(returns_matrix, policy_returns)
        
        assert metrics["frontier_size"] == 3
        assert not metrics["is_pareto_optimal"]
        assert "min_distance" in metrics
        assert "mean_distance" in metrics

    def test_optimal_policy(self):
        """Test metrics for an optimal policy."""
        returns_matrix = np.array([
            [10, 10],
            [5, 5]
        ])
        policy_returns = np.array([10, 10])
        
        metrics = compute_pareto_metrics(returns_matrix, policy_returns)
        
        assert metrics["is_pareto_optimal"]
        assert np.isclose(metrics["min_distance"], 0.0)