"""
Tests for T024: bin_energy_data function.

Verifies correct binning by frequency and material type,
and proper error handling for missing/invalid input.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path
from stats import bin_energy_data, StatsError

@pytest.fixture
def sample_energy_data(tmp_path):
    """Create a temporary CSV with valid energy data."""
    data = {
        'particle_id': [1, 1, 2, 2, 3, 3],
        'timestamp': [0.0, 0.1, 0.0, 0.1, 0.0, 0.1],
        'E_trans': [1.0, 1.2, 2.0, 2.1, 1.5, 1.6],
        'E_rot': [0.1, 0.12, 0.2, 0.21, 0.15, 0.16],
        'E_pot': [0.5, 0.55, 0.8, 0.85, 0.6, 0.65],
        'E_vib': [0.01, 0.012, 0.02, 0.021, 0.015, 0.016],
        'pot_incomplete': [False, False, False, False, False, False],
        'driving_frequency': [10.0, 10.0, 20.0, 20.0, 10.0, 10.0],
        'material_type': ['steel', 'steel', 'polymer', 'polymer', 'steel', 'steel']
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "energy_samples.csv"
    df.to_csv(file_path, index=False)
    return file_path

def test_bin_energy_data_success(sample_energy_data):
    """Test successful binning of energy data."""
    bins = bin_energy_data(str(sample_energy_data))
    
    assert len(bins) == 2  # (10.0, steel), (20.0, polymer)
    
    # Check (10.0, steel)
    key1 = (10.0, 'steel')
    assert key1 in bins
    df1 = bins[key1]
    assert len(df1) == 4  # 4 samples
    assert set(df1['material_type']) == {'steel'}
    assert set(df1['driving_frequency']) == {10.0}
    
    # Check (20.0, polymer)
    key2 = (20.0, 'polymer')
    assert key2 in bins
    df2 = bins[key2]
    assert len(df2) == 2
    assert set(df2['material_type']) == {'polymer'}
    assert set(df2['driving_frequency']) == {20.0}

def test_bin_energy_data_missing_file(tmp_path):
    """Test error handling for missing input file."""
    non_existent = tmp_path / "non_existent.csv"
    with pytest.raises(FileNotFoundError) as exc_info:
        bin_energy_data(str(non_existent))
    assert "not found or invalid" in str(exc_info.value)

def test_bin_energy_data_missing_columns(tmp_path):
    """Test error handling for missing required columns."""
    data = {
        'particle_id': [1, 2],
        'E_trans': [1.0, 2.0]
        # Missing other required columns
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "invalid.csv"
    df.to_csv(file_path, index=False)
    
    with pytest.raises(StatsError) as exc_info:
        bin_energy_data(str(file_path))
    assert "Missing required columns" in str(exc_info.value)

def test_bin_energy_data_empty_file(tmp_path):
    """Test handling of empty file (header only)."""
    data = {
        'particle_id': [],
        'timestamp': [],
        'E_trans': [],
        'E_rot': [],
        'E_pot': [],
        'E_vib': [],
        'pot_incomplete': [],
        'driving_frequency': [],
        'material_type': []
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "empty.csv"
    df.to_csv(file_path, index=False)
    
    bins = bin_energy_data(str(file_path))
    assert len(bins) == 0  # No bins created