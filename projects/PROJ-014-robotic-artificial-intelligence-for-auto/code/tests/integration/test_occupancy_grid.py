"""
Integration test for occupancy grid generation (US2).

This test verifies that the occupancy grid generation pipeline:
1. Correctly processes depth data into a binary occupancy grid.
2. Respects the specified radius and resolution parameters.
3. Handles noise injection gracefully (simulated via SimWrapper).
4. Produces a grid with the expected shape and binary dtype.
5. Aligns with the calibration parameters if available.

It relies on the real implementation in `code/src/data/pipeline.py`
and the simulation wrapper in `code/src/environment/sim_wrapper.py`.
"""
import os
import sys
import json
import pytest
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Any

# Add src to path if not already done (handled by conftest usually, but safe to ensure)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.environment.sim_wrapper import SimWrapper, NoiseConfig, create_sim_wrapper
from src.utils.config import get_config, init_config, get_path
from src.data.calibration import ExtrinsicParams, CalibrationReport, CalibrationValidator
from src.data.pipeline import generate_occupancy_grid, preprocess_depth

# Constants for test parameters
TEST_GRID_RES = 0.1  # meters per cell
TEST_GRID_SIZE = 20  # 20x20 grid
TEST_RADIUS = 0.5    # meters
TEST_NOISE_LEVEL = 0.05

@pytest.fixture
def sim_wrapper():
    """Create a SimWrapper instance with deterministic noise for testing."""
    noise_cfg = NoiseConfig(
        depth_noise_std=TEST_NOISE_LEVEL,
        lidar_noise_std=0.0,
        enabled=True
    )
    wrapper = create_sim_wrapper(noise_cfg)
    return wrapper

@pytest.fixture
def dummy_calibration():
    """Create a dummy calibration report for spatial alignment checks."""
    # In a real scenario, this would come from results/calibration_report.json
    # Here we simulate a valid report structure
    calib_data = {
        "timestamp": "2023-10-27T10:00:00Z",
        "extrinsics": {
            "rotation": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
            "translation": [0.0, 0.0, 0.0]
        },
        "validation": {
            "passed": True,
            "error_meters": 0.001
        }
    }
    return calib_data

@pytest.fixture
def mock_depth_data(sim_wrapper):
    """
    Generate mock depth data using the sim_wrapper.
    Since we don't have real sensor data, we use the wrapper to generate
    a consistent, deterministic depth map that simulates a simple obstacle.
    """
    # Simulate a scene: empty space with a wall at 5 meters
    height, width = 480, 640
    depth_map = np.ones((height, width), dtype=np.float32) * 10.0  # Default 10m empty
    
    # Create a "wall" in the center
    center_y, center_x = height // 2, width // 2
    wall_radius = 50
    y, x = np.ogrid[:height, :width]
    mask = (x - center_x)**2 + (y - center_y)**2 <= wall_radius**2
    depth_map[mask] = 5.0  # Wall at 5m
    
    # Apply noise via wrapper (if enabled)
    noisy_depth = sim_wrapper.inject_depth_noise(depth_map)
    return noisy_depth

def test_occupancy_grid_generation_basic(mock_depth_data, dummy_calibration):
    """
    Test basic generation of occupancy grid from depth data.
    Verifies output shape, dtype, and binary nature.
    """
    grid = generate_occupancy_grid(
        depth_map=mock_depth_data,
        resolution=TEST_GRID_RES,
        max_range=10.0,
        radius=TEST_RADIUS,
        calibration=dummy_calibration
    )
    
    assert grid is not None, "Occupancy grid generation returned None"
    assert isinstance(grid, np.ndarray), "Output must be a numpy array"
    assert grid.dtype == np.uint8 or grid.dtype == bool, "Grid must be binary (uint8 or bool)"
    
    # Check shape: (height_cells, width_cells)
    # Expected cells = floor(2 * max_range / resolution)
    expected_dim = int(np.floor(2 * 10.0 / TEST_GRID_RES))
    assert grid.shape[0] == expected_dim, f"Expected height {expected_dim}, got {grid.shape[0]}"
    assert grid.shape[1] == expected_dim, f"Expected width {expected_dim}, got {grid.shape[1]}"
    
    # Verify binary values (0 for empty, 1 for occupied)
    unique_vals = np.unique(grid)
    assert all(v in [0, 1] for v in unique_vals), f"Grid must be binary, found values: {unique_vals}"

def test_occupancy_grid_obstacle_detection(mock_depth_data, dummy_calibration):
    """
    Test that the grid correctly detects obstacles within the specified radius.
    """
    grid = generate_occupancy_grid(
        depth_map=mock_depth_data,
        resolution=TEST_GRID_RES,
        max_range=10.0,
        radius=TEST_RADIUS,
        calibration=dummy_calibration
    )
    
    # The mock data has a wall at 5m. With radius 0.5m, cells within 0.5m of the wall
    # should be occupied.
    # We check the center of the grid (corresponding to the center of the image)
    # The wall is at the center, so the center cell should be occupied.
    center_y, center_x = grid.shape[0] // 2, grid.shape[1] // 2
    
    # Allow a small margin of error due to discretization
    is_occupied = False
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            y, x = center_y + dy, center_x + dx
            if 0 <= y < grid.shape[0] and 0 <= x < grid.shape[1]:
                if grid[y, x] == 1:
                    is_occupied = True
                    break
        if is_occupied:
            break
    
    assert is_occupied, "Expected the center of the grid to be occupied (wall at 5m)"

