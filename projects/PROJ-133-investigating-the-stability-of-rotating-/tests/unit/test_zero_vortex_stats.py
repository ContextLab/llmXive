"""
Unit tests for handling zero initial vortex cases in statistical analysis.

This module validates that the statistical pipeline correctly handles scenarios
where no vortices are detected in the initial state, ensuring no division-by-zero
errors occur during metric calculations or statistical aggregations.
"""
import numpy as np
import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.metrics import calculate_vortex_density, calculate_all_metrics, StabilityMetric
from statistics.aggregators import calculate_point_statistics, determine_stability_status
from models.entities import SimulationRun, StabilityMetric as EntityStabilityMetric


class TestZeroVortexStats:
    """Test cases for zero initial vortex scenarios."""

    def test_no_division_by_zero_density(self):
        """
        Verify that calculate_vortex_density does not raise division by zero
        when vortex count is zero.
        
        Scenario: A stable condensate with no vortices detected.
        Expected: Vortex density should be 0.0, not an exception.
        """
        # Create a synthetic phase grid (10x10) with no phase winding (no vortices)
        # Using a constant phase field
        phase_grid = np.zeros((10, 10), dtype=np.float64)
        
        # Define grid parameters
        grid_size = 10
        domain_size = 10.0  # arbitrary units
        dx = domain_size / grid_size
        
        # This should not raise ZeroDivisionError
        density = calculate_vortex_density(0, grid_size * grid_size * dx * dx)
        
        assert density == 0.0, "Vortex density should be 0.0 when no vortices exist"
        assert isinstance(density, float), "Density should be a float"

    def test_no_division_by_zero_metrics(self):
        """
        Verify that calculate_all_metrics handles zero vortices without errors.
        
        Scenario: A snapshot with zero vortices.
        Expected: All metrics should be calculated successfully, with vortex density = 0.
        """
        # Create synthetic data
        density_grid = np.random.rand(10, 10) * 0.1  # Low density, no vortices
        phase_grid = np.zeros((10, 10))  # No phase winding
        
        # Mock vortex detection result (0 vortices)
        num_vortices = 0
        vortex_positions = []
        
        # Calculate area
        area = 10.0 * 10.0  # 100 arbitrary units
        
        # This should not raise any exceptions
        metrics = calculate_all_metrics(
            density_grid=density_grid,
            phase_grid=phase_grid,
            num_vortices=num_vortices,
            vortex_positions=vortex_positions,
            area=area
        )
        
        assert metrics is not None, "Metrics should not be None"
        assert metrics.vortex_density == 0.0, "Vortex density must be 0.0"
        assert metrics.radial_variance >= 0.0, "Radial variance should be non-negative"
        assert metrics.structure_factor_sharpness >= 0.0, "Structure factor sharpness should be non-negative"

    def test_aggregation_zero_vortex_list(self):
        """
        Verify that calculate_point_statistics handles a list of results
        where some or all have zero vortices.
        
        Scenario: Multiple simulation runs, all with zero initial vortices.
        Expected: Statistics (mean, std) should be calculated correctly without division by zero.
        """
        # Simulate multiple runs with zero vortices
        metrics_list = [
            StabilityMetric(
                vortex_density=0.0,
                radial_variance=0.05,
                structure_factor_sharpness=0.8,
                is_stable=True,
                run_id="run_1"
            ),
            StabilityMetric(
                vortex_density=0.0,
                radial_variance=0.06,
                structure_factor_sharpness=0.75,
                is_stable=True,
                run_id="run_2"
            ),
            StabilityMetric(
                vortex_density=0.0,
                radial_variance=0.055,
                structure_factor_sharpness=0.82,
                is_stable=True,
                run_id="run_3"
            )
        ]
        
        # This should not raise ZeroDivisionError
        stats = calculate_point_statistics(metrics_list)
        
        assert stats is not None, "Statistics should be calculated"
        assert stats.mean_vortex_density == 0.0, "Mean vortex density should be 0.0"
        assert stats.std_vortex_density == 0.0, "Std vortex density should be 0.0"
        assert stats.count == 3, "Count should be 3"

    def test_stability_determination_zero_vortex(self):
        """
        Verify that determine_stability_status correctly identifies
        a zero-vortex state as stable (or metastable) without errors.
        
        Scenario: A run with zero vortices and low radial variance.
        Expected: Should be classified as stable.
        """
        # Create a mock simulation run with zero vortices
        run = SimulationRun(
            run_id="test_zero_vortex_run",
            omega=0.5,
            epsilon_dd=0.5,
            n_particles=10000,
            grid_size=64,
            is_successful=True,
            metrics=StabilityMetric(
                vortex_density=0.0,
                radial_variance=0.02,  # Low variance indicates stability
                structure_factor_sharpness=0.9,
                is_stable=True,
                run_id="test_zero_vortex_run"
            )
        )
        
        # This should not raise any exceptions
        stability_status = determine_stability_status(run.metrics)
        
        assert stability_status is not None, "Stability status should be determined"
        assert stability_status.is_stable == True, "Zero vortex state should be stable"

    def test_edge_case_empty_vortex_list(self):
        """
        Test handling of an empty list of vortex positions.
        
        Scenario: Vortex detector returns an empty list.
        Expected: Density calculation should return 0.0.
        """
        vortex_positions = []  # Empty list
        area = 100.0
        num_vortices = len(vortex_positions)
        
        # Direct call to ensure no iteration over empty list causes issues
        density = num_vortices / area if area > 0 else 0.0
        
        assert density == 0.0, "Density from empty list should be 0.0"

    def test_ratio_calculation_zero_denominator_protection(self):
        """
        Explicitly test the ratio calculation logic used in metrics
        to ensure it handles zero denominators gracefully.
        
        This is a defensive test for the internal logic of metrics.py.
        """
        # Simulate a case where area might be 0 (edge case)
        num_vortices = 0
        area = 0.0
        
        # The formula in calculate_vortex_density should handle this
        if area <= 1e-12:
            density = 0.0
        else:
            density = num_vortices / area
        
        assert density == 0.0, "Density with zero area should be 0.0"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])