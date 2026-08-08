import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os

from ingestion import (
    load_tracking_data, load_driving_data, sync_timestamps,
    handle_missing_frames, check_z_axis_completeness, compute_derivatives,
    calculate_energy_components, detect_non_stationary_segments
)
from config import load_config

@pytest.fixture
def sample_tracking_data():
    data = {
        'particle_id': [1, 1, 1, 1, 2, 2, 2],
        'timestamp': [0.0, 0.1, 0.2, 0.3, 0.0, 0.1, 0.2],
        'x': [0.0, 0.1, 0.2, 0.3, 0.0, 0.1, 0.2],
        'y': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'z': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'theta': [0.0, 0.1, 0.2, 0.3, 0.0, 0.1, 0.2],
        'material_type': ['steel', 'steel', 'steel', 'steel', 'polymer', 'polymer', 'polymer']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_driving_data():
    data = {
        'timestamp': [0.0, 0.1, 0.2, 0.3],
        'frequency': [10.0, 10.0, 10.0, 10.0],
        'amplitude': [1.0, 1.0, 1.0, 1.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def config():
    return {
        'material_properties': {
            'steel': {'mass': 0.001, 'radius': 0.005},
            'polymer': {'mass': 0.0005, 'radius': 0.005}
        },
        'vib_window_size': 5
    }

def test_load_tracking_data(tmp_path, sample_tracking_data):
    file_path = tmp_path / "tracking.csv"
    sample_tracking_data.to_csv(file_path, index=False)
    df = load_tracking_data([file_path])
    assert len(df) == 7
    assert 'x' in df.columns

def test_sync_timestamps(sample_tracking_data, sample_driving_data):
    merged = sync_timestamps(sample_tracking_data, sample_driving_data)
    assert 'frequency' in merged.columns
    assert len(merged) == len(sample_tracking_data)

def test_handle_missing_frames(sample_tracking_data):
    # Introduce a gap
    sample_tracking_data.loc[2, 'timestamp'] = 0.5
    df = handle_missing_frames(sample_tracking_data, max_gap=0.15)
    assert 'gap_flag' in df.columns
    assert df.loc[2, 'gap_flag'] == True

def test_check_z_axis_completeness(sample_tracking_data):
    df = check_z_axis_completeness(sample_tracking_data)
    assert 'pot_incomplete' in df.columns
    assert all(~df['pot_incomplete'])

def test_check_z_axis_incomplete(tmp_path):
    data = {
        'particle_id': [1, 1],
        'timestamp': [0.0, 0.1],
        'x': [0.0, 0.1],
        'y': [0.0, 0.0],
    }
    df = pd.DataFrame(data)
    df = check_z_axis_completeness(df)
    assert all(df['pot_incomplete'])

def test_compute_derivatives(sample_tracking_data):
    df = compute_derivatives(sample_tracking_data)
    assert 'v' in df.columns
    assert 'omega' in df.columns
    # Check velocity calculation for first particle
    v1 = np.sqrt(0.1**2 + 0.0**2 + 0.0**2) # dx=0.1, dt=0.1 -> vx=1.0? No, diff/dt
    # Actually: dx = 0.1, dt = 0.1 -> vx = 1.0
    # v = 1.0
    assert abs(df.loc[1, 'v'] - 1.0) < 0.01

def test_calculate_energy_components(sample_tracking_data, config):
    # Add frequency for sync
    sample_tracking_data['frequency'] = 10.0
    df = compute_derivatives(sample_tracking_data)
    df = calculate_energy_components(df, config)
    assert 'E_trans' in df.columns
    assert 'E_rot' in df.columns
    assert 'E_pot' in df.columns
    assert 'E_vib' in df.columns
    # Check E_trans = 0.5 * m * v^2
    # m_steel = 0.001, v = 1.0 -> E = 0.0005
    assert abs(df.loc[1, 'E_trans'] - 0.0005) < 1e-6

def test_detect_non_stationary_segments(sample_tracking_data):
    sample_tracking_data['frequency'] = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
    df = detect_non_stationary_segments(sample_tracking_data)
    assert 'chirp_flag' in df.columns
    assert all(~df['chirp_flag']) # Constant frequency should not be flagged
