import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import yaml

# Import functions to test
from ingestion import (
    handle_missing_frames,
    check_z_axis_completeness,
    calculate_energy_components,
    ingest_data
)

@pytest.fixture
def sample_tracking_data():
    """Generate sample tracking data for testing."""
    data = {
        'particle_id': [1, 1, 1, 2, 2, 2],
        'timestamp': [0.0, 0.1, 0.2, 0.0, 0.1, 0.2],
        'x': [0.0, 0.1, 0.2, 0.0, 0.05, 0.1],
        'y': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'z': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'theta': [0.0, 0.1, 0.2, 0.0, 0.05, 0.1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_config():
    """Generate sample config for testing."""
    return {
        'mass': 0.001,  # 1g
        'radius': 0.0025,  # 2.5mm
        'gravity': 9.81,
        'inertia': 0.0  # Will be derived
    }

def test_handle_missing_frames(sample_tracking_data):
    """Test linear interpolation of missing frames."""
    # Introduce a missing frame
    df_missing = sample_tracking_data.copy()
    df_missing = df_missing.drop(index=2)  # Remove row at t=0.2 for particle 1
    
    # Interpolate
    df_interp = handle_missing_frames(df_missing)
    
    # Check that x at t=0.2 for particle 1 is interpolated
    p1_t02 = df_interp[(df_interp['particle_id'] == 1) & (df_interp['timestamp'] == 0.2)]
    assert len(p1_t02) == 1
    # Should be interpolated between 0.1 and 0.2 -> 0.15
    assert abs(p1_t02['x'].values[0] - 0.15) < 1e-9

def test_check_z_axis_completeness_present(sample_tracking_data):
    """Test flagging when z-axis is present."""
    df, has_z = check_z_axis_completeness(sample_tracking_data)
    assert has_z is True
    assert all(df['pot_incomplete'] == False)

def test_check_z_axis_completeness_missing():
    """Test flagging when z-axis is missing."""
    data = {
        'particle_id': [1, 1],
        'timestamp': [0.0, 0.1],
        'x': [0.0, 0.1],
        'y': [0.0, 0.0],
        'theta': [0.0, 0.1]
    }
    df = pd.DataFrame(data)
    df, has_z = check_z_axis_completeness(df)
    assert has_z is False
    assert all(df['pot_incomplete'] == True)

def test_calculate_energy_components(sample_tracking_data, sample_config):
    """Test energy calculation formulas."""
    df = calculate_energy_components(sample_tracking_data, sample_config)
    
    # Check columns exist
    assert 'E_trans' in df.columns
    assert 'E_rot' in df.columns
    assert 'E_pot' in df.columns
    assert 'E_vib' in df.columns
    
    # E_trans = 0.5 * m * v^2
    # For particle 1, t=0.1: v = (0.1-0.0)/0.1 = 1.0 m/s
    # E_trans = 0.5 * 0.001 * 1.0^2 = 0.0005
    expected_E_trans = 0.5 * sample_config['mass'] * 1.0**2
    assert abs(df.loc[1, 'E_trans'] - expected_E_trans) < 1e-9

def test_ingest_data_full_pipeline(sample_tracking_data, sample_config):
    """Test full ingestion pipeline produces correct output file."""
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        tracking_file = Path(tmpdir) / "tracking.csv"
        driving_file = Path(tmpdir) / "driving.csv"
        config_file = Path(tmpdir) / "config.yaml"
        output_file = Path(tmpdir) / "energy_samples.csv"
        
        # Write inputs
        sample_tracking_data.to_csv(tracking_file, index=False)
        pd.DataFrame({'timestamp': [0.0, 0.1, 0.2], 'amplitude': [1.0, 1.0, 1.0]}).to_csv(driving_file, index=False)
        
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        # Run ingestion
        ingest_data(
            tracking_files=[str(tracking_file)],
            driving_files=[str(driving_file)],
            config=sample_config,
            output_path=str(output_file)
        )
        
        # Verify output
        assert output_file.exists()
        output_df = pd.read_csv(output_file)
        
        # Check required columns
        required_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
        for col in required_cols:
            assert col in output_df.columns
        
        # Check pot_incomplete is False (z-axis present)
        assert all(output_df['pot_incomplete'] == False)
