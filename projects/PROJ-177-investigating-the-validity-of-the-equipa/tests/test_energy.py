import pytest
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

# Import the function to test
from ingestion import compute_energy, IngestionError

@pytest.fixture
def sample_config(tmp_path):
    """Create a temporary config file for testing."""
    config_data = {
        "mass": 0.01,  # 10 grams in kg
        "inertia": 0.000002, # Moment of inertia
        "material_type": "steel",
        "frequency_bins": [1.0, 5.0, 10.0]
    }
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, 'w') as f:
        import yaml
        yaml.dump(config_data, f)
    return str(config_path)

@pytest.fixture
def sample_velocity_data():
    """Create a DataFrame with pre-calculated velocities."""
    data = {
        'timestamp': [0.0, 1.0, 2.0, 3.0, 4.0],
        'particle_id': [1, 1, 1, 1, 1],
        'x': [0.0, 1.0, 2.0, 3.0, 4.0],
        'y': [0.0, 0.0, 0.0, 0.0, 0.0],
        'z': [1.0, 1.1, 1.2, 1.3, 1.4],
        'v': [1.0, 1.0, 1.0, 1.0, 1.0], # Constant speed
        'omega': [2.0, 2.0, 2.0, 2.0, 2.0], # Constant angular velocity
        'v_z': [0.1, 0.1, 0.1, 0.1, 0.1] # Constant vertical velocity
    }
    return pd.DataFrame(data)

def test_translational_energy(sample_config, sample_velocity_data):
    """Test E_trans = 0.5 * m * v^2"""
    mass = 0.01
    v = 1.0
    expected_E_trans = 0.5 * mass * (v ** 2)
    
    df = compute_energy(sample_velocity_data, sample_config, window_size_N=3)
    
    # Check that E_trans is calculated correctly
    assert np.allclose(df['E_trans'], expected_E_trans)

def test_rotational_energy(sample_config, sample_velocity_data):
    """Test E_rot = 0.5 * I * omega^2"""
    inertia = 0.000002
    omega = 2.0
    expected_E_rot = 0.5 * inertia * (omega ** 2)
    
    df = compute_energy(sample_velocity_data, sample_config, window_size_N=3)
    
    assert np.allclose(df['E_rot'], expected_E_rot)

def test_potential_energy(sample_config, sample_velocity_data):
    """Test E_pot = m * g * z"""
    mass = 0.01
    g = 9.81
    # z values: 1.0, 1.1, 1.2, 1.3, 1.4
    expected_E_pot = mass * g * np.array([1.0, 1.1, 1.2, 1.3, 1.4])
    
    df = compute_energy(sample_velocity_data, sample_config, window_size_N=3)
    
    assert np.allclose(df['E_pot'], expected_E_pot)

def test_vibrational_energy(sample_config, sample_velocity_data):
    """Test E_vib = 0.5 * m * sigma_{v,z}^2"""
    mass = 0.01
    # v_z is constant [0.1, 0.1, 0.1, 0.1, 0.1]
    # Variance of a constant sequence is 0
    expected_v_z_var = 0.0
    expected_E_vib = 0.5 * mass * expected_v_z_var
    
    df = compute_energy(sample_velocity_data, sample_config, window_size_N=3)
    
    # Since variance of constant is 0, E_vib should be 0 (or very close due to floating point)
    assert np.allclose(df['E_vib'], expected_E_vib, atol=1e-9)

def test_vibrational_energy_with_variance(sample_config, sample_velocity_data):
    """Test E_vib with varying v_z."""
    # Modify v_z to have variance
    data = sample_velocity_data.copy()
    data['v_z'] = [0.0, 0.1, 0.2, 0.3, 0.4]
    
    # Calculate variance manually for a window of 3
    # Window 1: [0.0] -> var=NaN (min_periods=1 usually gives 0 or NaN, pandas default is NaN for n<2)
    # Window 2: [0.0, 0.1] -> var=0.005
    # Window 3: [0.0, 0.1, 0.2] -> var=0.01
    # Window 4: [0.1, 0.2, 0.3] -> var=0.01
    # Window 5: [0.2, 0.3, 0.4] -> var=0.01
    
    # Let's just check that it's non-zero and proportional to variance
    df = compute_energy(data, sample_config, window_size_N=3)
    
    mass = 0.01
    # Check that E_vib is not zero for rows where variance is expected to be non-zero
    # Row 1 (index 1) has v_z [0.0, 0.1] -> var=0.005 -> E_vib = 0.5 * 0.01 * 0.005 = 0.000025
    # Row 2 (index 2) has v_z [0.0, 0.1, 0.2] -> var=0.01 -> E_vib = 0.5 * 0.01 * 0.01 = 0.00005
    
    # Note: pandas rolling var with min_periods=1 gives NaN for n=1, 0 for n=1? 
    # Actually, var(n=1) is NaN. var(n=2) is computed.
    # So index 0 might be NaN or 0 depending on implementation.
    # We check indices 1 and 2.
    
    assert not np.isnan(df.loc[1, 'E_vib'])
    assert df.loc[1, 'E_vib'] > 0
    assert df.loc[2, 'E_vib'] > 0

def test_missing_velocity_column(sample_config):
    """Test that IngestionError is raised if 'v' is missing."""
    data = {
        'timestamp': [0.0, 1.0],
        'x': [0.0, 1.0],
        'z': [1.0, 1.0]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(IngestionError, match="missing 'v' column"):
        compute_energy(df, sample_config, window_size_N=3)

def test_missing_inertia_config(tmp_path):
    """Test that IngestionError is raised if inertia is missing from config."""
    config_data = {
        "mass": 0.01,
        "material_type": "steel",
        "frequency_bins": [1.0]
    }
    config_path = tmp_path / "bad_config.yaml"
    with open(config_path, 'w') as f:
        import yaml
        yaml.dump(config_data, f)
    
    data = {
        'timestamp': [0.0],
        'v': [1.0],
        'omega': [1.0],
        'z': [1.0],
        'v_z': [0.0]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(IngestionError, match="must specify 'inertia'"):
        compute_energy(df, str(config_path), window_size_N=3)
