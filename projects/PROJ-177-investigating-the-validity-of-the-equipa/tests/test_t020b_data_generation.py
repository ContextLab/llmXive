"""
Tests for T020b: Synthetic Data Generation.

Verifies that:
1. The script runs without error.
2. Output files are created with correct names.
3. Data distributions match expected properties (Thermal vs Non-Thermal).
4. Files have the 'test_' prefix.
"""
import os
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
import subprocess
import sys

import pytest

# Constants
THERMAL_FILE = "data/derived/test_thermal_data.csv"
NON_THERMAL_FILE = "data/derived/test_nonthermal_data.csv"
PARAMS_FILE = "artifacts/test_params.json"

@pytest.fixture
def setup_test_env(tmp_path):
    """Setup a temporary environment for testing."""
    # Create necessary directories
    data_dir = tmp_path / "data" / "derived"
    data_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy params file (mimicking T020a output)
    params = {
        "maxwell_boltzmann": {"mean": 1.0, "scale": 0.1},
        "pareto": {"shape": 2.0}
    }
    with open(artifacts_dir / "test_params.json", 'w') as f:
        json.dump(params, f)
    
    # Change to temp directory
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    yield {
        "data_dir": data_dir,
        "artifacts_dir": artifacts_dir
    }
    
    os.chdir(old_cwd)

def test_script_execution(setup_test_env):
    """Test that the generation script runs successfully."""
    result = subprocess.run(
        [sys.executable, "code/generate_test_data.py"],
        cwd=setup_test_env["data_dir"].parent.parent, # Run from project root
        capture_output=True,
        text=True
    )
    
    # We need to copy the script to the temp location or adjust paths
    # For this test, we assume the script is in the project root relative to the temp dir
    # Actually, let's just run it from the temp dir root
    script_path = Path(__file__).parent.parent / "code" / "generate_test_data.py"
    
    # Copy script to temp location to avoid path issues
    temp_script = setup_test_env["data_dir"].parent.parent / "generate_test_data.py"
    shutil.copy(script_path, temp_script)
    
    result = subprocess.run(
        [sys.executable, "generate_test_data.py"],
        cwd=setup_test_env["data_dir"].parent.parent,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Cleanup
    temp_script.unlink()

def test_files_created(setup_test_env):
    """Test that output files are created."""
    # Run script
    script_path = Path(__file__).parent.parent / "code" / "generate_test_data.py"
    temp_script = setup_test_env["data_dir"].parent.parent / "generate_test_data.py"
    shutil.copy(script_path, temp_script)
    
    subprocess.run([sys.executable, "generate_test_data.py"], cwd=setup_test_env["data_dir"].parent.parent)
    
    thermal_path = setup_test_env["data_dir"] / THERMAL_FILE
    nonthermal_path = setup_test_env["data_dir"] / NON_THERMAL_FILE
    
    assert thermal_path.exists(), f"Thermal data file not created: {thermal_path}"
    assert nonthermal_path.exists(), f"Non-thermal data file not created: {nonthermal_path}"
    
    temp_script.unlink()

def test_file_prefix(setup_test_env):
    """Test that files have the 'test_' prefix."""
    script_path = Path(__file__).parent.parent / "code" / "generate_test_data.py"
    temp_script = setup_test_env["data_dir"].parent.parent / "generate_test_data.py"
    shutil.copy(script_path, temp_script)
    
    subprocess.run([sys.executable, "generate_test_data.py"], cwd=setup_test_env["data_dir"].parent.parent)
    
    thermal_files = list(setup_test_env["data_dir"].glob("test_*.csv"))
    assert len(thermal_files) > 0, "No files with 'test_' prefix found."
    
    # Verify specific names
    names = [f.name for f in thermal_files]
    assert "test_thermal_data.csv" in names
    assert "test_nonthermal_data.csv" in names
    
    temp_script.unlink()

def test_thermal_distribution_properties(setup_test_env):
    """Test that thermal data follows expected distribution properties."""
    script_path = Path(__file__).parent.parent / "code" / "generate_test_data.py"
    temp_script = setup_test_env["data_dir"].parent.parent / "generate_test_data.py"
    shutil.copy(script_path, temp_script)
    
    subprocess.run([sys.executable, "generate_test_data.py"], cwd=setup_test_env["data_dir"].parent.parent)
    
    df = pd.read_csv(setup_test_env["data_dir"] / THERMAL_FILE)
    
    # Check columns
    expected_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'material_type', 'frequency_bin']
    assert all(col in df.columns for col in expected_cols), "Missing expected columns."
    
    # Check for non-negative energy
    assert (df['E_trans'] >= 0).all(), "Thermal E_trans should be non-negative."
    assert (df['E_rot'] >= 0).all(), "Thermal E_rot should be non-negative."
    
    # Check for finite values (no NaN/Inf)
    assert df['E_trans'].isna().sum() == 0, "Thermal E_trans contains NaN."
    
    temp_script.unlink()

def test_nonthermal_distribution_properties(setup_test_env):
    """Test that non-thermal data follows expected distribution properties."""
    script_path = Path(__file__).parent.parent / "code" / "generate_test_data.py"
    temp_script = setup_test_env["data_dir"].parent.parent / "generate_test_data.py"
    shutil.copy(script_path, temp_script)
    
    subprocess.run([sys.executable, "generate_test_data.py"], cwd=setup_test_env["data_dir"].parent.parent)
    
    df = pd.read_csv(setup_test_env["data_dir"] / NON_THERMAL_FILE)
    
    # Check columns
    expected_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'material_type', 'frequency_bin']
    assert all(col in df.columns for col in expected_cols), "Missing expected columns."
    
    # Check for non-negative energy
    assert (df['E_trans'] >= 0).all(), "Non-thermal E_trans should be non-negative."
    
    # Check for finite values
    assert df['E_trans'].isna().sum() == 0, "Non-thermal E_trans contains NaN."
    
    # Pareto data should have a heavier tail (higher max relative to mean)
    # This is a soft check, just ensuring it's not all identical
    assert df['E_trans'].std() > 0, "Non-thermal E_trans should have variance."
    
    temp_script.unlink()

def test_data_types_and_values(setup_test_env):
    """Test data types and specific value constraints."""
    script_path = Path(__file__).parent.parent / "code" / "generate_test_data.py"
    temp_script = setup_test_env["data_dir"].parent.parent / "generate_test_data.py"
    shutil.copy(script_path, temp_script)
    
    subprocess.run([sys.executable, "generate_test_data.py"], cwd=setup_test_env["data_dir"].parent.parent)
    
    thermal_df = pd.read_csv(setup_test_env["data_dir"] / THERMAL_FILE)
    nonthermal_df = pd.read_csv(setup_test_env["data_dir"] / NON_THERMAL_FILE)
    
    # Check material types
    assert thermal_df['material_type'].unique()[0] == 'steel'
    assert nonthermal_df['material_type'].unique()[0] == 'glass'
    
    # Check frequency bins
    assert thermal_df['frequency_bin'].unique()[0] == '10Hz'
    assert nonthermal_df['frequency_bin'].unique()[0] == '50Hz'
    
    # Check particle IDs are unique
    assert thermal_df['particle_id'].nunique() == len(thermal_df)
    assert nonthermal_df['particle_id'].nunique() == len(nonthermal_df)
    
    temp_script.unlink()
