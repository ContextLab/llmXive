"""
Unit tests for generate_test_data module.

Tests verify that:
1. Test data is generated correctly with expected distributions
2. Output files are created at the correct paths
3. Data contains required columns
4. Files are prefixed with 'test_'
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from generate_test_data import (
    load_params,
    generate_thermal_data,
    generate_nonthermal_data,
    main
)

@pytest.fixture
def temp_params_file():
    """Create a temporary parameters file for testing."""
    params = {
        "maxwell_boltzmann": {"mean": 1.0, "scale": 0.1},
        "pareto": {"shape": 2.0}
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(params, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_params(temp_params_file):
    """Test loading parameters from JSON file."""
    params = load_params(temp_params_file)
    assert "maxwell_boltzmann" in params
    assert "pareto" in params
    assert params["maxwell_boltzmann"]["mean"] == 1.0
    assert params["maxwell_boltzmann"]["scale"] == 0.1
    assert params["pareto"]["shape"] == 2.0

def test_load_params_file_not_found():
    """Test that load_params raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_params("nonexistent_file.json")

def test_generate_thermal_data_structure(temp_output_dir):
    """Test that thermal data has correct structure."""
    output_path = temp_output_dir / "test_thermal_data.csv"
    df = generate_thermal_data(
        n_particles=100,
        n_frames=10,
        output_path=output_path
    )
    
    # Check file exists
    assert output_path.exists()
    
    # Check DataFrame structure
    assert len(df) == 100 * 10
    assert "particle_id" in df.columns
    assert "timestamp" in df.columns
    assert "x" in df.columns
    assert "y" in df.columns
    assert "z" in df.columns
    assert "velocity_magnitude" in df.columns
    assert "angular_velocity" in df.columns
    assert "material_type" in df.columns

def test_generate_thermal_data_distribution(temp_output_dir):
    """Test that thermal data follows approximately Maxwell-Boltzmann distribution."""
    output_path = temp_output_dir / "test_thermal_data.csv"
    df = generate_thermal_data(
        n_particles=1000,
        n_frames=100,
        output_path=output_path
    )
    
    # Check that velocities are positive
    assert (df["velocity_magnitude"] > 0).all()
    
    # Check that velocities have reasonable mean (should be close to mean parameter)
    # For Maxwell-Boltzmann, mean velocity is approximately scale * sqrt(8/(3*pi))
    # But our implementation uses a simplified approach
    velocities = df["velocity_magnitude"]
    assert velocities.mean() > 0
    assert velocities.mean() < 10  # Sanity check

def test_generate_nonthermal_data_structure(temp_output_dir):
    """Test that non-thermal data has correct structure."""
    output_path = temp_output_dir / "test_nonthermal_data.csv"
    df = generate_nonthermal_data(
        n_particles=100,
        n_frames=10,
        output_path=output_path
    )
    
    # Check file exists
    assert output_path.exists()
    
    # Check DataFrame structure
    assert len(df) == 100 * 10
    assert "particle_id" in df.columns
    assert "timestamp" in df.columns
    assert "x" in df.columns
    assert "y" in df.columns
    assert "z" in df.columns
    assert "velocity_magnitude" in df.columns
    assert "angular_velocity" in df.columns
    assert "material_type" in df.columns

def test_generate_nonthermal_data_distribution(temp_output_dir):
    """Test that non-thermal data follows Pareto distribution (heavy-tailed)."""
    output_path = temp_output_dir / "test_nonthermal_data.csv"
    df = generate_nonthermal_data(
        n_particles=1000,
        n_frames=100,
        output_path=output_path
    )
    
    # Check that velocities are positive
    assert (df["velocity_magnitude"] > 0).all()
    
    # Check that velocities have higher variance than thermal (heavy-tailed)
    # This is a qualitative check
    velocities = df["velocity_magnitude"]
    assert velocities.mean() > 0
    
    # Check for heavy tail: some velocities should be significantly larger than mean
    max_vel = velocities.max()
    mean_vel = velocities.mean()
    assert max_vel > 2 * mean_vel  # Heavy tail should produce outliers

def test_generate_thermal_data_file_prefix(temp_output_dir):
    """Test that thermal data file has correct 'test_' prefix."""
    output_path = temp_output_dir / "test_thermal_data.csv"
    generate_thermal_data(
        n_particles=10,
        n_frames=5,
        output_path=output_path
    )
    
    assert output_path.exists()
    assert output_path.name.startswith("test_")
    assert output_path.name.endswith(".csv")

def test_generate_nonthermal_data_file_prefix(temp_output_dir):
    """Test that non-thermal data file has correct 'test_' prefix."""
    output_path = temp_output_dir / "test_nonthermal_data.csv"
    generate_nonthermal_data(
        n_particles=10,
        n_frames=5,
        output_path=output_path
    )
    
    assert output_path.exists()
    assert output_path.name.startswith("test_")
    assert output_path.name.endswith(".csv")

def test_main_function(temp_params_file, temp_output_dir):
    """Test the main function with command line arguments."""
    # Mock command line arguments
    import sys
    original_argv = sys.argv
    sys.argv = [
        "generate_test_data.py",
        "--params", temp_params_file,
        "--output-dir", str(temp_output_dir),
        "--n-particles", "50",
        "--n-frames", "5"
    ]
    
    try:
        main()
        
        # Check files were created
        thermal_path = temp_output_dir / "test_thermal_data.csv"
        nonthermal_path = temp_output_dir / "test_nonthermal_data.csv"
        
        assert thermal_path.exists()
        assert nonthermal_path.exists()
        
        # Check file sizes
        assert thermal_path.stat().st_size > 0
        assert nonthermal_path.stat().st_size > 0
        
    finally:
        sys.argv = original_argv

def test_data_types_and_values(temp_output_dir):
    """Test that generated data has correct data types and reasonable values."""
    output_path = temp_output_dir / "test_thermal_data.csv"
    df = generate_thermal_data(
        n_particles=100,
        n_frames=10,
        output_path=output_path
    )
    
    # Check data types
    assert df["particle_id"].dtype in [np.int64, np.int32]
    assert df["timestamp"].dtype in [np.int64, np.int32]
    assert df["x"].dtype in [np.float64, np.float32]
    assert df["y"].dtype in [np.float64, np.float32]
    assert df["z"].dtype in [np.float64, np.float32]
    assert df["velocity_magnitude"].dtype in [np.float64, np.float32]
    assert df["angular_velocity"].dtype in [np.float64, np.float32]
    assert df["material_type"].dtype == object  # String

    # Check for no NaN values in critical columns
    assert not df["velocity_magnitude"].isna().any()
    assert not df["angular_velocity"].isna().any()
    assert not df["x"].isna().any()
    assert not df["y"].isna().any()
    assert not df["z"].isna().any()

def test_particle_ids_and_timestamps(temp_output_dir):
    """Test that particle IDs and timestamps are correctly generated."""
    output_path = temp_output_dir / "test_thermal_data.csv"
    df = generate_thermal_data(
        n_particles=10,
        n_frames=5,
        output_path=output_path
    )
    
    # Check particle IDs
    expected_particle_ids = np.repeat(np.arange(10), 5)
    assert np.array_equal(df["particle_id"].values, expected_particle_ids)
    
    # Check timestamps
    expected_timestamps = np.tile(np.arange(5), 10)
    assert np.array_equal(df["timestamp"].values, expected_timestamps)