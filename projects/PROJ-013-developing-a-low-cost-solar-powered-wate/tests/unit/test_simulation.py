"""
Unit tests for simulation module components.
"""
import pytest
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.data_ingestion import GeometryConfig
from code.simulation import calculate_convective_coeff


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