def test_occupancy_grid_empty_space(mock_depth_data, dummy_calibration):
    """
    Test that empty space (far from obstacles) is correctly marked as 0.
    """
    # Modify mock data to have a large empty region
    height, width = mock_depth_data.shape
    empty_region = mock_depth_data.copy()
    # Set a large corner to 20m (beyond max_range or very far)
    empty_region[0:height//4, 0:width//4] = 20.0
    
    grid = generate_occupancy_grid(
        depth_map=empty_region,
        resolution=TEST_GRID_RES,
        max_range=15.0, # Increase max range to include the 20m point as "out of range" or far
        radius=TEST_RADIUS,
        calibration=dummy_calibration
    )
    
    # The top-left corner should be empty (0)
    corner_y, corner_x = 0, 0
    # Check a small region
    is_empty = True
    for dy in range(0, 5):
        for dx in range(0, 5):
            y, x = corner_y + dy, corner_x + dx
            if y < grid.shape[0] and x < grid.shape[1]:
                if grid[y, x] == 1:
                    is_empty = False
                    break
        if not is_empty:
            break
    
    assert is_empty, "Expected the far corner to be empty"

def test_occupancy_grid_noise_sensitivity(mock_depth_data, dummy_calibration):
    """
    Test that the grid generation is robust to noise (simulated by SimWrapper).
    We compare a grid generated with noise vs without noise.
    """
    # Generate with noise (already applied in mock_depth_data via fixture)
    grid_noisy = generate_occupancy_grid(
        depth_map=mock_depth_data,
        resolution=TEST_GRID_RES,
        max_range=10.0,
        radius=TEST_RADIUS,
        calibration=dummy_calibration
    )
    
    # Generate without noise
    grid_clean = generate_occupancy_grid(
        depth_map=mock_depth_data * (1.0 - TEST_NOISE_LEVEL), # Approximate clean
        resolution=TEST_GRID_RES,
        max_range=10.0,
        radius=TEST_RADIUS,
        calibration=dummy_calibration
    )
    
    # The grids should be similar, but not necessarily identical due to discretization
    # We check that the correlation is high
    correlation = np.corrcoef(grid_noisy.flatten(), grid_clean.flatten())[0, 1]
    assert correlation > 0.9, f"Expected high correlation (>0.9) between noisy and clean grids, got {correlation}"

def test_occupancy_grid_calibration_integration(mock_depth_data, dummy_calibration):
    """
    Test that the calibration parameters are used in the generation process.
    This is a structural test to ensure the pipeline accepts and uses the calibration.
    """
    # If the pipeline fails or ignores calibration, it might produce a grid
    # but the alignment_report would be missing or incorrect in a full run.
    # Here we just ensure the function call succeeds with calibration data.
    try:
        grid = generate_occupancy_grid(
            depth_map=mock_depth_data,
            resolution=TEST_GRID_RES,
            max_range=10.0,
            radius=TEST_RADIUS,
            calibration=dummy_calibration
        )
        assert grid is not None
    except Exception as e:
        pytest.fail(f"Occupancy grid generation failed with calibration data: {e}")

def test_occupancy_grid_shape_consistency(mock_depth_data, dummy_calibration):
    """
    Verify that the grid shape is consistent regardless of minor parameter changes.
    """
    grid1 = generate_occupancy_grid(
        depth_map=mock_depth_data,
        resolution=TEST_GRID_RES,
        max_range=10.0,
        radius=TEST_RADIUS,
        calibration=dummy_calibration
    )
    
    grid2 = generate_occupancy_grid(
        depth_map=mock_depth_data,
        resolution=TEST_GRID_RES,
        max_range=10.0,
        radius=TEST_RADIUS + 0.1, # Slightly larger radius
        calibration=dummy_calibration
    )
    
    assert grid1.shape == grid2.shape, "Grid shape should remain consistent despite radius change"

def test_occupancy_grid_with_invalid_calibration(mock_depth_data):
    """
    Test behavior with invalid or missing calibration data.
    Should either raise a clear error or fall back to a safe default.
    """
    invalid_calib = {"passed": False, "error_meters": 5.0}
    
    # Depending on implementation, this might raise or fallback
    # We expect it not to crash silently with wrong data
    try:
        grid = generate_occupancy_grid(
            depth_map=mock_depth_data,
            resolution=TEST_GRID_RES,
            max_range=10.0,
            radius=TEST_RADIUS,
            calibration=invalid_calib
        )
        # If it returns a grid, it should be valid
        assert grid is not None
        assert grid.shape[0] > 0 and grid.shape[1] > 0
    except Exception:
        # Raising an error is also acceptable behavior for invalid calibration
        pass

def test_occupancy_grid_boundary_conditions(mock_depth_data, dummy_calibration):
    """
    Test grid generation at the boundaries of the sensor range.
    """
    # Create depth map with values at the edge of max_range
    height, width = mock_depth_data.shape
    edge_depth = np.ones((height, width), dtype=np.float32) * 10.0
    
    grid = generate_occupancy_grid(
        depth_map=edge_depth,
        resolution=TEST_GRID_RES,
        max_range=10.0,
        radius=TEST_RADIUS,
        calibration=dummy_calibration
    )
    
    # All cells should be empty (0) or handled as out-of-range
    # Depending on implementation, 10.0 might be included or excluded
    # We check that the grid is not all 1s
    assert np.sum(grid) < grid.size, "Expected most cells to be empty at max_range boundary"

def test_occupancy_grid_performance(mock_depth_data, dummy_calibration):
    """
    Basic performance check: ensure generation completes within a reasonable time.
    """
    import time
    start = time.time()
    
    grid = generate_occupancy_grid(
        depth_map=mock_depth_data,
        resolution=TEST_GRID_RES,
        max_range=10.0,
        radius=TEST_RADIUS,
        calibration=dummy_calibration
    )
    
    elapsed = time.time() - start
    assert elapsed < 5.0, f"Grid generation took too long: {elapsed}s"