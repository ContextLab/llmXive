"""
Unit tests for Thomas-Fermi initial condition generator.
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from simulation.initial_conditions import (
    calculate_tf_radius,
    generate_tf_profile,
    generate_initial_condition
)
from config.grid_config import get_grid_resolution, get_domain_size

@pytest.fixture
def mock_config():
    """Mock grid configuration for tests."""
    with patch('simulation.initial_conditions.get_grid_resolution') as mock_res, \
         patch('simulation.initial_conditions.get_domain_size') as mock_size, \
         patch('simulation.initial_conditions.load_physical_params') as mock_phys:
        
        mock_res.return_value = (64, 64)
        mock_size.return_value = (20.0e-6, 20.0e-6) # 20 microns
        mock_phys.return_value = {
            'a_s': 5.3e-9,
            'm': 1.44e-25,
            'omega_r': 2 * np.pi * 100,
            'omega_z': 2 * np.pi * 200
        }
        yield mock_res, mock_size, mock_phys


def test_calculate_tf_radius():
    """Test Thomas-Fermi radius calculation."""
    N = 10000
    a_s = 5.3e-9
    m = 1.44e-25
    omega_r = 2 * np.pi * 100
    omega_z = 2 * np.pi * 200
    epsilon_dd = 0.0

    R_r, R_z = calculate_tf_radius(N, a_s, m, omega_r, omega_z, epsilon_dd)

    # Radii should be positive
    assert R_r > 0
    assert R_z > 0
    # For anisotropic trap (omega_z > omega_r), R_z should be smaller
    assert R_z < R_r


def test_generate_tf_profile(mock_config):
    """Test density profile generation."""
    R_r = 5e-6
    R_z = 2.5e-6
    Nx, Ny = 64, 64
    L = 20e-6
    x = np.linspace(-L/2, L/2, Nx)
    y = np.linspace(-L/2, L/2, Ny)
    N = 10000
    epsilon_dd = 0.0

    density = generate_tf_profile(R_r, R_z, x, y, N, epsilon_dd)

    assert density.shape == (Nx, Ny)
    assert np.all(density >= 0)
    # Max density should be at the center
    center_idx = Nx // 2
    assert density[center_idx, center_idx] == density.max()
    # Density should be zero at boundaries
    assert density[0, 0] == 0.0
    assert density[-1, -1] == 0.0


def test_generate_initial_condition(mock_config):
    """Test full initial condition generation."""
    N = 10000
    omega = 0.5 * 2 * np.pi * 100
    epsilon_dd = 0.0

    result = generate_initial_condition(N, omega, epsilon_dd)

    assert 'psi' in result
    assert 'density' in result
    assert 'R_r' in result
    assert 'R_z' in result
    assert 'grid_r' in result
    assert 'grid_z' in result

    psi = result['psi']
    density = result['density']

    assert psi.shape == density.shape
    assert np.allclose(np.abs(psi)**2, density, atol=1e-10)

    # Check normalization (approximate)
    dx = result['grid_r'][1] - result['grid_r'][0]
    dy = result['grid_z'][1] - result['grid_z'][0]
    integral = np.sum(np.abs(psi)**2) * dx * dy
    # Allow some tolerance due to discretization and TF approximation
    assert np.isclose(integral, N, rtol=0.1)


def test_initial_condition_with_seed(mock_config):
    """Test initial condition with random seed perturbation."""
    N = 10000
    omega = 0.8 * 2 * np.pi * 100 # High rotation
    epsilon_dd = 0.0
    seed = 42

    result = generate_initial_condition(N, omega, epsilon_dd, seed=seed)
    
    psi = result['psi']
    density = result['density']

    # With seed, there should be some phase variation (if perturbation added)
    # Even if perturbation is small, the phase should not be exactly zero everywhere
    # But our implementation only adds perturbation if omega > 0.5 * omega_r
    # and seed is provided.
    # Check that density is still normalized
    dx = result['grid_r'][1] - result['grid_r'][0]
    dy = result['grid_z'][1] - result['grid_z'][0]
    integral = np.sum(np.abs(psi)**2) * dx * dy
    assert np.isclose(integral, N, rtol=0.1)