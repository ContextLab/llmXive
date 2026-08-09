import os
import json
import tempfile
import shutil
import pytest
import numpy as np
import healpy as hp
from pathlib import Path

# Import the function to test
# We assume the module is installed or in the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data_loader import apply_galactic_mask, calculate_sha256

# Mock data generation for testing (since we cannot download real data in unit tests easily)
# We will create a temporary directory with fake FITS files that mimic the structure
# But we must ensure the logic works.

# However, the requirement says "Never fake data" for the main pipeline.
# For unit tests, we can generate synthetic FITS files to test the LOGIC of the function
# (e.g., the 95% check, the file saving) without needing the real 1GB Planck map.
# We will create a small Nside=16 map and mask to test the logic.

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def create_test_fits_file(path, nside=16, mask=False):
    """Create a minimal FITS file for testing."""
    n_pix = hp.nside2npix(nside)
    if mask:
        # Create a mask with 98% unmasked pixels (to pass the 95% check)
        data = np.ones(n_pix)
        # Mask out 2%
        n_mask = int(n_pix * 0.02)
        data[:n_mask] = 0
        hp.write_map(path, data, fits_id=True, nest=True, overwrite=True)
    else:
        # Create a temperature map
        data = np.random.randn(n_pix) * 1e-5
        hp.write_map(path, data, fits_id=True, nest=True, overwrite=True)

def test_apply_galactic_mask_success(temp_data_dir):
    """Test that apply_galactic_mask works when retention >= 95%."""
    # Create test files
    input_map = Path(temp_data_dir) / "test_map.fits"
    output_map = Path(temp_data_dir) / "masked_map.fits"
    mask_file = Path(temp_data_dir) / "test_mask.fits"
    
    create_test_fits_file(input_map, nside=16, mask=False)
    create_test_fits_file(mask_file, nside=16, mask=True) # 98% retention
    
    # We need to mock the download logic or provide the mask directly
    # Since the function tries to download the mask if not found, we must ensure it exists
    # Or we modify the function to accept a mask path. 
    # The current implementation looks for 'commander_mask.fits' in data/raw.
    # To test this function properly, we will create the expected structure.
    
    data_raw = Path(temp_data_dir) / "data" / "raw"
    data_processed = Path(temp_data_dir) / "data" / "processed"
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)
    
    # Copy mask to expected location
    shutil.copy(mask_file, data_raw / "commander_mask.fits")
    
    # Temporarily change the working directory or mock the path
    # Since the function uses hardcoded paths relative to project root, we need to be careful.
    # For the test, we will assume the test runs in a context where we can control the file system.
    
    # Let's refactor the test to use the actual function but with a mocked download path
    # Or, simpler: create the files in the expected relative paths for the test run.
    
    # We will run the test in the temp directory and set the CWD
    old_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    
    try:
        # We need to patch the download function to not actually download
        # Or simply ensure the file exists.
        # The function checks: if not mask_path.exists(): download...
        # We created it above.
        
        # Also need to ensure config paths are respected.
        # For this test, we assume the default config paths are used.
        
        # Run the function
        stats = apply_galactic_mask(
            input_map_path=str(input_map),
            output_map_path=str(output_map),
            mask_filename="test_mask.fits" # Override filename to match our test file
        )
        
        # Assertions
        assert stats["retention_percentage"] >= 95.0
        assert os.path.exists(output_map)
        assert os.path.exists("data/processed/mask_stats.json")
        assert os.path.exists("data/processed/mask_validation_report.json")
        
        with open("data/processed/mask_stats.json") as f:
            saved_stats = json.load(f)
        assert saved_stats["retention_percentage"] >= 95.0
        
    finally:
        os.chdir(old_cwd)

def test_apply_galactic_mask_failure_low_retention(temp_data_dir):
    """Test that apply_galactic_mask raises ValueError if retention < 95%."""
    # Create a mask with 90% retention
    nside = 16
    n_pix = hp.nside2npix(nside)
    data = np.ones(n_pix)
    n_mask = int(n_pix * 0.10) # 10% masked -> 90% retention
    data[:n_mask] = 0
    
    mask_path = Path(temp_data_dir) / "bad_mask.fits"
    hp.write_map(mask_path, data, fits_id=True, nest=True, overwrite=True)
    
    input_map = Path(temp_data_dir) / "test_map.fits"
    hp.write_map(input_map, np.random.randn(n_pix), fits_id=True, nest=True, overwrite=True)
    
    data_raw = Path(temp_data_dir) / "data" / "raw"
    data_processed = Path(temp_data_dir) / "data" / "processed"
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)
    
    shutil.copy(mask_path, data_raw / "commander_mask.fits")
    
    old_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    
    try:
        with pytest.raises(ValueError) as excinfo:
            apply_galactic_mask(
                input_map_path=str(input_map),
                output_map_path=str(Path(temp_data_dir) / "masked_map.fits"),
                mask_filename="commander_mask.fits"
            )
        
        assert "95%" in str(excinfo.value)
    finally:
        os.chdir(old_cwd)
