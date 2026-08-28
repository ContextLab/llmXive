import pytest
import pandas as pd
import json
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate_test_data import load_params, generate_thermal_data, generate_nonthermal_data

@pytest.fixture
def temp_params_file(tmp_path):
    """Create a temporary params file matching T020a output."""
    params = {
        "maxwell_boltzmann": {
            "mean": 1.0,
            "scale": 0.1
        },
        "pareto": {
            "shape": 2.0
        }
    }
    params_path = tmp_path / "test_params.json"
    with open(params_path, 'w') as f:
        json.dump(params, f)
    return str(params_path)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "data" / "derived"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def test_load_params(temp_params_file):
    """Test that parameters are loaded correctly."""
    params = load_params(temp_params_file)
    assert params['maxwell_boltzmann']['mean'] == 1.0
    assert params['maxwell_boltzmann']['scale'] == 0.1
    assert params['pareto']['shape'] == 2.0

def test_load_params_file_not_found():
    """Test that FileNotFoundError is raised for missing params."""
    with pytest.raises(FileNotFoundError):
        load_params('nonexistent.json')

def test_generate_thermal_data(temp_params_file, temp_output_dir):
    """Test thermal data generation with Maxwell-Boltzmann distribution."""
    output_path = str(temp_output_dir / "test_thermal_data.csv")
    params = load_params(temp_params_file)
    
    generate_thermal_data(params, output_path)
    
    # Verify file exists
    assert Path(output_path).exists()
    
    # Verify data structure
    df = pd.read_csv(output_path)
    
    # Check columns
    expected_cols = ['particle_id', 'timestamp', 'v_x', 'v_y', 'v_z', 
                    'omega_x', 'omega_y', 'omega_z']
    assert list(df.columns) == expected_cols
    
    # Check row count (1000 particles * 100 frames)
    assert len(df) == 100000
    
    # Check data types
    assert df['particle_id'].dtype in ['int64', 'int32']
    assert df['timestamp'].dtype in ['float64', 'float32']
    
    # Check that velocities are positive (shifted distribution)
    assert (df['v_x'] > 0).all()
    assert (df['v_y'] > 0).all()
    assert (df['v_z'] > 0).all()

def test_generate_nonthermal_data(temp_params_file, temp_output_dir):
    """Test non-thermal data generation with Pareto distribution."""
    output_path = str(temp_output_dir / "test_nonthermal_data.csv")
    params = load_params(temp_params_file)
    
    generate_nonthermal_data(params, output_path)
    
    # Verify file exists
    assert Path(output_path).exists()
    
    # Verify data structure
    df = pd.read_csv(output_path)
    
    # Check columns
    expected_cols = ['particle_id', 'timestamp', 'v_x', 'v_y', 'v_z', 
                    'omega_x', 'omega_y', 'omega_z']
    assert list(df.columns) == expected_cols
    
    # Check row count (1000 particles * 100 frames)
    assert len(df) == 100000
    
    # Check that velocities follow heavy-tailed distribution
    # Pareto with shape=2.0 should have some large values
    assert (df['v_x'] > 0).all()
    assert (df['v_y'] > 0).all()
    assert (df['v_z'] > 0).all()
    
    # Check for presence of large values (characteristic of Pareto)
    max_v_x = df['v_x'].max()
    assert max_v_x > 5.0, "Pareto distribution should have some large values"

def test_test_prefix_in_filename(temp_output_dir):
    """Verify that generated files have 'test_' prefix as required."""
    params = {
        "maxwell_boltzmann": {"mean": 1.0, "scale": 0.1},
        "pareto": {"shape": 2.0}
    }
    
    thermal_path = str(temp_output_dir / "test_thermal_data.csv")
    nonthermal_path = str(temp_output_dir / "test_nonthermal_data.csv")
    
    generate_thermal_data(params, thermal_path)
    generate_nonthermal_data(params, nonthermal_path)
    
    assert Path(thermal_path).name.startswith("test_")
    assert Path(nonthermal_path).name.startswith("test_")
