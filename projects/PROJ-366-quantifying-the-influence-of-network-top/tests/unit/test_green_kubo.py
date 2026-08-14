"""
Unit tests for the Green-Kubo simulation wrapper.

These tests verify the logic of generating LAMMPS input files and
data files from graph data, without actually running the LAMMPS executable.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import numpy as np

# Mock the config and paths to avoid dependency on full project setup
import sys
from unittest.mock import patch, MagicMock

# Import the module under test
from simulation.green_kubo import (
    generate_lammps_data_file,
    generate_lammps_input_script,
    run_green_kubo_for_sample,
    post_process_hcacf
)

@pytest.fixture
def sample_graph_data():
    """Create a minimal valid graph data structure."""
    return {
        "nodes": [
            {"id": 1, "x": 0.0, "y": 0.0, "z": 0.0, "type": 1},
            {"id": 2, "x": 2.35, "y": 0.0, "z": 0.0, "type": 1},
            {"id": 3, "x": 1.175, "y": 2.035, "z": 0.0, "type": 1},
            {"id": 4, "x": 1.175, "y": 0.678, "z": 1.935, "type": 1}
        ],
        "edges": [
            (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)
        ],
        "box": [-1.0, 3.35, -1.0, 3.035, -1.0, 3.935]
    }

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_lammps_data_file(temp_dir, sample_graph_data):
    """Test that a valid LAMMPS DATA file is generated."""
    output_path = temp_dir / "test.data"
    result_path = generate_lammps_data_file(sample_graph_data, output_path)
    
    assert result_path.exists()
    
    with open(result_path, 'r') as f:
        content = f.read()
    
    # Verify header
    assert "LAMMPS Data File" in content
    assert "4 atoms" in content
    assert "1 atom types" in content
    
    # Verify box
    assert "-1.000000" in content
    assert "3.350000" in content
    
    # Verify atoms
    assert "1 1 0.000000 0.000000 0.000000" in content
    assert "2 1 2.350000 0.000000 0.000000" in content
    
    # Verify bonds
    assert "Bonds" in content
    assert "1 1 1 2" in content

def test_generate_lammps_input_script(temp_dir, sample_graph_data):
    """Test that a valid LAMMPS input script is generated."""
    data_file = temp_dir / "test.data"
    generate_lammps_data_file(sample_graph_data, data_file)
    
    potential_file = temp_dir / "potential.txt"
    potential_file.write_text("dummy potential content")
    
    script_path = generate_lammps_input_script(
        data_file=data_file,
        potential_file=potential_file,
        output_dir=temp_dir,
        timestep=1.0,
        n_steps_equil=100,
        n_steps_prod=200,
        temperature=300.0
    )
    
    assert script_path.exists()
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    assert "units metal" in content
    assert "read_data test.data" in content
    assert "pair_style sw" in content
    assert "fix 1 all nvt temp 300.0 300.0 0.1" in content
    assert "run 100" in content # Equilibration
    assert "compute 1 all heat_flux" in content
    assert "run 200" in content # Production
    assert "fix 3 all ave/correlate" in content

def test_post_process_hcacf(temp_dir):
    """Test HCACF post-processing with dummy data."""
    hcacf_file = temp_dir / "hcacf.dat"
    
    # Create dummy data: time, Jx, Jy, Jz, <JxJx>, <JyJy>, <JzJz>
    # Simulating a decaying correlation
    times = np.linspace(0, 100, 1000)
    cxx = np.exp(-times / 10)
    cyy = np.exp(-times / 10)
    czz = np.exp(-times / 10)
    
    data = np.column_stack([times, cxx, cyy, czz, cxx, cyy, czz])
    np.savetxt(hcacf_file, data)
    
    result = post_process_hcacf(hcacf_file)
    
    assert result is not None
    # The integral of exp(-t/10) from 0 to 100 is approx 10 * (1 - exp(-10)) ~ 10
    # We have 3 components, so sum ~ 30.
    # Check if it's in the right ballpark (positive and reasonable magnitude)
    assert result > 0
    assert result < 1000 # Sanity check

def test_run_green_kubo_for_sample_integration(temp_dir, sample_graph_data):
    """
    Integration test for the full sample processing flow.
    Note: This test mocks the LAMMPS execution to avoid requiring LAMMPS installed.
    """
    # Create a mock graph file
    graph_file = temp_dir / "sample_001.pkl"
    import pickle
    with open(graph_file, 'wb') as f:
        pickle.dump(sample_graph_data, f)
    
    output_dir = temp_dir / "output"
    output_dir.mkdir()
    
    config = {
        "simulation": {
            "timestep": 1.0,
            "equilibration_steps": 100,
            "production_steps": 200,
            "temperature": 300.0,
            "potential_file": "dummy_pot"
        }
    }
    
    # Mock subprocess.run to simulate LAMMPS success without running it
    with patch('simulation.green_kubo.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="LAMMPS simulation completed",
            stderr=""
        )
        
        result = run_green_kubo_for_sample(
            sample_id="sample_001",
            graph_path=graph_file,
            output_dir=output_dir,
            config=config
        )
        
        # Verify that the script and data files were created
        assert (output_dir / "sample_001" / "sample_001.data").exists()
        assert (output_dir / "sample_001" / "in.green_kubo").exists()
        
        # Verify result structure
        assert result["success"] is True
        assert "elapsed" in result
        
        # Verify that subprocess.run was called
        assert mock_run.called