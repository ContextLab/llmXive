"""
Tests for ingestion functions in code/ingestion.py.
"""
import pytest
import pandas as pd
import numpy as np
import os
from pathlib import Path
from ingestion import handle_missing_frames, check_z_axis_completeness, calculate_energy_components
from config import load_config

@pytest.fixture
def sample_tracking_data(tmp_path):
    """Create sample tracking CSV."""
    data = {
        'particle_id': [1, 1, 1, 2, 2, 2],
        'timestamp': [0.0, 0.1, 0.2, 0.0, 0.1, 0.2],
        'x': [0.1, 0.15, 0.2, 0.2, 0.25, 0.3],
        'y': [0.2, 0.25, 0.3, 0.3, 0.35, 0.4],
        'z': [0.5, 0.55, 0.6, 0.6, 0.65, 0.7],
        'theta': [0.0, 0.1, 0.2, 0.0, 0.1, 0.2],
        'material_type': ['steel', 'steel', 'steel', 'polymer', 'polymer', 'polymer']
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "tracking.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)

@pytest.fixture
def sample_config(tmp_path):
    """Create sample config.yaml."""
    config_data = """
    materials:
      steel:
        mass: 0.01
        inertia: 0.0001
        roughness: 0.5
      polymer:
        mass: 0.005
        inertia: 0.00005
        roughness: 0.2
    frequency_bins:
      - 5.0
      - 10.0
    gravity: 9.81
    """
    file_path = tmp_path / "config.yaml"
    file_path.write_text(config_data)
    return str(file_path)

def test_handle_missing_frames():
    """Test linear interpolation for missing frames."""
    data = {
        'timestamp': [0.0, 0.1, 0.2, 0.3, 0.4],
        'x': [0.0, 0.1, np.nan, 0.3, 0.4],
        'y': [0.0, 0.1, 0.2, 0.3, 0.4]
    }
    df = pd.DataFrame(data)
    result = handle_missing_frames(df)
    assert not result['x'].isna().any()
    assert result.loc[2, 'x'] == 0.2  # Interpolated value

def test_check_z_axis_completeness():
    """Test z-axis completeness flagging."""
    data = {
        'particle_id': [1, 1, 2, 2],
        'z': [0.5, np.nan, 0.6, 0.7]
    }
    df = pd.DataFrame(data)
    result = check_z_axis_completeness(df)
    assert 'pot_incomplete' in result.columns
    assert result.loc[1, 'pot_incomplete'] == True
    assert result.loc[0, 'pot_incomplete'] == False

def test_calculate_energy_components(sample_tracking_data, sample_config):
    """Test energy component calculation."""
    df = pd.read_csv(sample_tracking_data)
    # Add frequency column for sync (mock)
    df['frequency'] = 10.0
    
    result = calculate_energy_components(df, sample_config)
    assert 'E_trans' in result.columns
    assert 'E_rot' in result.columns
    assert 'E_pot' in result.columns
    assert 'E_vib' in result.columns
    # Check that energies are positive
    assert (result['E_trans'] >= 0).all()
    assert (result['E_rot'] >= 0).all()