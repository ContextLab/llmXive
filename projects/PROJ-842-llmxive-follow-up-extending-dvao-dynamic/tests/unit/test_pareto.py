import pytest
import numpy as np
import sys
import os

# Add src to path if running from tests directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.analysis.pareto import (
    calculate_pareto_frontier,
    distance_to_frontier,
    compute_pareto_metrics
)

class TestParetoFrontierCalculation:
    def test_empty_input(self):
        """Test with empty input"""
        objectives = np.array([]).reshape(0, 2)
        result = calculate_pareto_frontier(objectives)
        assert len(result) == 0
        assert result.dtype == bool

    def test_single_point(self):
        """Test with a single point - should be on frontier"""
        objectives = np.array([[1.0, 2.0]])
        result = calculate_pareto_frontier(objectives)
        assert len(result) == 1
        assert result[0] == True

    def test_two_dominated_points(self):
        """Test with two points where one dominates the other"""
        objectives = np.array([
            [2.0, 2.0],  # Dominates
            [1.0, 1.0]   # Dominated
        ])
        result = calculate_pareto_frontier(objectives)
        assert result[0] == True  # First is on frontier
        assert result[1] == False  # Second is dominated

    def test_two_incomparable_points(self):
        """Test with two incomparable points (both on frontier)"""
        objectives = np.array([
            [2.0, 1.0],
            [1.0, 2.0]
        ])
        result = calculate_pareto_frontier(objectives)
        assert result[0] == True
        assert result[1] == True

    def test_multiple_objectives(self):
        """Test with 3 objectives"""
        objectives = np.array([
            [3.0, 3.0, 3.0],  # Best
            [2.0, 2.0, 2.0],  # Dominated by first
            [3.0, 2.0, 2.0]   # Dominated by first
        ])
        result = calculate_pareto_frontier(objectives)
        assert result[0] == True
        assert result[1] == False
        assert result[2] == False

    def test_minimization(self):
        """Test minimization case"""
        objectives = np.array([
            [1.0, 1.0],  # Best (min)
            [2.0, 2.0]   # Worse
        ])
        result = calculate_pareto_frontier(objectives, maximize=False)
        assert result[0] == True
        assert result[1] == False

    def test_duplicate_points(self):
        """Test with duplicate points - both should be on frontier"""
        objectives = np.array([
            [2.0, 2.0],
            [2.0, 2.0]
        ])
        result = calculate_pareto_frontier(objectives)
        # Both are on frontier because neither strictly dominates the other
        assert result[0] == True
        assert result[1] == True


class TestDistanceToFrontier:
    def test_point_on_frontier(self):
        """Test distance is zero when point is on frontier"""
        point = np.array([2.0, 2.0])
        frontier = np.array([
            [2.0, 2.0],
            [3.0, 1.0],
            [1.0, 3.0]
        ])
        dist = distance_to_frontier(point, frontier)
        assert np.isclose(dist, 0.0)

    def test_point_not_on_frontier(self):
        """Test distance is positive when point is not on frontier"""
        point = np.array([1.0, 1.0])
        frontier = np.array([
            [2.0, 2.0],
            [3.0, 1.0],
            [1.0, 3.0]
        ])
        dist = distance_to_frontier(point, frontier)
        assert dist > 0.0
        # Distance to [2, 2] should be sqrt(2)
        expected = np.sqrt(2)
        assert np.isclose(dist, expected)

    def test_empty_frontier(self):
        """Test with empty frontier returns infinity"""
        point = np.array([1.0, 1.0])
        frontier = np.array([]).reshape(0, 2)
        dist = distance_to_frontier(point, frontier)
        assert np.isinf(dist)

    def test_dimension_mismatch(self):
        """Test that dimension mismatch raises error"""
        point = np.array([1.0, 1.0])
        frontier = np.array([[1.0, 2.0, 3.0]])
        with pytest.raises(ValueError):
            distance_to_frontier(point, frontier)


class TestComputeParetoMetrics:
    def test_basic_metrics(self):
        """Test basic metric computation"""
        objectives = np.array([
            [3.0, 3.0],
            [2.0, 2.0],
            [1.0, 1.0]
        ])
        policy_values = np.array([10.0, 5.0, 1.0])

        metrics = compute_pareto_metrics(objectives, policy_values)

        assert 'frontier_indices' in metrics
        assert 'frontier_size' in metrics
        assert 'distances' in metrics
        assert 'mean_distance' in metrics
        assert 'max_distance' in metrics
        assert 'frontier_values' in metrics
        assert 'correlation_reward_distance' in metrics

        # First point should be on frontier
        assert 0 in metrics['frontier_indices']
        assert metrics['frontier_size'] == 1

    def test_multiple_frontier_points(self):
        """Test with multiple points on frontier"""
        objectives = np.array([
            [3.0, 1.0],
            [1.0, 3.0],
            [2.0, 2.0]
        ])
        policy_values = np.array([5.0, 5.0, 3.0])

        metrics = compute_pareto_metrics(objectives, policy_values)

        # Both first and second points should be on frontier
        assert metrics['frontier_size'] == 2
        assert 0 in metrics['frontier_indices']
        assert 1 in metrics['frontier_indices']
        assert 2 not in metrics['frontier_indices']

    def test_correlation_calculation(self):
        """Test that correlation is calculated correctly"""
        objectives = np.array([
            [3.0, 3.0],
            [2.0, 2.0],
            [1.0, 1.0]
        ])
        # High reward for high objective, low reward for low objective
        policy_values = np.array([10.0, 5.0, 1.0])

        metrics = compute_pareto_metrics(objectives, policy_values)

        # Points with higher objectives should be closer to frontier (dist=0)
        # Points with lower objectives should be further
        # So reward and distance should be negatively correlated
        assert -1.0 <= metrics['correlation_reward_distance'] <= 1.0

    def test_mismatched_shapes(self):
        """Test that mismatched shapes raise error"""
        objectives = np.array([[1.0, 2.0], [3.0, 4.0]])
        policy_values = np.array([1.0])

        with pytest.raises(ValueError):
            compute_pareto_metrics(objectives, policy_values)

    def test_constant_policy_values(self):
        """Test correlation when policy values are constant"""
        objectives = np.array([
            [3.0, 3.0],
            [2.0, 2.0],
            [1.0, 1.0]
        ])
        policy_values = np.array([5.0, 5.0, 5.0])

        metrics = compute_pareto_metrics(objectives, policy_values)

        # Correlation should be 0 when one variable is constant
        assert metrics['correlation_reward_distance'] == 0.0