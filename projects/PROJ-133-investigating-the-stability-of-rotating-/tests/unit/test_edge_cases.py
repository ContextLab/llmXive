"""
Unit tests for edge cases in vortex detection and stability metrics.

Specifically tests:
1. Zero initial vortices scenario
2. Vortex-antivortex annihilation events
3. Division by zero handling in metric calculations
"""
import numpy as np
import pytest
from typing import List, Tuple
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis.vortex_detector import (
    calculate_phase_winding, 
    detect_vortices_phase_winding
)
from analysis.metrics import (
    calculate_vortex_density, 
    calculate_radial_variance, 
    calculate_structure_factor_sharpness
)
from utils.logger import get_logger

logger = get_logger(__name__)


def create_phase_grid_with_vortices(
    shape: Tuple[int, int], 
    vortices: List[Tuple[int, int, int]], 
    grid_size: float = 10.0
) -> np.ndarray:
    """
    Create a synthetic phase grid with specified vortices.
    
    Args:
        shape: Grid dimensions (Nx, Ny)
        vortices: List of (x, y, charge) tuples where charge is +1 (vortex) or -1 (antivortex)
        grid_size: Physical size of the domain
        
    Returns:
        Phase grid (radians)
    """
    Nx, Ny = shape
    x = np.linspace(-grid_size/2, grid_size/2, Nx)
    y = np.linspace(-grid_size/2, grid_size/2, Ny)
    X, Y = np.meshgrid(x, y)
    
    phase = np.zeros((Ny, Nx))
    
    for vx, vy, charge in vortices:
        # Convert grid coordinates to physical
        px = x[vx] if 0 <= vx < Nx else 0
        py = y[vy] if 0 <= vy < Ny else 0
        
        # Calculate phase contribution from this vortex
        dx = X - px
        dy = Y - py
        # Avoid division by zero at vortex core
        r2 = dx**2 + dy**2 + 1e-10
        
        # Phase winding: theta = charge * arctan2(dy, dx)
        phase += charge * np.arctan2(dy, dx)
    
    return phase


def test_zero_initial_vortices():
    """
    Test that zero initial vortices results in zero vortex count and valid metrics.
    
    This is a critical edge case:
    - No vortices should be detected
    - Vortex density should be exactly 0
    - Radial variance should be calculated without error
    - Structure factor should be calculated without error
    - No division by zero errors should occur
    """
    # Create a grid with NO vortices (flat phase)
    shape = (64, 64)
    phase_grid = create_phase_grid_with_vortices(shape, vortices=[])
    
    # Detect vortices
    detected_vortices = detect_vortices_phase_winding(phase_grid, grid_size=10.0)
    
    # Assertions
    assert len(detected_vortices) == 0, f"Expected 0 vortices, got {len(detected_vortices)}"
    
    # Calculate metrics
    area = 10.0 * 10.0  # grid_size^2
    vortex_density = calculate_vortex_density(len(detected_vortices), area)
    
    assert vortex_density == 0.0, f"Expected vortex density 0.0, got {vortex_density}"
    
    # Radial variance with zero vortices should be 0 (or handle gracefully)
    # Since there are no vortex positions, we expect 0 or a defined default
    radial_variance = calculate_radial_variance([])
    assert radial_variance == 0.0, f"Expected radial variance 0.0, got {radial_variance}"
    
    # Structure factor sharpness with no vortices
    # Create a mock density array (flat) for structure factor calculation
    density = np.ones(shape) / (shape[0] * shape[1])  # Normalized flat density
    structure_factor_sharpness = calculate_structure_factor_sharpness(density)
    
    # Should not raise an error and should return a valid float
    assert isinstance(structure_factor_sharpness, float), "Structure factor sharpness should be a float"
    assert not np.isnan(structure_factor_sharpness), "Structure factor sharpness should not be NaN"
    
    logger.info("test_zero_initial_vortices passed: Zero vortex case handled correctly")


