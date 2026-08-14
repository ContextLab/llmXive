"""
Unit tests for model utility functions (clamping and extrapolation detection).
"""
import pytest
import numpy as np
from scipy.spatial import ConvexHull

from model_utils import clamp_predictions, test_extrapolation, process_model_predictions

class TestClampPredictions:
    def test_no_clamping_needed(self):
        """Test when all predictions are within bounds."""
        predictions = np.array([10.0, 20.0, 30.0])
        result = clamp_predictions(predictions, lower_bound=0.0, upper_bound=100.0)
        np.testing.assert_array_equal(result, predictions)

    def test_lower_bound_clamping(self):
        """Test clamping to lower bound."""
        predictions = np.array([-5.0, 10.0, -1.0])
        result = clamp_predictions(predictions, lower_bound=0.0)
        expected = np.array([0.0, 10.0, 0.0])
        np.testing.assert_array_equal(result, expected)

    def test_upper_bound_clamping(self):
        """Test clamping to upper bound."""
        predictions = np.array([50.0, 150.0, 200.0])
        result = clamp_predictions(predictions, upper_bound=100.0)
        expected = np.array([50.0, 100.0, 100.0])
        np.testing.assert_array_equal(result, expected)

    def test_both_bounds_clamping(self):
        """Test clamping with both bounds."""
        predictions = np.array([-10.0, 50.0, 150.0, 200.0])
        result = clamp_predictions(predictions, lower_bound=0.0, upper_bound=100.0)
        expected = np.array([0.0, 50.0, 100.0, 100.0])
        np.testing.assert_array_equal(result, expected)

    def test_modulus_property_clamping(self):
        """Test specific case for modulus properties (must be > 0)."""
        predictions = np.array([-2.5, 0.0, 0.5, 10.0])
        result = clamp_predictions(predictions, lower_bound=0.0, property_name="shear_modulus")
        expected = np.array([0.0, 0.0, 0.5, 10.0])
        np.testing.assert_array_equal(result, expected)

class TestExtrapolationDetection:
    def setup_method(self):
        """Setup test data."""
        # Create a simple 2D training set forming a triangle
        self.training_features = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.5, 0.5],
            [0.2, 0.2]
        ])
        
        # Points inside the hull
        self.inside_points = np.array([
            [0.3, 0.3],
            [0.4, 0.2],
            [0.1, 0.6]
        ])
        
        # Points outside the hull
        self.outside_points = np.array([
            [-0.1, 0.1],
            [0.5, 0.6],
            [1.1, 0.0],
            [0.0, 1.1]
        ])

    def test_inside_points_not_extrapolated(self):
        """Test that points inside the hull are not flagged as extrapolated."""
        is_extrapolated, stats = test_extrapolation(self.inside_points, self.training_features)
        assert not np.any(is_extrapolated), "Points inside hull should not be extrapolated"
        assert stats["extrapolated_count"] == 0

    def test_outside_points_extrapolated(self):
        """Test that points outside the hull are flagged as extrapolated."""
        is_extrapolated, stats = test_extrapolation(self.outside_points, self.training_features)
        assert np.all(is_extrapolated), "Points outside hull should be extrapolated"
        assert stats["extrapolated_count"] == len(self.outside_points)

    def test_mixed_points(self):
        """Test with a mix of inside and outside points."""
        mixed_points = np.vstack([self.inside_points, self.outside_points])
        is_extrapolated, stats = test_extrapolation(mixed_points, self.training_features)
        
        expected_extrapolated = np.array([False, False, False, True, True, True, True])
        np.testing.assert_array_equal(is_extrapolated, expected_extrapolated)
        assert stats["extrapolated_count"] == 4
        assert stats["total_points"] == 7

    def test_insufficient_training_data(self):
        """Test behavior when training data is insufficient for hull."""
        insufficient_training = np.array([[0.0, 0.0], [1.0, 1.0]])
        test_points = np.array([[0.5, 0.5]])
        
        is_extrapolated, stats = test_extrapolation(test_points, insufficient_training)
        
        assert np.all(is_extrapolated), "Should flag all as extrapolated when hull cannot be computed"
        assert stats["reason"] == "insufficient_training_data"

    def test_high_dimensional_data(self):
        """Test with higher dimensional data."""
        training_5d = np.random.rand(20, 5)
        test_5d = np.random.rand(5, 5)
        
        is_extrapolated, stats = test_extrapolation(test_5d, training_5d)
        
        assert len(is_extrapolated) == 5
        assert "extrapolated_count" in stats
        assert "percentage_extrapolated" in stats

class TestProcessModelPredictions:
    def setup_method(self):
        """Setup test data."""
        self.training_features = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.5, 0.5],
            [0.2, 0.2]
        ])
        self.feature_matrix = np.array([
            [0.3, 0.3],  # Inside
            [-0.1, 0.1], # Outside
            [0.5, 0.6],  # Outside
            [0.4, 0.2]   # Inside
        ])
        self.raw_predictions = np.array([-5.0, 10.0, 150.0, 50.0])

    def test_clamping_and_extrapolation(self):
        """Test full pipeline with clamping and extrapolation detection."""
        result = process_model_predictions(
            self.raw_predictions,
            self.feature_matrix,
            self.training_features,
            "shear_modulus",
            lower_bound=0.0,
            upper_bound=100.0
        )
        
        # Check clamping
        expected_clamped = np.array([0.0, 10.0, 100.0, 50.0])
        np.testing.assert_array_equal(result["clamped_predictions"], expected_clamped)
        
        # Check extrapolation
        expected_extrapolated = np.array([False, True, True, False])
        np.testing.assert_array_equal(result["is_extrapolated"], expected_extrapolated)
        
        # Check structure
        assert "raw_predictions" in result
        assert "clamped_predictions" in result
        assert "is_extrapolated" in result
        assert "extrapolation_stats" in result
        assert result["property_name"] == "shear_modulus"

    def test_no_upper_bound(self):
        """Test with only lower bound specified."""
        result = process_model_predictions(
            self.raw_predictions,
            self.feature_matrix,
            self.training_features,
            "bulk_modulus",
            lower_bound=0.0
        )
        
        expected_clamped = np.array([0.0, 10.0, 150.0, 50.0])
        np.testing.assert_array_equal(result["clamped_predictions"], expected_clamped)
        assert result["extrapolation_stats"]["extrapolated_count"] == 2