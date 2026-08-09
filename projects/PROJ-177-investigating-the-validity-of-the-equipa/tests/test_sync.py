import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingestion import (
    load_driving_data,
    load_particle_tracking_data,
    sync_particle_and_driving_data,
    IngestionError
)

@pytest.fixture
def sample_driving_data():
    """Create sample driving signal data."""
    data = {
        'timestamp': [1000, 2000, 3000, 4000, 5000],
        'frequency': [50.0, 50.5, 51.0, 51.5, 52.0],
        'amplitude': [1.0, 1.1, 1.2, 1.3, 1.4]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_particle_data():
    """Create sample particle tracking data."""
    data = {
        'timestamp': [1000, 1500, 2000, 2500, 3000, 3500, 4000],
        'particle_id': [1, 1, 1, 1, 1, 1, 1],
        'x': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
        'y': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
        'z': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_driving_csv(sample_driving_data):
    """Create a temporary driving CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_driving_data.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_particle_csv(sample_particle_data):
    """Create a temporary particle tracking CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_particle_data.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_driving_data_valid(temp_driving_csv, sample_driving_data):
    """Test loading valid driving data."""
    df = load_driving_data(temp_driving_csv)
    assert len(df) == len(sample_driving_data)
    assert 'timestamp' in df.columns
    assert 'frequency' in df.columns
    assert 'amplitude' in df.columns
    assert df['timestamp'].iloc[0] == 1000

def test_load_driving_data_missing_file():
    """Test loading from a non-existent file raises error."""
    with pytest.raises(IngestionError, match="not found"):
        load_driving_data("/nonexistent/path.csv")

def test_load_driving_data_empty():
    """Test loading empty file raises error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("timestamp,frequency,amplitude\n")
        temp_path = f.name
    try:
        with pytest.raises(IngestionError, match="empty"):
            load_driving_data(temp_path)
    finally:
        os.unlink(temp_path)

def test_load_particle_tracking_valid(temp_particle_csv, sample_particle_data):
    """Test loading valid particle tracking data."""
    df = load_particle_tracking_data(temp_particle_csv)
    assert len(df) == len(sample_particle_data)
    assert 'timestamp' in df.columns
    assert 'particle_id' in df.columns
    assert 'x' in df.columns

def test_load_particle_tracking_missing_file():
    """Test loading particle tracking from non-existent file raises error."""
    with pytest.raises(IngestionError, match="not found"):
        load_particle_tracking_data("/nonexistent/path.csv")

def test_sync_data_basic(sample_driving_data, sample_particle_data):
    """Test basic synchronization of particle and driving data."""
    synced = sync_particle_and_driving_data(sample_particle_data, sample_driving_data, tolerance_seconds=1000)
    
    # Should have all particle rows
    assert len(synced) == len(sample_particle_data)
    
    # Should have driving columns merged
    assert 'frequency' in synced.columns
    assert 'amplitude' in synced.columns
    
    # First particle (ts=1000) should match first driving (ts=1000)
    assert synced.loc[0, 'frequency'] == 50.0
    assert synced.loc[0, 'amplitude'] == 1.0

def test_sync_data_with_tolerance(sample_driving_data, sample_particle_data):
    """Test synchronization with tight tolerance."""
    # Tight tolerance: 100 units
    synced = sync_particle_and_driving_data(sample_particle_data, sample_driving_data, tolerance_seconds=100)
    
    # Particle at 1500 should not match any driving signal (closest is 1000 or 2000, both > 100 away)
    # So frequency should be NaN for that row
    assert pd.isna(synced.loc[1, 'frequency'])

def test_sync_data_empty_driving(sample_particle_data):
    """Test synchronization with empty driving data raises error."""
    empty_driving = pd.DataFrame(columns=['timestamp', 'frequency', 'amplitude'])
    with pytest.raises(IngestionError, match="Driving signal data is empty"):
        sync_particle_and_driving_data(sample_particle_data, empty_driving)

def test_sync_data_empty_particle(sample_driving_data):
    """Test synchronization with empty particle data raises error."""
    empty_particle = pd.DataFrame(columns=['timestamp', 'particle_id'])
    with pytest.raises(IngestionError, match="Particle tracking data is empty"):
        sync_particle_and_driving_data(empty_particle, sample_driving_data)

def test_sync_data_column_preservation(sample_driving_data, sample_particle_data):
    """Test that particle columns are preserved after sync."""
    synced = sync_particle_and_driving_data(sample_particle_data, sample_driving_data)
    
    # Original particle columns should still exist
    assert 'particle_id' in synced.columns
    assert 'x' in synced.columns
    assert 'y' in synced.columns
    assert 'z' in synced.columns
    
    # Values should be unchanged
    assert synced['x'].tolist() == sample_particle_data['x'].tolist()