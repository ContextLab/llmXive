"""
Tests for the ingestion module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from ingestion import (
    load_tracking_data,
    load_driving_data,
    sync_timestamps,
    handle_missing_frames,
    compute_derivatives,
    calculate_energy_components,
    ingest_data,
    IngestionError,
    load_config,
)

from config import load_config


def test_load_tracking_data(tmp_path):
    """Test loading tracking data from CSV."""
    csv_file = tmp_path / "tracking.csv"
    data = "particle_id,timestamp,x,y,z,theta\n1,0.0,0.0,0.0,0.0,0.0\n1,0.1,0.1,0.0,0.0,0.1"
    csv_file.write_text(data)
    
    df = load_tracking_data(csv_file)
    assert len(df) == 2
    assert df['particle_id'].iloc[0] == 1
    assert df['timestamp'].iloc[0] == 0.0


def test_load_driving_data(tmp_path):
    """Test loading driving data from CSV."""
    csv_file = tmp_path / "driving.csv"
    data = "timestamp,frequency,amplitude\n0.0,10.0,1.0\n0.1,10.0,1.0"
    csv_file.write_text(data)
    
    df = load_driving_data(csv_file)
    assert len(df) == 2
    assert df['frequency'].iloc[0] == 10.0


def test_sync_timestamps():
    """Test syncing tracking and driving data."""
    tracking = pd.DataFrame({
        'timestamp': [0.0, 0.05, 0.1],
        'x': [0.0, 0.05, 0.1]
    })
    driving = pd.DataFrame({
        'timestamp': [0.0, 0.1],
        'frequency': [10.0, 20.0]
    })
    
    synced_tracking, synced_driving = sync_timestamps(tracking, driving)
    
    assert 'driving_frequency' in synced_tracking.columns
    # Interpolated values should be between 10 and 20
    assert all(10.0 <= f <= 20.0 for f in synced_tracking['driving_frequency'])


def test_handle_missing_frames():
    """Test interpolation of missing frames."""
    data = {
        'timestamp': [0.0, 0.2, 0.3],
        'x': [0.0, 0.2, 0.3]
    }
    df = pd.DataFrame(data)
    
    # Gap of 0.2 > tol=0.1, so should interpolate
    result = handle_missing_frames(df, tol=0.1)
    
    # Should have interpolated values (no NaN)
    assert result['x'].isna().sum() == 0


def test_compute_derivatives():
    """Test velocity calculation via finite differences."""
    data = {
        'timestamp': [0.0, 0.1, 0.2],
        'x': [0.0, 0.1, 0.2],
        'y': [0.0, 0.0, 0.0]
    }
    df = pd.DataFrame(data)
    
    result = compute_derivatives(df, ['x', 'y'])
    
    assert 'v_x' in result.columns
    assert 'v_y' in result.columns
    # Velocity should be ~1.0 for x
    assert abs(result['v_x'].iloc[1] - 1.0) < 0.01


def test_calculate_energy_components():
    """Test energy calculation formulas."""
    config = load_config()
    
    data = {
        'timestamp': [0.0, 0.1, 0.2],
        'x': [0.0, 0.1, 0.2],
        'y': [0.0, 0.0, 0.0],
        'z': [0.0, 0.0, 0.0],
        'theta': [0.0, 0.1, 0.2]
    }
    df = pd.DataFrame(data)
    
    # Add velocity manually to simplify test
    df['v_x'] = [0.0, 1.0, 1.0]
    df['v_y'] = 0.0
    df['v_z'] = 0.0
    
    result = calculate_energy_components(df, config)
    
    assert 'E_trans' in result.columns
    assert 'E_rot' in result.columns
    assert 'E_pot' in result.columns
    
    # E_trans = 0.5 * m * v^2. For v=1, E_trans = 0.5 * m
    mass = config['materials']['steel']['mass_density'] * (4/3 * 3.14159 * (0.0025**3))
    expected_E_trans = 0.5 * mass * (1.0 ** 2)
    
    # Check second row (v=1)
    assert abs(result['E_trans'].iloc[1] - expected_E_trans) < 1e-9

def test_missing_z_axis_handling():
    """Test that missing z-axis is handled correctly."""
    config = load_config()
    
    data = {
        'timestamp': [0.0, 0.1],
        'x': [0.0, 0.1],
        'y': [0.0, 0.0],
        'theta': [0.0, 0.1]
    }
    df = pd.DataFrame(data)
    df['v_x'] = [0.0, 1.0]
    df['v_y'] = 0.0
    
    result = calculate_energy_components(df, config)
    
    assert 'pot_incomplete' in result.columns
    assert result['pot_incomplete'].all()
    assert result['E_pot'].iloc[0] == 0.0
