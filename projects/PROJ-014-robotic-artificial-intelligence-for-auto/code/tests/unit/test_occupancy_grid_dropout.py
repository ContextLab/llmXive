import pytest
import numpy as np
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from data.pipeline import OccupancyGridGenerator, OccupancyGridConfig

@pytest.fixture
def valid_depth_data():
    """Create valid depth data with obstacles"""
    depth = np.ones((200, 200), dtype=np.float32) * 5.0  # 5 meters everywhere
    depth[90:110, 90:110] = 0.3  # Obstacle in center
    return depth

@pytest.fixture
def empty_depth_data():
    """Create empty depth data (LiDAR dropout scenario)"""
    depth = np.zeros((200, 200), dtype=np.float32)
    return depth

@pytest.fixture
def sparse_depth_data():
    """Create sparse depth data (near dropout)"""
    depth = np.ones((200, 200), dtype=np.float32) * 5.0
    depth[100:105, 100:105] = 0.3  # Tiny valid region
    return depth

@pytest.fixture
def generator():
    config = OccupancyGridConfig(
        resolution=0.1,
        max_distance=10.0,
        obstacle_radius=0.5,
        noise_std=0.0,  # Disable noise for deterministic tests
        dropout_threshold=0.01
    )
    return OccupancyGridGenerator(config)

def test_occupancy_grid_with_valid_data(generator, valid_depth_data):
    """Test that valid data produces a grid with obstacles detected"""
    grid = generator.generate(valid_depth_data)
    
    assert grid is not None
    assert grid.shape[0] == grid.shape[1]
    assert grid.dtype == np.uint8
    
    # Should have detected the obstacle (at least one occupied cell)
    assert np.sum(grid) > 0, "Valid obstacle data should result in occupied grid cells"

def test_occupancy_grid_with_empty_data_fallback(generator, empty_depth_data):
    """Test that empty depth data triggers fallback to safe empty grid"""
    grid = generator.generate(empty_depth_data)
    
    assert grid is not None
    assert grid.shape[0] == grid.shape[1]
    assert grid.dtype == np.uint8
    
    # Should be all zeros (safe empty grid)
    assert np.sum(grid) == 0, "Empty depth data should result in empty grid"

def test_occupancy_grid_with_sparse_data_fallback(generator, sparse_depth_data):
    """Test that sparse data below threshold triggers fallback"""
    grid = generator.generate(sparse_depth_data)
    
    assert grid is not None
    assert grid.shape[0] == grid.shape[1]
    assert grid.dtype == np.uint8
    
    # Should be all zeros (safe empty grid) because valid ratio is too low
    assert np.sum(grid) == 0, "Sparse depth data below threshold should result in empty grid"

def test_occupancy_grid_handles_none_input(generator):
    """Test that None input triggers fallback"""
    grid = generator.generate(None)
    
    assert grid is not None
    assert grid.shape[0] == grid.shape[1]
    assert np.sum(grid) == 0

def test_occupancy_grid_handles_empty_array_input(generator):
    """Test that empty array input triggers fallback"""
    grid = generator.generate(np.array([]))
    
    assert grid is not None
    assert grid.shape[0] == grid.shape[1]
    assert np.sum(grid) == 0

def test_dropout_threshold_configurable():
    """Test that dropout threshold is respected"""
    # High threshold
    config_high = OccupancyGridConfig(
        resolution=0.1,
        max_distance=10.0,
        obstacle_radius=0.5,
        noise_std=0.0,
        dropout_threshold=0.5  # 50% valid data required
    )
    generator_high = OccupancyGridGenerator(config_high)
    
    # 30% valid data should trigger dropout
    depth_30_percent = np.ones((100, 100), dtype=np.float32) * 5.0
    depth_30_percent[:30, :] = 0.3  # 30% valid
    
    grid = generator_high.generate(depth_30_percent)
    assert np.sum(grid) == 0, "30% valid data with 50% threshold should trigger fallback"
    
    # Low threshold
    config_low = OccupancyGridConfig(
        resolution=0.1,
        max_distance=10.0,
        obstacle_radius=0.5,
        noise_std=0.0,
        dropout_threshold=0.01  # 1% valid data required
    )
    generator_low = OccupancyGridGenerator(config_low)
    
    # 30% valid data should NOT trigger dropout
    grid = generator_low.generate(depth_30_percent)
    assert np.sum(grid) > 0, "30% valid data with 1% threshold should NOT trigger fallback"

def test_logging_on_dropout(empty_depth_data, generator, caplog):
    """Test that a warning is logged when dropout occurs"""
    with caplog.at_level(logging.WARNING):
        grid = generator.generate(empty_depth_data)
        
    assert "LiDAR dropout detected" in caplog.text
    assert "Substituting safe empty grid" in caplog.text
