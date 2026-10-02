import os
import json
import tempfile
import numpy as np
import healpy as hp
import pytest
from pathlib import Path

# Import the function to test
# We assume the module is code/coverage.py
# Adjust import path as needed based on project structure
# Since the task is in code/, and tests are in tests/, we might need to add code to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from coverage import generate_coverage_report, calculate_coverage_stats

@pytest.fixture
def temp_masked_map():
    """Create a temporary masked CMB map for testing."""
    nside = 16
    n_pix = hp.nside2npix(nside)
    
    # Create a mock map: valid pixels have random values, masked are NaN
    data = np.random.randn(n_pix)
    
    # Mask some pixels (e.g., first 10%)
    num_masked = int(0.1 * n_pix)
    data[:num_masked] = np.nan
    
    with tempfile.NamedTemporaryFile(suffix='.fits', delete=False) as f:
        hp.write_map(f.name, data, overwrite=True)
        return f.name

@pytest.fixture
def temp_output_path():
    """Create a temporary output path."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        return f.name

def test_generate_coverage_report(temp_masked_map, temp_output_path):
    """Test the main function generates a valid report."""
    report = generate_coverage_report(temp_masked_map, temp_output_path)
    
    # Check report structure
    assert 'sky_coverage' in report
    assert 'valid_pixels' in report
    assert 'total_pixels' in report
    
    # Check types
    assert isinstance(report['sky_coverage'], float)
    assert isinstance(report['valid_pixels'], int)
    assert isinstance(report['total_pixels'], int)
    
    # Check values
    nside = 16
    total = 12 * nside * nside
    expected_valid = total - int(0.1 * total)
    
    assert report['total_pixels'] == total
    assert report['valid_pixels'] == expected_valid
    assert abs(report['sky_coverage'] - (expected_valid / total)) < 1e-6
    
    # Check file was written
    assert os.path.exists(temp_output_path)
    
    with open(temp_output_path, 'r') as f:
        loaded_report = json.load(f)
    assert loaded_report == report

def test_calculate_coverage_stats():
    """Test the stats calculation logic."""
    nside = 16
    n_pix = hp.nside2npix(nside)
    total = 12 * nside * nside
    
    # Create a mask: 1.0 for valid, 0.0 for masked
    mask = np.ones(n_pix)
    mask[:100] = 0.0
    
    stats = calculate_coverage_stats(mask, total)
    
    assert stats['valid_pixels'] == n_pix - 100
    assert stats['total_pixels'] == total
    assert abs(stats['sky_coverage'] - (n_pix - 100) / total) < 1e-6

def test_coverage_with_all_valid(temp_output_path):
    """Test with a map that has no masked pixels."""
    nside = 16
    n_pix = hp.nside2npix(nside)
    data = np.random.randn(n_pix)
    
    with tempfile.NamedTemporaryFile(suffix='.fits', delete=False) as f:
        hp.write_map(f.name, data, overwrite=True)
        temp_map = f.name
    
    try:
        report = generate_coverage_report(temp_map, temp_output_path)
        assert report['valid_pixels'] == report['total_pixels']
        assert abs(report['sky_coverage'] - 1.0) < 1e-6
    finally:
        os.unlink(temp_map)

def test_coverage_with_all_masked(temp_output_path):
    """Test with a map that is fully masked (all NaN)."""
    nside = 16
    n_pix = hp.nside2npix(nside)
    data = np.full(n_pix, np.nan)
    
    with tempfile.NamedTemporaryFile(suffix='.fits', delete=False) as f:
        hp.write_map(f.name, data, overwrite=True)
        temp_map = f.name
    
    try:
        report = generate_coverage_report(temp_map, temp_output_path)
        assert report['valid_pixels'] == 0
        assert report['sky_coverage'] == 0.0
    finally:
        os.unlink(temp_map)
