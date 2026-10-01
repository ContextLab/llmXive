"""
Unit tests for preprocessing module.
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

from preprocess import (
    TrajectoryCorruptionError, MissingFramesError, NanValueError,
    RealDataFetchError, load_trajectory_data, build_neighbor_list,
    calculate_d2_min, extract_stress_strain, detect_yield_onset
)
from utils import set_seed

set_seed(42)

@pytest.fixture
def sample_positions():
    """Generate sample particle positions."""
    np.random.seed(42)
    return np.random.rand(10, 3) * 10  # 10 particles in 3D space

@pytest.fixture
def sample_stress():
    """Generate sample stress data."""
    np.random.seed(42)
    return np.random.rand(100, 6) * 10  # 100 timesteps, 6 stress components

@pytest.fixture
def sample_strain():
    """Generate sample strain data."""
    np.random.seed(42)
    return np.cumsum(np.random.rand(100) * 0.1)

def test_build_neighbor_list(sample_positions):
    """Test neighbor list construction."""
    cutoff = 5.0
    neighbor_list = build_neighbor_list(sample_positions, cutoff)
    
    assert len(neighbor_list) == len(sample_positions)
    for neighbors in neighbor_list:
        assert all(isinstance(n, int) for n in neighbors)
        assert all(0 <= n < len(sample_positions) for n in neighbors)

def test_calculate_d2_min(sample_positions):
    """Test D2_min calculation."""
    neighbor_list = build_neighbor_list(sample_positions, cutoff=5.0)
    d2_min = calculate_d2_min(sample_positions, neighbor_list)
    
    assert len(d2_min) == len(sample_positions)
    assert all(isinstance(d, (int, float)) for d in d2_min)
    assert not np.isnan(d2_min).any()
    assert not np.isinf(d2_min).any()

def test_extract_stress_strain(sample_stress):
    """Test stress-strain extraction."""
    stress_von_mises, strain = extract_stress_strain(sample_stress)
    
    assert len(stress_von_mises) == len(sample_stress)
    assert len(strain) == len(sample_stress)
    assert all(isinstance(s, (int, float)) for s in stress_von_mises)
    assert not np.isnan(stress_von_mises).any()

def test_detect_yield_onset(sample_stress, sample_strain):
    """Test yield onset detection."""
    # Create stress with a clear drop
    stress_with_drop = np.copy(sample_stress.mean(axis=1))
    stress_with_drop[50:] *= 0.8  # 20% drop at timestep 50
    
    yield_index = detect_yield_onset(stress_with_drop, sample_strain)
    
    assert yield_index is not None
    assert yield_index > 0
    assert yield_index < len(stress_with_drop)

def test_detect_yield_onset_no_drop(sample_stress, sample_strain):
    """Test yield detection when no drop occurs."""
    # Create stress without significant drops
    stress_no_drop = np.cumsum(np.abs(np.random.rand(len(sample_strain)) * 0.01))
    
    yield_index = detect_yield_onset(stress_no_drop, sample_strain)
    
    assert yield_index is None

def test_detect_yield_onset_multiple_drops(sample_stress, sample_strain):
    """Test that only the first significant drop is detected."""
    stress_with_multiple_drops = np.copy(sample_stress.mean(axis=1))
    stress_with_multiple_drops[30:] *= 0.8  # First drop at 30
    stress_with_multiple_drops[70:] *= 0.7  # Second drop at 70
    
    yield_index = detect_yield_onset(stress_with_multiple_drops, sample_strain)
    
    assert yield_index == 30  # Should detect only the first drop

def test_nan_value_detection(sample_positions):
    """Test that NaN values are properly detected."""
    nan_positions = sample_positions.copy()
    nan_positions[0, 0] = np.nan
    
    neighbor_list = build_neighbor_list(nan_positions, cutoff=5.0)
    
    with pytest.raises(NanValueError):
        calculate_d2_min(nan_positions, neighbor_list)

def test_particle_count_validation():
    """Test particle count validation."""
    # This would be tested with actual data loading
    # For now, test the logic
    assert True  # Placeholder for actual validation test
