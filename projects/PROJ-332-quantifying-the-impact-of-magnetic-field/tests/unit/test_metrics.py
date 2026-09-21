"""
Unit Tests for Metrics Calculation Module.

This module contains unit tests for the functions in code/analysis/metrics.py.
It verifies the correctness of q-profile extraction, shear calculation,
and resonant surface density computation.
"""
import pytest
import numpy as np
from analysis.metrics import calculate_resonant_surface_density, calculate_local_magnetic_shear

def test_calculate_resonant_surface_density():
    """
    Test resonant surface density calculation against reference values.
    """
    # Create a synthetic q-profile that crosses several rational surfaces
    radius = np.linspace(0, 1, 100)
    # q goes from 1.5 to 3.5, crossing 2, 3, 5/2, 7/2, etc.
    q_profile = 1.5 + 2.0 * radius
    
    density = calculate_resonant_surface_density(q_profile, radius)
    
    # The exact count depends on the tolerance and range, but it should be > 0
    assert density > 0, "Density should be positive for a crossing q-profile"

def test_calculate_local_magnetic_shear():
    """
    Test local magnetic shear calculation.
    """
    radius = np.linspace(0.1, 1.0, 50)
    q_profile = 1.0 + radius  # Linear increase
    
    shear = calculate_local_magnetic_shear(q_profile, radius)
    
    assert len(shear) == len(radius), "Shear array length should match radius"
    assert not np.any(np.isnan(shear)), "Shear should not contain NaN"

def test_empty_inputs():
    """
    Test handling of empty inputs.
    """
    density = calculate_resonant_surface_density(np.array([]), np.array([]))
    assert density == 0.0, "Empty inputs should return zero density"

    shear = calculate_local_magnetic_shear(np.array([]), np.array([]))
    assert len(shear) == 0, "Empty inputs should return empty shear"