def test_vortex_antivortex_annihilation():
    """
    Test detection of vortex-antivortex pairs and their potential annihilation.
    
    Scenario: Create a pair of opposite charges very close together.
    In a real simulation, these might annihilate, leaving zero net vorticity.
    The detector should either:
    1. Detect both (if separation is above resolution)
    2. Detect neither (if they cancel out in phase winding)
    """
    shape = (64, 64)
    grid_size = 10.0
    
    # Create a vortex-antivortex pair
    center_x, center_y = 32, 32
    separation = 2  # pixels apart
    
    vortices = [
        (center_x, center_y, +1),      # Vortex
        (center_x + separation, center_y, -1)  # Antivortex
    ]
    
    phase_grid = create_phase_grid_with_vortices(shape, vortices, grid_size)
    
    # Detect vortices
    detected_vortices = detect_vortices_phase_winding(phase_grid, grid_size=grid_size)
    
    # The detector might find 0, 1, or 2 vortices depending on resolution
    # Key assertion: No crash, and metrics are calculable
    logger.info(f"Detected {len(detected_vortices)} vortices in annihilation test")
    
    # Calculate metrics - must not crash
    area = grid_size * grid_size
    vortex_density = calculate_vortex_density(len(detected_vortices), area)
    
    # Extract positions for radial variance
    positions = [(v[0], v[1]) for v in detected_vortices]
    radial_variance = calculate_radial_variance(positions)
    
    # All metrics should be valid numbers
    assert not np.isnan(vortex_density), "Vortex density should not be NaN"
    assert not np.isnan(radial_variance), "Radial variance should not be NaN"
    
    logger.info("test_vortex_antivortex_annihilation passed: Annihilation edge case handled")


def test_single_vortex_detection():
    """
    Verify that a single vortex is correctly detected and counted.
    """
    shape = (64, 64)
    vortices = [(32, 32, +1)]
    
    phase_grid = create_phase_grid_with_vortices(shape, vortices, grid_size=10.0)
    
    detected_vortices = detect_vortices_phase_winding(phase_grid, grid_size=10.0)
    
    assert len(detected_vortices) == 1, f"Expected 1 vortex, got {len(detected_vortices)}"
    
    # Verify charge
    # The vortex detector returns (x, y, charge) tuples
    assert detected_vortices[0][2] == +1, "Detected vortex should have charge +1"
    
    logger.info("test_single_vortex_detection passed: Single vortex correctly identified")


def test_multiple_vortices_with_zero_net_charge():
    """
    Test a configuration with multiple vortices but zero net charge.
    """
    shape = (64, 64)
    # Two vortices (+1) and two antivortices (-1)
    vortices = [
        (20, 20, +1),
        (40, 40, +1),
        (20, 40, -1),
        (40, 20, -1)
    ]
    
    phase_grid = create_phase_grid_with_vortices(shape, vortices, grid_size=10.0)
    
    detected_vortices = detect_vortices_phase_winding(phase_grid, grid_size=10.0)
    
    # Should detect 4 vortices (2 positive, 2 negative)
    assert len(detected_vortices) == 4, f"Expected 4 vortices, got {len(detected_vortices)}"
    
    # Calculate density
    area = 10.0 * 10.0
    density = calculate_vortex_density(len(detected_vortices), area)
    expected_density = 4.0 / area
    
    assert np.isclose(density, expected_density), f"Expected density {expected_density}, got {density}"
    
    logger.info("test_multiple_vortices_with_zero_net_charge passed: Multiple vortices handled correctly")


def test_metrics_with_single_vortex():
    """
    Test metric calculations with exactly one vortex (edge case for variance).
    """
    # With one vortex, radial variance should be 0 (no spread)
    positions = [(32, 32)]
    radial_variance = calculate_radial_variance(positions)
    
    assert radial_variance == 0.0, f"Expected 0 variance for single point, got {radial_variance}"
    
    logger.info("test_metrics_with_single_vortex passed: Single vortex metrics correct")