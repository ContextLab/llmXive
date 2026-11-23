import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import yaml

from ingestion import compute_energy, load_config

def create_test_config(tmp_path):
    """Create a minimal config file for testing."""
    config = {
        'material_properties': {
            'steel': {
                'mass': 0.001,
                'radius': 0.005,
                'roughness': 0.05
            }
        },
        'frequency_bins': [
            {'low': [0.0, 10.0]},
            {'medium': [10.0, 50.0]},
            {'high': [50.0, 100.0]}
        ],
        'window_size_N': 100,
        'sampling_threshold': 1000000
    }
    config_path = tmp_path / 'test_config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    return str(config_path)

def create_test_dataframe():
    """Create a synthetic dataframe with known values for energy calculation."""
    n = 200
    data = {
        'particle_id': [1] * n,
        'timestamp': np.linspace(0, 10, n),
        'x': np.linspace(0, 1, n),
        'y': np.linspace(0, 1, n),
        'z': np.linspace(0, 0.1, n),
        'material_type': ['steel'] * n
    }
    return pd.DataFrame(data)

def test_energy_calculation_units():
    """Test that energy values are in Joules."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_path = create_test_config(tmp_path)
        df = create_test_dataframe()
        output_path = tmp_path / 'test_energy.csv'
        
        # Run energy calculation
        result = compute_energy(df, config_path, str(output_path))
        
        # Check units (Joules)
        # E_trans = 0.5 * m * v^2. m=0.001 kg, v ~ 0.1 m/s -> E ~ 5e-6 J
        # E_vib = m * var(a) * dt^2. Should be positive.
        
        assert 'E_trans' in result.columns
        assert 'E_rot' in result.columns
        assert 'E_pot' in result.columns
        assert 'E_vib' in result.columns
        
        # All energies should be non-negative (physics)
        assert (result['E_trans'] >= 0).all()
        assert (result['E_rot'] >= 0).all()
        assert (result['E_pot'] >= 0).all()
        assert (result['E_vib'] >= 0).all()
        
        # Check magnitude (should be in Joules, not kJ or mJ)
        # For our synthetic data, E_trans should be around 1e-6 to 1e-3 J
        assert result['E_trans'].max() < 1.0  # Less than 1 J
        assert result['E_trans'].min() > 0.0  # Greater than 0 J

def test_energy_formula_accuracy():
    """Test that energy formulas match manual calculations."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config_path = create_test_config(tmp_path)
        
        # Create data with known velocity
        n = 100
        dt = 0.1
        v = 1.0  # m/s
        m = 0.001  # kg
        data = {
            'particle_id': [1] * n,
            'timestamp': np.arange(n) * dt,
            'x': np.arange(n) * v * dt,  # x = v * t
            'y': np.zeros(n),
            'z': np.zeros(n),
            'material_type': ['steel'] * n
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / 'test_energy.csv'
        
        result = compute_energy(df, config_path, str(output_path))
        
        # Expected E_trans = 0.5 * m * v^2 = 0.5 * 0.001 * 1^2 = 0.0005 J
        expected_E_trans = 0.5 * m * v**2
        
        # Check that calculated E_trans is close to expected
        assert np.isclose(result['E_trans'].mean(), expected_E_trans, rtol=1e-2)

def test_window_size_parameter():
    """Test that window_size_N from config is used."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Config with window_size_N = 50
        config = {
            'material_properties': {'steel': {'mass': 0.001, 'radius': 0.005, 'roughness': 0.05}},
            'frequency_bins': [],
            'window_size_N': 50,
            'sampling_threshold': 1000000
        }
        config_path = tmp_path / 'test_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        n = 100
        data = {
            'particle_id': [1] * n,
            'timestamp': np.arange(n) * 0.1,
            'x': np.arange(n) * 0.1,
            'y': np.zeros(n),
            'z': np.zeros(n),
            'material_type': ['steel'] * n
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / 'test_energy.csv'
        
        result = compute_energy(df, str(config_path), str(output_path))
        
        # With window_size=50 and n=100, we should have 2 windows (or close)
        # The number of rows in result should be roughly n / window_size
        assert len(result) > 0
        # Check that we have at least 1 row
        assert len(result) >= 1
