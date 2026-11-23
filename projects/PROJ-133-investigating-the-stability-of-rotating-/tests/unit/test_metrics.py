import pytest
import numpy as np
import os
import json
import tempfile
from pathlib import Path

# Import the functions to test
from analysis.metrics import (
    calculate_vortex_density,
    calculate_radial_variance,
    calculate_structure_factor_sharpness,
    calculate_all_metrics,
    process_snapshot_file
)
from analysis.vortex_detector import detect_vortices_phase_winding

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def synthetic_vortex_snapshot(temp_dir):
    """
    Generate synthetic data with a known single vortex at the center.
    """
    n = 64
    x = np.linspace(-1, 1, n)
    y = np.linspace(-1, 1, n)
    X, Y = np.meshgrid(x, y)
    
    # Create a phase field with a vortex at (0,0)
    # Phase = atan2(y, x)
    phase = np.atan2(Y, X)
    
    # Create a density field: Gaussian centered at 0
    sigma = 0.1
    density = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
    
    # Save files
    density_path = os.path.join(temp_dir, "test_density.npy")
    phase_path = os.path.join(temp_dir, "test_phase.npy")
    
    np.save(density_path, density)
    np.save(phase_path, phase)
    
    return density_path, phase_path, 2.0/n  # Approx grid spacing for domain [-1, 1]

@pytest.fixture
def synthetic_flat_snapshot(temp_dir):
    """
    Generate synthetic data with no vortices (constant phase, flat density).
    """
    n = 64
    x = np.linspace(-1, 1, n)
    y = np.linspace(-1, 1, n)
    X, Y = np.meshgrid(x, y)
    
    phase = np.zeros_like(X)
    density = np.ones_like(X) * 0.1 # Constant density
    
    density_path = os.path.join(temp_dir, "flat_density.npy")
    phase_path = os.path.join(temp_dir, "flat_phase.npy")
    
    np.save(density_path, density)
    np.save(phase_path, phase)
    
    return density_path, phase_path, 2.0/n

def test_vortex_density_single_vortex(synthetic_vortex_snapshot):
    """Test that a single vortex is detected and density is calculated correctly."""
    density_path, phase_path, spacing = synthetic_vortex_snapshot
    
    density = np.load(density_path)
    phase = np.load(phase_path)
    
    density_val, count = calculate_vortex_density(density, phase, spacing)
    
    # We expect exactly 1 vortex
    assert count == 1, f"Expected 1 vortex, got {count}"
    assert density_val > 0, "Vortex density should be positive"

def test_vortex_density_zero_vortices(synthetic_flat_snapshot):
    """Test that zero vortices are detected in a flat field."""
    density_path, phase_path, spacing = synthetic_flat_snapshot
    
    density = np.load(density_path)
    phase = np.load(phase_path)
    
    density_val, count = calculate_vortex_density(density, phase, spacing)
    
    assert count == 0, f"Expected 0 vortices, got {count}"
    assert density_val == 0.0, "Vortex density should be 0 for flat field"

def test_radial_variance_flat_distribution(synthetic_flat_snapshot):
    """Test radial variance for a flat distribution."""
    density_path, phase_path, spacing = synthetic_flat_snapshot
    density = np.load(density_path)
    
    var = calculate_radial_variance(density)
    # For a flat distribution over a square domain, variance is non-zero but finite
    assert var >= 0, "Variance must be non-negative"
    assert var < 100, "Variance should be within reasonable bounds for this domain"

def test_radial_variance_concentrated(synthetic_vortex_snapshot):
    """Test radial variance for a concentrated Gaussian."""
    density_path, phase_path, spacing = synthetic_vortex_snapshot
    density = np.load(density_path)
    
    var = calculate_radial_variance(density)
    # A Gaussian with sigma=0.1 should have a very small variance
    assert var < 0.1, "Variance should be small for concentrated Gaussian"

def test_structure_factor_sharpness_flat(synthetic_flat_snapshot):
    """Test structure factor sharpness for a flat (constant) density."""
    density_path, phase_path, spacing = synthetic_flat_snapshot
    density = np.load(density_path)
    
    sharpness = calculate_structure_factor_sharpness(density)
    # A constant density has a delta peak in k-space (only DC component)
    # This should be the sharpest possible (1.0)
    assert sharpness == 1.0, "Constant density should have max sharpness (1.0)"

def test_structure_factor_sharpness_random(temp_dir):
    """Test structure factor sharpness for a noisy field."""
    n = 64
    np.random.seed(42)
    density = np.random.random((n, n))
    
    density_path = os.path.join(temp_dir, "noise_density.npy")
    np.save(density_path, density)
    
    sharpness = calculate_structure_factor_sharpness(density)
    # Random noise should have low sharpness (broad spectrum)
    assert sharpness < 0.5, "Random noise should have low sharpness"

def test_calculate_all_metrics(synthetic_vortex_snapshot, temp_dir):
    """Integration test for calculate_all_metrics."""
    density_path, phase_path, spacing = synthetic_vortex_snapshot
    
    metrics = calculate_all_metrics(density_path, phase_path, spacing)
    
    assert metrics.vortex_count == 1
    assert metrics.vortex_density > 0
    assert metrics.radial_variance >= 0
    assert 0 <= metrics.structure_factor_sharpness <= 1
    assert metrics.grid_size == (64, 64)

def test_process_snapshot_file(synthetic_vortex_snapshot, temp_dir):
    """Test the full processing pipeline saving to JSON."""
    density_path, phase_path, spacing = synthetic_vortex_snapshot
    output_path = os.path.join(temp_dir, "metrics.json")
    
    # This function expects a base name or path, we pass the density path
    # and it will look for corresponding phase file.
    # To make this robust, we pass the base path logic as implemented.
    # The function implementation looks for <path>_density.npy and <path>_phase.npy
    # So we pass the directory and base name logic.
    
    # Adjusting test to match the specific implementation of process_snapshot_file
    # which expects: snapshot_path -> constructs density/phase paths
    # Let's pass the directory and a base name that matches the files
    base_dir = os.path.dirname(density_path)
    base_name = "test" # matches test_density.npy
    
    # Re-implementing the call to match the function's expected input signature
    # The function takes snapshot_path as a string.
    # In the implementation:
    # density_file = os.path.join(dir_name, f"{base_name}_density.npy")
    # So if we pass "test", it looks for "test_density.npy" in current dir.
    # We need to ensure the files are accessible.
    
    # Let's use the absolute paths directly by modifying the test to match the function's logic
    # or just call calculate_all_metrics directly as process_snapshot_file is a wrapper.
    # The function `process_snapshot_file` in the implementation above:
    # expects `snapshot_path` to be the base name (e.g. "test") and assumes files are in the same dir.
    # OR if it's a full path, it extracts the dir.
    
    # Let's test the logic:
    # If snapshot_path = "/tmp/xyz/test", it looks for "/tmp/xyz/test_density.npy"
    # Our files are at "/tmp/xyz/test_density.npy" and "/tmp/xyz/test_phase.npy"
    
    # So we pass the path without extension
    snapshot_base = os.path.join(base_dir, base_name)
    
    metric_obj = process_snapshot_file(snapshot_base, output_path, spacing)
    
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data["vortex_count"] == 1
    assert "vortex_density" in data
    assert "radial_variance" in data
    assert "structure_factor_sharpness" in data