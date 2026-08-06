"""
Tests for T019: Energy output generation and schema verification.
"""
import os
import json
import hashlib
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Mock the ingestion functions for testing
from ingestion import check_z_axis_completeness, calculate_energy_components, write_energy_output

def test_z_axis_incomplete_flagging():
    """Test that missing z-axis data is correctly flagged."""
    data = {
        'particle_id': [1, 1, 2, 2],
        'timestamp': [0.0, 1.0, 0.0, 1.0],
        'x': [0.1, 0.2, 0.3, 0.4],
        'y': [0.1, 0.2, 0.3, 0.4],
        # No z column
    }
    df = pd.DataFrame(data)
    config = {}
    
    result_df, status = check_z_axis_completeness(df)
    
    assert 'pot_incomplete' in result_df.columns
    assert all(result_df['pot_incomplete'] == True)
    assert status[1] == False
    assert status[2] == False

def test_z_axis_partial_incomplete():
    """Test that partial missing z-axis data is flagged."""
    data = {
        'particle_id': [1, 1, 2, 2],
        'timestamp': [0.0, 1.0, 0.0, 1.0],
        'x': [0.1, 0.2, 0.3, 0.4],
        'y': [0.1, 0.2, 0.3, 0.4],
        'z': [0.1, np.nan, 0.3, 0.4],  # Particle 1 has missing z
    }
    df = pd.DataFrame(data)
    config = {}
    
    result_df, status = check_z_axis_completeness(df)
    
    assert result_df.loc[0, 'pot_incomplete'] == True  # Particle 1
    assert result_df.loc[2, 'pot_incomplete'] == False  # Particle 2

def test_energy_calculation():
    """Test basic energy calculation formulas."""
    data = {
        'particle_id': [1, 1],
        'timestamp': [0.0, 1.0],
        'x': [0.0, 1.0],
        'y': [0.0, 0.0],
        'z': [0.0, 0.0],
        'v_x': [1.0, 1.0],
        'v_y': [0.0, 0.0],
        'v_z': [0.0, 0.0],
        'a_x': [0.0, 0.0],
        'a_y': [0.0, 0.0],
        'a_z': [0.0, 0.0],
        'omega': [1.0, 1.0],
        'pot_incomplete': [False, False],
        'mass': [2.0, 2.0],
        'inertia': [1.0, 1.0],
        'a_mag_sq': [0.0, 0.0],
    }
    df = pd.DataFrame(data)
    config = {'vibration_window_size': 5}
    
    result_df = calculate_energy_components(df, config)
    
    # E_trans = 0.5 * m * v^2 = 0.5 * 2.0 * 1.0 = 1.0
    assert result_df['E_trans'].iloc[0] == pytest.approx(1.0)
    
    # E_rot = 0.5 * I * omega^2 = 0.5 * 1.0 * 1.0 = 0.5
    assert result_df['E_rot'].iloc[0] == pytest.approx(0.5)
    
    # E_pot = m * g * z = 2.0 * 9.81 * 0.0 = 0.0
    assert result_df['E_pot'].iloc[0] == pytest.approx(0.0)

def test_energy_output_schema():
    """Test that output CSV has correct schema and hash is generated."""
    data = {
        'particle_id': [1, 2],
        'timestamp': [0.0, 1.0],
        'E_trans': [1.0, 2.0],
        'E_rot': [0.5, 1.0],
        'E_pot': [0.0, 0.1],
        'E_vib': [0.0, 0.0],
        'pot_incomplete': [False, True],
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_energy.csv')
        write_energy_output(df, output_path)
        
        # Check file exists
        assert os.path.exists(output_path)
        
        # Check hash file exists
        hash_path = output_path + '.hash'
        assert os.path.exists(hash_path)
        
        # Verify hash
        with open(output_path, 'rb') as f:
            content = f.read()
            expected_hash = hashlib.sha256(content).hexdigest()
        
        with open(hash_path, 'r') as f:
            actual_hash = f.read().strip()
        
        assert expected_hash == actual_hash
        
        # Verify schema
        loaded_df = pd.read_csv(output_path)
        expected_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
        assert list(loaded_df.columns) == expected_cols
        
        # Verify types
        assert loaded_df['particle_id'].dtype == 'int64'
        assert loaded_df['pot_incomplete'].dtype == 'bool'