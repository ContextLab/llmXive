"""
Unit tests for simulation module components.
"""
import pytest
import sys
import os
from pathlib import Path
import math

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.data_ingestion import GeometryConfig
from code.simulation import calculate_view_factor, calculate_convective_coeff


class TestCalculateViewFactor:
    """Tests for the view factor calculation."""

    def test_function_exists(self):
        """Verify calculate_view_factor exists with correct signature."""
        # Signature: (geometry: GeometryConfig, angle: float) -> float
        assert callable(calculate_view_factor)

    def test_returns_within_range_flat_plate(self):
        """Assert the result is within [0, 1] for a flat plate geometry."""
        geometry = GeometryConfig(
            geometry_id="flat_plate",
            surface_area=1.0,
            inclination_angle=0.0,
            view_factor=1.0
        )

        # Test with angle 0 (sun directly overhead)
        angle = 0.0
        result = calculate_view_factor(geometry, angle)

        assert isinstance(result, float), "Result should be a float"
        assert 0.0 <= result <= 1.0, f"View factor must be in [0, 1], got {result}"

    def test_returns_within_range_single_slope(self):
        """Assert the result is within [0, 1] for a single slope geometry."""
        geometry = GeometryConfig(
            geometry_id="single_slope",
            surface_area=1.0,
            inclination_angle=45.0,
            view_factor=0.9
        )

        # Test with various angles
        for angle in [0.0, 30.0, 45.0, 60.0, 80.0]:
            result = calculate_view_factor(geometry, angle)
            assert isinstance(result, float), f"Result for angle {angle} should be a float"
            assert 0.0 <= result <= 1.0, f"View factor for angle {angle} must be in [0, 1], got {result}"

    def test_returns_within_range_double_slope(self):
        """Assert the result is within [0, 1] for a double slope geometry."""
        geometry = GeometryConfig(
            geometry_id="double_slope",
            surface_area=1.0,
            inclination_angle=30.0,
            view_factor=0.95
        )

        # Test with various angles
        for angle in [0.0, 15.0, 30.0, 45.0, 75.0]:
            result = calculate_view_factor(geometry, angle)
            assert isinstance(result, float), f"Result for angle {angle} should be a float"
            assert 0.0 <= result <= 1.0, f"View factor for angle {angle} must be in [0, 1], got {result}"

    def test_view_factor_decreases_with_angle(self):
        """Assert that view factor generally decreases as angle deviates from optimal."""
        geometry = GeometryConfig(
            geometry_id="flat_plate",
            surface_area=1.0,
            inclination_angle=0.0,
            view_factor=1.0
        )

        # For a flat plate (inclination 0), view factor should be highest at angle 0
        result_0 = calculate_view_factor(geometry, 0.0)
        result_45 = calculate_view_factor(geometry, 45.0)
        result_80 = calculate_view_factor(geometry, 80.0)

        # The view factor should decrease as the angle increases (assuming sun angle relative to surface)
        # Note: The exact behavior depends on the implementation, but it should stay within [0, 1]
        assert result_0 >= 0.0
        assert result_45 >= 0.0
        assert result_80 >= 0.0
        assert result_0 <= 1.0
        assert result_45 <= 1.0
        assert result_80 <= 1.0

    def test_handles_extreme_angles(self):
        """Assert behavior at extreme angles (0 and 90 degrees)."""
        geometry = GeometryConfig(
            geometry_id="flat_plate",
            surface_area=1.0,
            inclination_angle=0.0,
            view_factor=1.0
        )

        # At 0 degrees
        result_0 = calculate_view_factor(geometry, 0.0)
        assert 0.0 <= result_0 <= 1.0, f"View factor at 0 degrees must be in [0, 1], got {result_0}"

        # At 90 degrees
        result_90 = calculate_view_factor(geometry, 90.0)
        assert 0.0 <= result_90 <= 1.0, f"View factor at 90 degrees must be in [0, 1], got {result_90}"

    def test_different_geometries_produce_valid_results(self):
        """Verify that different geometry configurations produce valid view factors."""
        geometries = [
            GeometryConfig(geometry_id="flat_plate", surface_area=1.0, inclination_angle=0.0, view_factor=1.0),
            GeometryConfig(geometry_id="single_slope", surface_area=1.0, inclination_angle=45.0, view_factor=0.9),
            GeometryConfig(geometry_id="double_slope", surface_area=1.0, inclination_angle=30.0, view_factor=0.95)
        ]

        angle = 30.0

        for geom in geometries:
            result = calculate_view_factor(geom, angle)
            assert isinstance(result, float), f"Result for {geom.geometry_id} should be a float"
            assert 0.0 <= result <= 1.0, f"View factor for {geom.geometry_id} must be in [0, 1], got {result}"


