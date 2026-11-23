"""
Tests for T019: Energy output generation and verification.

Verifies:
- energy_samples.csv is written with correct columns and types
- SHA-256 hash is generated and matches
- pot_incomplete flag is set correctly
"""
import os
import json
import tempfile
import shutil
import hashlib
import pytest
import pandas as pd
import numpy as np

from ingestion import ingest_data, write_energy_output, check_z_axis_completeness


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with mock tracking data."""
    tmpdir = tempfile.mkdtemp()
    data_dir = os.path.join(tmpdir, "data", "raw")
    os.makedirs(data_dir)

    # Create mock tracking CSV
    mock_data = {
        'particle_id': [1, 1, 1, 2, 2, 2],
        'timestamp': [0.0, 0.1, 0.2, 0.0, 0.1, 0.2],
        'x': [0.0, 0.1, 0.2, 1.0, 1.1, 1.2],
        'y': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'theta': [0.0, 0.1, 0.2, 0.0, 0.1, 0.2],
        # No 'z' column to test pot_incomplete
    }
    df = pd.DataFrame(mock_data)
    csv_path = os.path.join(data_dir, "tracking.csv")
    df.to_csv(csv_path, index=False)

    yield tmpdir, data_dir

    # Cleanup
    shutil.rmtree(tmpdir)


@pytest.fixture
def config_path(temp_data_dir):
    """Create a temporary config.yaml."""
    tmpdir, _ = temp_data_dir
    config_path = os.path.join(tmpdir, "data", "config.yaml")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    config_content = """
    materials:
      steel:
        mass: 0.001
        inertia: 1e-6
      polymer:
        mass: 0.0005
        inertia: 5e-7
    frequency_bins:
      - 10
      - 20
      - 30
    """
    with open(config_path, "w") as f:
        f.write(config_content)

    return config_path


def test_energy_output_columns(temp_data_dir, config_path):
    """Test that energy_samples.csv has the correct columns and types."""
    tmpdir, data_dir = temp_data_dir
    output_path = os.path.join(tmpdir, "data", "derived", "energy_samples.csv")
    hash_path = os.path.join(tmpdir, "artifacts", "energy_samples.hash")

    df = ingest_data(data_dir, config_path)
    write_energy_output(df, output_path, hash_path)

    # Verify file exists
    assert os.path.exists(output_path), "energy_samples.csv not found"
    assert os.path.exists(hash_path), "Hash file not found"

    # Load and verify columns
    result = pd.read_csv(output_path)
    expected_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
    assert list(result.columns) == expected_cols, f"Columns mismatch: {list(result.columns)} vs {expected_cols}"

    # Verify types
    assert result['particle_id'].dtype in ['int64', 'int32'], "particle_id should be int"
    assert result['timestamp'].dtype == 'float64', "timestamp should be float"
    assert result['E_trans'].dtype == 'float64', "E_trans should be float"
    assert result['E_rot'].dtype == 'float64', "E_rot should be float"
    assert result['E_pot'].dtype == 'float64', "E_pot should be float"
    assert result['E_vib'].dtype == 'float64', "E_vib should be float"
    assert result['pot_incomplete'].dtype == 'bool', "pot_incomplete should be bool"


def test_hash_verification(temp_data_dir, config_path):
    """Test that the generated hash matches the file content."""
    tmpdir, data_dir = temp_data_dir
    output_path = os.path.join(tmpdir, "data", "derived", "energy_samples.csv")
    hash_path = os.path.join(tmpdir, "artifacts", "energy_samples.hash")

    df = ingest_data(data_dir, config_path)
    write_energy_output(df, output_path, hash_path)

    # Compute expected hash
    sha256_hash = hashlib.sha256()
    with open(output_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    expected_hash = sha256_hash.hexdigest()

    # Read stored hash
    with open(hash_path, "r") as f:
        stored_hash = f.read().strip()

    assert expected_hash == stored_hash, f"Hash mismatch: {expected_hash} vs {stored_hash}"


def test_pot_incomplete_flag(temp_data_dir, config_path):
    """Test that pot_incomplete is True when z-axis is missing."""
    tmpdir, data_dir = temp_data_dir
    output_path = os.path.join(tmpdir, "data", "derived", "energy_samples.csv")
    hash_path = os.path.join(tmpdir, "artifacts", "energy_samples.hash")

    df = ingest_data(data_dir, config_path)
    write_energy_output(df, output_path, hash_path)

    result = pd.read_csv(output_path)

    # Since we didn't provide z, all should be True
    assert result['pot_incomplete'].all(), "pot_incomplete should be True for all when z is missing"


def test_pot_incomplete_with_z(temp_data_dir, config_path):
    """Test that pot_incomplete is False when z-axis is present."""
    tmpdir, data_dir = temp_data_dir
    output_path = os.path.join(tmpdir, "data", "derived", "energy_samples.csv")
    hash_path = os.path.join(tmpdir, "artifacts", "energy_samples.hash")

    # Add z column
    csv_path = os.path.join(data_dir, "tracking.csv")
    df = pd.read_csv(csv_path)
    df['z'] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    df.to_csv(csv_path, index=False)

    df_ingested = ingest_data(data_dir, config_path)
    write_energy_output(df_ingested, output_path, hash_path)

    result = pd.read_csv(output_path)

    # Since z is present, all should be False
    assert not result['pot_incomplete'].any(), "pot_incomplete should be False when z is present"
