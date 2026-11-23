"""
Unit tests for T015 aggregation logic.
"""
import pytest
import math
from code.aggregation import calculate_weighted_mean_variance, aggregate_project_level_metrics


class TestWeightedMeanVariance:
    def test_basic_calculation(self):
        """Test basic weighted mean calculation."""
        data = [
            {"response_time_variance": 10.0, "interaction_count": 2},
            {"response_time_variance": 20.0, "interaction_count": 3}
        ]
        # Weighted sum: (10*2 + 20*3) = 20 + 60 = 80
        # Total weight: 2 + 3 = 5
        # Result: 80 / 5 = 16.0
        result = calculate_weighted_mean_variance(data)
        assert math.isclose(result, 16.0, rel_tol=1e-9)

    def test_empty_list(self):
        """Test handling of empty input."""
        result = calculate_weighted_mean_variance([])
        assert result == 0.0

    def test_zero_weights_ignored(self):
        """Test that zero weights are ignored."""
        data = [
            {"response_time_variance": 10.0, "interaction_count": 0},
            {"response_time_variance": 20.0, "interaction_count": 2}
        ]
        # Only second pair counts: 20.0 * 2 / 2 = 20.0
        result = calculate_weighted_mean_variance(data)
        assert math.isclose(result, 20.0, rel_tol=1e-9)

    def test_missing_fields(self):
        """Test handling of missing fields."""
        data = [
            {"response_time_variance": 10.0},  # Missing weight
            {"interaction_count": 2},  # Missing variance
            {"response_time_variance": 30.0, "interaction_count": 1}
        ]
        # Only third pair counts: 30.0 * 1 / 1 = 30.0
        result = calculate_weighted_mean_variance(data)
        assert math.isclose(result, 30.0, rel_tol=1e-9)

    def test_custom_weight_field(self):
        """Test using a custom weight field."""
        data = [
            {"response_time_variance": 100.0, "custom_weight": 1},
            {"response_time_variance": 200.0, "custom_weight": 1}
        ]
        # (100*1 + 200*1) / 2 = 150.0
        result = calculate_weighted_mean_variance(data, weight_field="custom_weight")
        assert math.isclose(result, 150.0, rel_tol=1e-9)


class TestAggregateProjectLevelMetrics:
    def test_aggregation_structure(self):
        """Test that aggregation returns correct structure."""
        data = [
            {"response_time_variance": 10.0, "interaction_count": 2},
            {"response_time_variance": 20.0, "interaction_count": 3}
        ]
        result = aggregate_project_level_metrics(data, "proj-001")

        assert result["project_id"] == "proj-001"
        assert "weighted_mean_variance" in result
        assert "simple_mean_variance" in result
        assert result["pair_count"] == 2
        assert result["aggregation_method"] == "weighted_mean"

    def test_aggregation_values(self):
        """Test calculated values in aggregation."""
        data = [
            {"response_time_variance": 10.0, "interaction_count": 2},
            {"response_time_variance": 20.0, "interaction_count": 3}
        ]
        result = aggregate_project_level_metrics(data, "proj-001")

        # Weighted mean: 16.0
        assert math.isclose(result["weighted_mean_variance"], 16.0, rel_tol=1e-9)

        # Simple mean: (10 + 20) / 2 = 15.0
        assert math.isclose(result["simple_mean_variance"], 15.0, rel_tol=1e-9)

    def test_empty_data(self):
        """Test aggregation with no data."""
        result = aggregate_project_level_metrics([], "proj-empty")
        assert result["weighted_mean_variance"] == 0.0
        assert result["pair_count"] == 0