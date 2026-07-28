"""
Unit tests for energy calculation formulas.
"""

import pytest
import numpy as np
import pandas as pd

from config import load_config
from ingestion import calculate_energy_components


def test_translational_energy_formula():
    """Verify E_trans = 0.5 * m * v^2."""
    config = load_config()
    mass = config['materials']['steel']['mass_density'] * (4/3 * 3.14159 * (0.0025**3))
    
    # Create a single particle with known velocity
    data = {
        'timestamp': [0.0],
        'x': [0.0],
        'y': [0.0],
        'z': [0.0],
        'theta': [0.0],
        'v_x': [2.0],
        'v_y': [0.0],
        'v_z': [0.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_energy_components(df, config)
    
    expected_E_trans = 0.5 * mass * (2.0 ** 2)
    assert abs(result['E_trans'].iloc[0] - expected_E_trans) < 1e-9


def test_rotational_energy_formula():
    """Verify E_rot = 0.5 * I * omega^2."""
    config = load_config()
    inertia = config['constants']['moment_of_inertia_factor'] * \
              (config['materials']['steel']['mass_density'] * (4/3 * 3.14159 * (0.0025**3))) * \
              (0.0025 ** 2)
    
    # Create data with known angular velocity
    data = {
        'timestamp': [0.0, 0.1],
        'x': [0.0, 0.0],
        'y': [0.0, 0.0],
        'z': [0.0, 0.0],
        'theta': [0.0, 0.2], # omega = 0.2 / 0.1 = 2.0
        'v_x': [0.0, 0.0],
        'v_y': [0.0, 0.0],
        'v_z': [0.0, 0.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_energy_components(df, config)
    
    # omega = 2.0
    omega = 2.0
    expected_E_rot = 0.5 * inertia * (omega ** 2)
    
    # Check second row
    assert abs(result['E_rot'].iloc[1] - expected_E_rot) < 1e-9


def test_potential_energy_formula():
    """Verify E_pot = m * g * z."""
    config = load_config()
    mass = config['materials']['steel']['mass_density'] * (4/3 * 3.14159 * (0.0025**3))
    g = config['constants']['g']
    
    data = {
        'timestamp': [0.0],
        'x': [0.0],
        'y': [0.0],
        'z': [10.0],
        'theta': [0.0],
        'v_x': [0.0],
        'v_y': [0.0],
        'v_z': [0.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_energy_components(df, config)
    
    expected_E_pot = mass * g * 10.0
    assert abs(result['E_pot'].iloc[0] - expected_E_pot) < 1e-9


def test_energy_with_known_inputs():
    """Test all energy components with a fully defined input."""
    config = load_config()
    mass = config['materials']['steel']['mass_density'] * (4/3 * 3.14159 * (0.0025**3))
    inertia = config['constants']['moment_of_inertia_factor'] * mass * (0.0025 ** 2)
    g = config['constants']['g']
    
    v = 3.0
    omega = 4.0
    z = 5.0
    
    # Construct data with pre-calculated velocity and theta steps
    data = {
        'timestamp': [0.0, 0.1],
        'x': [0.0, 0.3],
        'y': [0.0, 0.0],
        'z': [0.0, z],
        'theta': [0.0, omega * 0.1],
        'v_x': [0.0, v],
        'v_y': [0.0, 0.0],
        'v_z': [0.0, 0.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_energy_components(df, config)
    
    # Expected values
    exp_E_trans = 0.5 * mass * (v ** 2)
    exp_E_rot = 0.5 * inertia * (omega ** 2)
    exp_E_pot = mass * g * z
    
    # Check second row
    assert abs(result['E_trans'].iloc[1] - exp_E_trans) < 1e-9
    assert abs(result['E_rot'].iloc[1] - exp_E_rot) < 1e-9
    assert abs(result['E_pot'].iloc[1] - exp_E_pot) < 1e-9
