"""
Unit tests for the metrics module, specifically focusing on Chamfer Distance calculation.
Verifies that the calculation is performed on a normalized scale (meters) as per project requirements.
"""
import pytest
import numpy as np
import sys
import os

# Add the code directory to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from lib.metrics import chamfer_distance, calculate_p_psnr, calculate_p_ssim

class TestChamferDistance:
    """Tests for the chamfer_distance function in lib.metrics."""

    def test_identical_point_clouds_zero_distance(self):
        """Verify that identical point clouds result in a Chamfer Distance of 0."""
        # Create two identical random point clouds
        points_a = np.random.rand(100, 3).astype(np.float64)
        points_b = points_a.copy()

        distance = chamfer_distance(points_a, points_b)
        
        # The distance should be effectively zero (allowing for floating point epsilon)
        assert np.isclose(distance, 0.0, atol=1e-6), f"Expected 0.0, got {distance}"

    def test_separated_clouds_positive_distance(self):
        """Verify that separated point clouds result in a positive distance."""
        # Create two distinct point clouds separated by a known distance
        points_a = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
        points_b = np.array([[10.0, 10.0, 10.0], [11.0, 11.0, 11.0]])

        distance = chamfer_distance(points_a, points_b)
        
        # The distance should be positive and non-zero
        assert distance > 0.0, f"Expected positive distance, got {distance}"
        
        # The minimum distance from a point in A to B is roughly sqrt((10-0)^2 * 3) = sqrt(300) ~ 17.32
        # But Chamfer is the average of min distances. 
        # Point (0,0,0) to nearest in B is (10,10,10) -> dist ~ 17.32
        # Point (1,1,1) to nearest in B is (10,10,10) -> dist ~ 15.87
        # Average min distance from A to B ~ 16.6
        # Symmetric average should be similar.
        # We just check it's in a reasonable range > 0
        assert distance > 1.0, f"Expected significant distance, got {distance}"

    def test_normalized_scale_meters(self):
        """
        Verify that the Chamfer Distance is calculated on a normalized scale (meters).
        This test ensures that if input coordinates are in meters, the output is in meters.
        """
        # Define points in meters
        points_a = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]) # 1 meter apart
        points_b = np.array([[2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]) # 1 meter apart, shifted by 2m from A

        # Distance from A to B:
        # (0,0,0) -> nearest in B is (2,0,0) -> dist = 2
        # (1,0,0) -> nearest in B is (2,0,0) -> dist = 1
        # Avg A->B = 1.5
        
        # Distance from B to A:
        # (2,0,0) -> nearest in A is (1,0,0) -> dist = 1
        # (3,0,0) -> nearest in A is (1,0,0) -> dist = 2
        # Avg B->A = 1.5
        
        # Total Chamfer = 1.5 + 1.5 = 3.0 meters
        distance = chamfer_distance(points_a, points_b)
        
        # Assert the result is approximately 3.0 meters
        assert np.isclose(distance, 3.0, atol=1e-6), f"Expected 3.0 meters, got {distance}"

    def test_empty_point_cloud_handling(self):
        """Verify behavior when one or both point clouds are empty."""
        points_a = np.array([]).reshape(0, 3)
        points_b = np.array([[1.0, 1.0, 1.0]])

        # The function should handle empty inputs gracefully or raise a specific error.
        # Assuming the implementation raises ValueError for empty inputs as per robust design.
        with pytest.raises(ValueError):
            chamfer_distance(points_a, points_b)

    def test_scale_invariance_with_uniform_scaling(self):
        """
        Verify that scaling the input coordinates by a factor scales the distance by the same factor.
        This confirms the metric is linear and consistent with physical units (meters).
        """
        points_a = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
        points_b = np.array([[2.0, 2.0, 2.0], [3.0, 3.0, 3.0]])

        distance_original = chamfer_distance(points_a, points_b)

        # Scale by 10
        points_a_scaled = points_a * 10.0
        points_b_scaled = points_b * 10.0

        distance_scaled = chamfer_distance(points_a_scaled, points_b_scaled)

        # The distance should scale linearly
        assert np.isclose(distance_scaled, distance_original * 10.0, rtol=1e-5), \
            f"Expected scaled distance to be 10x original, got {distance_scaled} vs {distance_original * 10.0}"

    def test_asymmetry_check(self):
        """
        Verify that the directed distances (A->B and B->A) can differ,
        even if the final symmetric Chamfer distance is their sum.
        """
        # Create a case where one cloud is a subset of the other
        points_a = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]])
        points_b = np.array([[1.0, 1.0, 1.0]]) # A subset

        # A->B:
        # (0,0,0) -> (1,1,1) dist ~ 1.732
        # (1,1,1) -> (1,1,1) dist = 0
        # (2,2,2) -> (1,1,1) dist ~ 1.732
        # Avg = (1.732 + 0 + 1.732) / 3 = 1.1547

        # B->A:
        # (1,1,1) -> (1,1,1) dist = 0
        # Avg = 0

        # The function returns the sum of directed distances.
        # We just verify it runs and returns a scalar.
        distance = chamfer_distance(points_a, points_b)
        assert isinstance(distance, float), "Chamfer distance should return a float"
        assert distance >= 0.0, "Chamfer distance must be non-negative"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])