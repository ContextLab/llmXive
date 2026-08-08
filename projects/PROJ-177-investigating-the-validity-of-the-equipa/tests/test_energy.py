"""
Unit tests for energy calculation logic in T019b.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingestion import calculate_energy_components, compute_derivatives
from config import load_config

# Create a minimal mock config for testing
MOCK_CONFIG = {
    'mass': 1.0,
    'inertia': 0.5,
    'vib_window': 5,
    'data_dir': 'data/raw'
}

def test_translational_energy():
    """Verify E_trans = 0.5 * m * v^2"""
    df = pd.DataFrame({
        'vx': [3.0, 4.0],
        'vy': [0.0, 0.0],
        'vz': [0.0, 0.0],
        'omega_x': [0.0, 0.0],
        'omega_y': [0.0, 0.0],
        'omega_z': [0.0, 0.0],
        'ax': [0.0, 0.0],
        'ay': [0.0, 0.0],
        'az': [0.0, 0.0],
        'x': [0.0, 0.0],
        'y': [0.0, 0.0],
        'z': [0.0, 0.0],
        'timestamp': [0.0, 1.0],
        'particle_id': [1, 1]
    })
    
    # Mock config function to return our mock
    import ingestion
    original_load = ingestion.load_config
    ingestion.load_config = lambda x: MOCK_CONFIG
    
    try:
        result = calculate_energy_components(df, 'dummy.yaml')
        
        # E_trans = 0.5 * 1.0 * (3^2) = 4.5
        # E_trans = 0.5 * 1.0 * (4^2) = 8.0
        assert np.isclose(result['E_trans'].iloc[0], 4.5)
        assert np.isclose(result['E_trans'].iloc[1], 8.0)
    finally:
        ingestion.load_config = original_load

def test_rotational_energy():
    """Verify E_rot = 0.5 * I * omega^2"""
    df = pd.DataFrame({
        'vx': [0.0, 0.0],
        'vy': [0.0, 0.0],
        'vz': [0.0, 0.0],
        'omega_x': [2.0, 0.0],
        'omega_y': [0.0, 3.0],
        'omega_z': [0.0, 0.0],
        'ax': [0.0, 0.0],
        'ay': [0.0, 0.0],
        'az': [0.0, 0.0],
        'x': [0.0, 0.0],
        'y': [0.0, 0.0],
        'z': [0.0, 0.0],
        'timestamp': [0.0, 1.0],
        'particle_id': [1, 1]
    })
    
    import ingestion
    original_load = ingestion.load_config
    ingestion.load_config = lambda x: MOCK_CONFIG
    
    try:
        result = calculate_energy_components(df, 'dummy.yaml')
        
        # I = 0.5
        # Row 0: 0.5 * 0.5 * (2^2) = 1.0
        # Row 1: 0.5 * 0.5 * (3^2) = 2.25
        assert np.isclose(result['E_rot'].iloc[0], 1.0)
        assert np.isclose(result['E_rot'].iloc[1], 2.25)
    finally:
        ingestion.load_config = original_load

def test_potential_energy():
    """Verify E_pot = m * g * z"""
    df = pd.DataFrame({
        'vx': [0.0, 0.0],
        'vy': [0.0, 0.0],
        'vz': [0.0, 0.0],
        'omega_x': [0.0, 0.0],
        'omega_y': [0.0, 0.0],
        'omega_z': [0.0, 0.0],
        'ax': [0.0, 0.0],
        'ay': [0.0, 0.0],
        'az': [0.0, 0.0],
        'x': [0.0, 0.0],
        'y': [0.0, 0.0],
        'z': [10.0, 20.0],
        'timestamp': [0.0, 1.0],
        'particle_id': [1, 1]
    })
    
    import ingestion
    original_load = ingestion.load_config
    # Override g in config? Or assume 9.81 hardcoded.
    # Our implementation uses hardcoded 9.81.
    ingestion.load_config = lambda x: MOCK_CONFIG
    
    try:
        result = calculate_energy_components(df, 'dummy.yaml')
        
        # m=1, g=9.81
        # Row 0: 1 * 9.81 * 10 = 98.1
        # Row 1: 1 * 9.81 * 20 = 196.2
        assert np.isclose(result['E_pot'].iloc[0], 98.1)
        assert np.isclose(result['E_pot'].iloc[1], 196.2)
    finally:
        ingestion.load_config = original_load

def test_vibrational_energy():
    """Verify E_vib = m * var(a) over window"""
    # Create a sequence where we can calculate variance manually
    # a = [0, 0, 0, 0, 10] -> var = 16
    # a = [0, 0, 0, 0, 0] -> var = 0
    a_vals = [0.0, 0.0, 0.0, 0.0, 10.0]
    df = pd.DataFrame({
        'vx': [0.0]*5,
        'vy': [0.0]*5,
        'vz': [0.0]*5,
        'omega_x': [0.0]*5,
        'omega_y': [0.0]*5,
        'omega_z': [0.0]*5,
        'ax': a_vals,
        'ay': [0.0]*5,
        'az': [0.0]*5,
        'x': [0.0]*5,
        'y': [0.0]*5,
        'z': [0.0]*5,
        'timestamp': [0.0, 1.0, 2.0, 3.0, 4.0],
        'particle_id': [1]*5
    })
    
    import ingestion
    original_load = ingestion.load_config
    ingestion.load_config = lambda x: MOCK_CONFIG
    
    try:
        result = calculate_energy_components(df, 'dummy.yaml')
        
        # Window size 5.
        # Row 4 (last): window is [0,0,0,0,10]. Variance of this sample.
        # Variance of [0,0,0,0,10] = sum((x-mean)^2)/(N-1) ? Pandas default ddof=1.
        # Mean = 2.
        # (0-2)^2 * 4 + (10-2)^2 = 4*4 + 64 = 16 + 64 = 80.
        # Var = 80 / 4 = 20.
        # E_vib = m * var = 1.0 * 20 = 20.0
        
        # Check the last row
        last_row = result['E_vib'].iloc[-1]
        assert np.isclose(last_row, 20.0)
    finally:
        ingestion.load_config = original_load

def test_derivatives():
    """Verify acceleration calculation"""
    df = pd.DataFrame({
        'vx': [0.0, 10.0, 20.0],
        'vy': [0.0, 0.0, 0.0],
        'vz': [0.0, 0.0, 0.0],
        'timestamp': [0.0, 1.0, 2.0]
    })
    
    result = compute_derivatives(df)
    
    # dt = 1.0
    # ax = (10-0)/1 = 10
    # ax = (20-10)/1 = 10
    assert np.isclose(result['ax'].iloc[1], 10.0)
    assert np.isclose(result['ax'].iloc[2], 10.0)
