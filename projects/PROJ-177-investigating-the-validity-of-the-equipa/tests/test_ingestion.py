"""
Tests for ingestion module, specifically T017 (velocity calculation).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import compute_velocities_angular_velocities, IngestionError

@pytest.fixture
def simple_particle_data():
    """
    Create a simple dataset with known positions and times to verify velocity calculation.
    Particle 1: moves 1m in 1s -> v = 1 m/s
    Particle 2: rotates 1 rad in 1s -> omega = 1 rad/s
    """
    data = {
        'particle_id': [1, 1, 1, 2, 2, 2],
        'timestamp': [0.0, 1.0, 2.0, 0.0, 1.0, 2.0],
        'x': [0.0, 1.0, 2.0, 0.0, 0.0, 0.0],
        'y': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'z': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'angle': [0.0, 1.0, 2.0, 0.0, 0.0, 0.0]
    }
    return pd.DataFrame(data)

def test_compute_linear_velocity(simple_particle_data):
    """Test that linear velocity is calculated correctly."""
    df = compute_velocities_angular_velocities(
        simple_particle_data,
        time_col='timestamp',
        pos_cols=['x', 'y', 'z'],
        orient_cols=['angle'],
        particle_col='particle_id'
    )
    
    # Particle 1: x goes 0->1->2 in 1s steps. v should be 1.0
    p1_rows = df[df['particle_id'] == 1]
    # First row is 0 (no diff), second and third should be 1.0
    # Note: diff reduces length by 1, so we have 2 velocity values for 3 points.
    # The assignment logic in compute_velocities_angular_velocities assigns to indices[1:]
    # So p1_rows['v'] at index 1 and 2 should be 1.0
    
    # Check non-zero velocities
    p1_v = p1_rows['v'].values
    assert p1_v[1] == pytest.approx(1.0, rel=1e-5)
    assert p1_v[2] == pytest.approx(1.0, rel=1e-5)

def test_compute_angular_velocity(simple_particle_data):
    """Test that angular velocity is calculated correctly."""
    df = compute_velocities_angular_velocities(
        simple_particle_data,
        time_col='timestamp',
        pos_cols=['x', 'y', 'z'],
        orient_cols=['angle'],
        particle_col='particle_id'
    )
    
    # Particle 2: angle is 0, 0, 0 -> omega should be 0
    p2_rows = df[df['particle_id'] == 2]
    assert all(p2_rows['omega'] == 0.0)
    
    # Particle 1: angle 0->1->2 -> omega should be 1.0
    p1_rows = df[df['particle_id'] == 1]
    # Check non-zero values
    p1_omega = p1_rows['omega'].values
    assert p1_omega[1] == pytest.approx(1.0, rel=1e-5)
    assert p1_omega[2] == pytest.approx(1.0, rel=1e-5)

def test_missing_columns_raises_error():
    """Test that missing position columns raises an error."""
    data = {
        'particle_id': [1, 1],
        'timestamp': [0.0, 1.0]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(IngestionError):
        compute_velocities_angular_velocities(df, pos_cols=['x', 'y', 'z'])

def test_missing_orientation_sets_zero():
    """Test that missing orientation columns sets omega to 0."""
    data = {
        'particle_id': [1, 1],
        'timestamp': [0.0, 1.0],
        'x': [0.0, 1.0],
        'y': [0.0, 0.0],
        'z': [0.0, 0.0]
    }
    df = pd.DataFrame(data)
    
    result = compute_velocities_angular_velocities(
        df,
        pos_cols=['x', 'y', 'z']
    )
    
    assert all(result['omega'] == 0.0)
    assert 'v' in result.columns
