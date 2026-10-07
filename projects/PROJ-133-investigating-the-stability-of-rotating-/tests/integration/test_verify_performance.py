"""
Integration tests for the performance verification script.

These tests verify that the verification script:
1. Runs without errors
2. Produces valid output
3. Correctly identifies constraint violations
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from simulation.verify_performance import (
    get_peak_memory_mb,
    run_single_verification_run,
    run_verification_run
)

def test_get_peak_memory_mb():
    """Test that peak memory function returns a positive value."""
    memory = get_peak_memory_mb()
    assert memory > 0, "Peak memory should be positive"
    assert isinstance(memory, float), "Memory should be a float"

def test_single_verification_run_small_grid():
    """Test a single verification run with 64x64 grid."""
    result = run_single_verification_run(
        grid_resolution=64,
        omega=0.5,
        epsilon_dd=0.5,
        N=10000,
        max_steps=10
    )

    assert result['success'] is True, f"Run failed: {result['error']}"
    assert result['grid_resolution'] == 64
    assert result['omega'] == 0.5
    assert result['epsilon_dd'] == 0.5
    assert result['N'] == 10000
    assert result['runtime_seconds'] > 0
    assert result['peak_memory_mb'] > 0

def test_single_verification_run_large_grid():
    """Test a single verification run with 256x256 grid."""
    result = run_single_verification_run(
        grid_resolution=256,
        omega=0.5,
        epsilon_dd=0.5,
        N=10000,
        max_steps=5
    )

    assert result['success'] is True, f"Run failed: {result['error']}"
    assert result['grid_resolution'] == 256
    assert result['runtime_seconds'] > 0
    assert result['peak_memory_mb'] > 0

def test_verification_run_full_grid():
    """Test the full grid verification run."""
    results = run_verification_run(full_grid=True)

    assert len(results) > 0, "Should have at least one result"
    for result in results:
        assert result['success'] is True, f"Run failed: {result['error']}"
        assert result['grid_resolution'] == 64

def test_verification_run_large_grid():
    """Test the large grid verification run."""
    results = run_verification_run(full_grid=False)

    assert len(results) > 0, "Should have at least one result"
    for result in results:
        assert result['success'] is True, f"Run failed: {result['error']}"
        assert result['grid_resolution'] == 256

def test_output_file_creation():
    """Test that the verification script creates output files."""
    # Run verification
    results = run_verification_run(full_grid=False)

    # Check that output file exists
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'aggregated'
    output_path = output_dir / 'performance_verification_results.json'

    assert output_path.exists(), "Output file should exist"

    # Verify JSON content
    with open(output_path, 'r') as f:
        data = json.load(f)

    assert isinstance(data, list), "Output should be a list"
    assert len(data) > 0, "Output should contain results"

    # Clean up
    if output_path.exists():
        os.remove(output_path)

@pytest.mark.parametrize("grid_size,omega,epsilon_dd,N", [
    (64, 0.5, 0.5, 10000),
    (64, 0.8, 1.0, 50000),
    (256, 0.5, 0.5, 10000),
    (256, 0.2, 0.0, 20000),
])
def test_various_parameter_sets(grid_size, omega, epsilon_dd, N):
    """Test verification runs with various parameter combinations."""
    result = run_single_verification_run(
        grid_resolution=grid_size,
        omega=omega,
        epsilon_dd=epsilon_dd,
        N=N,
        max_steps=5
    )

    assert result['success'] is True
    assert result['grid_resolution'] == grid_size
    assert result['omega'] == omega
    assert result['epsilon_dd'] == epsilon_dd
    assert result['N'] == N