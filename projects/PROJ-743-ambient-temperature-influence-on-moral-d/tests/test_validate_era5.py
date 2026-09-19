"""
Tests for T001b: validate_era5.py
"""
import os
import sys
import pytest
from pathlib import Path
import numpy as np
import h5py

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

# Mock imports if needed, but we test logic structure here
# Note: Actual CDS API calls are skipped in unit tests unless mocked properly.
# We test the validation logic and file structure.

def test_validate_hdf5_structure():
    """
    Test that the validate_hdf5_sample function correctly identifies a valid file structure.
    """
    # Create a mock HDF5 file
    mock_path = Path("/tmp/test_era5_sample.h5")
    try:
        with h5py.File(mock_path, "w") as hf:
            hf.create_dataset("time", data=np.arange(168)) # 7 days * 24 hours
            hf.create_dataset("latitude", data=np.array([51.5074]))
            hf.create_dataset("longitude", data=np.array([-0.1278]))
            hf.create_dataset("temperature", data=np.random.rand(168, 1, 1).astype(np.float32) * 10 + 10)
        
        from validate_era5 import validate_hdf5_sample
        result = validate_hdf5_sample(mock_path)
        assert result is True
    finally:
        if mock_path.exists():
            mock_path.unlink()

def test_validate_hdf5_missing_key():
    """
    Test that validation fails if a required key is missing.
    """
    mock_path = Path("/tmp/test_era5_missing.h5")
    try:
        with h5py.File(mock_path, "w") as hf:
            hf.create_dataset("time", data=np.arange(168))
            hf.create_dataset("latitude", data=np.array([51.5074]))
            # Missing 'temperature'
        
        from validate_era5 import validate_hdf5_sample
        result = validate_hdf5_sample(mock_path)
        assert result is False
    finally:
        if mock_path.exists():
            mock_path.unlink()

def test_validate_hdf5_out_of_range():
    """
    Test that validation fails if temperature is out of plausible range.
    """
    mock_path = Path("/tmp/test_era5_range.h5")
    try:
        with h5py.File(mock_path, "w") as hf:
            hf.create_dataset("time", data=np.arange(168))
            hf.create_dataset("latitude", data=np.array([51.5074]))
            hf.create_dataset("longitude", data=np.array([-0.1278]))
            # Set temperature to 200 (plausible range is -100 to 100 in code)
            hf.create_dataset("temperature", data=np.full((168, 1, 1), 200.0, dtype=np.float32))
        
        from validate_era5 import validate_hdf5_sample
        result = validate_hdf5_sample(mock_path)
        assert result is False
    finally:
        if mock_path.exists():
            mock_path.unlink()