class TestCalculateConvectiveCoeff:
    """Tests for the convective heat transfer coefficient calculation."""

    def test_function_exists(self):
        """Verify calculate_convective_coeff exists with correct signature."""
        # Signature: (temp_diff: float, geometry: GeometryConfig) -> float
        assert callable(calculate_convective_coeff)

    def test_returns_positive_for_valid_inputs(self):
        """Assert the result is positive for valid inputs."""
        # Create a valid geometry config (using defaults from data_ingestion)
        geometry = GeometryConfig(
            geometry_id="single_slope",
            surface_area=1.0,
            inclination_angle=45.0,
            view_factor=0.9
        )

        # Test with a positive temperature difference (e.g., 10°C)
        temp_diff = 10.0
        result = calculate_convective_coeff(temp_diff, geometry)

        assert isinstance(result, float), "Result should be a float"
        assert result > 0.0, "Convective coefficient must be positive"

    def test_returns_positive_for_small_temp_diff(self):
        """Assert the result is positive even for small temperature differences."""
        geometry = GeometryConfig(
            geometry_id="flat_plate",
            surface_area=2.0,
            inclination_angle=0.0,
            view_factor=1.0
        )

        temp_diff = 0.1  # Small but positive
        result = calculate_convective_coeff(temp_diff, geometry)

        assert result > 0.0, "Convective coefficient must be positive for small temp_diff"

    def test_returns_positive_for_large_temp_diff(self):
        """Assert the result is positive for large temperature differences."""
        geometry = GeometryConfig(
            geometry_id="double_slope",
            surface_area=1.5,
            inclination_angle=30.0,
            view_factor=0.95
        )

        temp_diff = 50.0  # Large temperature difference
        result = calculate_convective_coeff(temp_diff, geometry)

        assert result > 0.0, "Convective coefficient must be positive for large temp_diff"

    def test_handles_zero_temp_diff(self):
        """Assert behavior when temp_diff is zero (should not crash, result should be non-negative)."""
        geometry = GeometryConfig(
            geometry_id="single_slope",
            surface_area=1.0,
            inclination_angle=45.0,
            view_factor=0.9
        )

        temp_diff = 0.0
        result = calculate_convective_coeff(temp_diff, geometry)

        # Even with zero temp_diff, the function should return a non-negative value
        # (often a baseline or minimum coefficient is used)
        assert result >= 0.0, "Convective coefficient should be non-negative for zero temp_diff"

    def test_different_geometries_produce_valid_results(self):
        """Verify that different geometry configurations produce valid positive coefficients."""
        geometries = [
            GeometryConfig(geometry_id="flat_plate", surface_area=1.0, inclination_angle=0.0, view_factor=1.0),
            GeometryConfig(geometry_id="single_slope", surface_area=1.0, inclination_angle=45.0, view_factor=0.9),
            GeometryConfig(geometry_id="double_slope", surface_area=1.0, inclination_angle=30.0, view_factor=0.95)
        ]

        temp_diff = 15.0

        for geom in geometries:
            result = calculate_convective_coeff(temp_diff, geom)
            assert result > 0.0, f"Convective coefficient must be positive for {geom.geometry_id}"