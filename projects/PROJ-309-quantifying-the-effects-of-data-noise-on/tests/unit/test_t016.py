"""
Unit tests for T016: Writing clean trajectories to data/raw/ with checksums.
"""

import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.run_t016 import save_trajectory_to_csv, write_sidecar_checksum
from code.utils.io import compute_file_checksum

def test_save_trajectory_to_csv():
    """Test that trajectories are saved correctly to CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_trajectory.csv'
        
        # Create test trajectory data
        time = np.linspace(0, 10, 100)
        data = np.random.randn(100, 3)
        trajectory = {'time': time, 'data': data}
        
        # Save trajectory
        save_trajectory_to_csv(trajectory, output_path)
        
        # Verify file exists
        assert output_path.exists(), "CSV file was not created"
        
        # Verify file content
        with open(output_path, 'r') as f:
            lines = f.readlines()
            
        # Check header
        header = lines[0].strip()
        assert header.startswith('time,'), f"Header should start with 'time,', got: {header}"
        assert 'x0' in header and 'x1' in header and 'x2' in header, "Header should contain x0, x1, x2"
        
        # Check data rows
        assert len(lines) == 101, f"Expected 101 lines (1 header + 100 data), got {len(lines)}"
        
        # Verify first data row
        first_row = lines[1].strip().split(',')
        assert len(first_row) == 4, f"First row should have 4 columns, got {len(first_row)}"
        assert float(first_row[0]) == time[0], "First time value mismatch"

def test_write_sidecar_checksum():
    """Test that checksum sidecars are created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / 'test.csv'
        checksum_path = Path(tmpdir) / 'test.sha256'
        
        # Create a test file
        with open(csv_path, 'w') as f:
            f.write("test content")
        
        # Write checksum
        write_sidecar_checksum(csv_path, checksum_path)
        
        # Verify checksum file exists
        assert checksum_path.exists(), "Checksum file was not created"
        
        # Verify checksum content
        with open(checksum_path, 'r') as f:
            sidecar_data = json.load(f)
            
        assert 'checksum' in sidecar_data, "Checksum should be in sidecar data"
        assert 'file' in sidecar_data, "Filename should be in sidecar data"
        assert sidecar_data['file'] == 'test.csv', "Filename should match"
        assert sidecar_data['checksum_algorithm'] == 'sha256', "Algorithm should be sha256"
        
        # Verify checksum is correct
        expected_checksum = compute_file_checksum(str(csv_path))
        assert sidecar_data['checksum'] == expected_checksum, "Checksum mismatch"

def test_trajectory_schema():
    """Test that trajectories conform to expected schema."""
    from code.generators import generate_lorenz_trajectory
    
    trajectory = generate_lorenz_trajectory(seed=42)
    
    assert trajectory is not None, "Trajectory should not be None"
    assert 'time' in trajectory, "Trajectory should have 'time' key"
    assert 'data' in trajectory, "Trajectory should have 'data' key"
    assert isinstance(trajectory['time'], np.ndarray), "Time should be numpy array"
    assert isinstance(trajectory['data'], np.ndarray), "Data should be numpy array"
    assert trajectory['data'].shape[0] == len(trajectory['time']), "Time and data length should match"
    assert trajectory['data'].shape[1] == 3, "Lorenz system should have 3 dimensions"

if __name__ == '__main__':
    test_save_trajectory_to_csv()
    test_write_sidecar_checksum()
    test_trajectory_schema()
    print("All T016 unit tests passed!")