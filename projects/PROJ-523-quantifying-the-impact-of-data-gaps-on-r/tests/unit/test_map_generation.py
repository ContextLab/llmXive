"""
Unit tests for map generation logic (Task T011).
"""
import pytest
import numpy as np
import os
import tempfile
from pathlib import Path

# Import the function to test
from code.simulation.generate_maps import generate_cmb_map, write_ground_truth_metadata, get_camb_version
from code.config import N_SIDE, COSMO_PARAMS

def test_generate_cmb_map_shape():
    """Test that generated map has correct shape for Nside=512."""
    seed = 42
    t_map, e_map, b_map = generate_cmb_map(seed, nside=N_SIDE)
    
    expected_npix = 12 * N_SIDE * N_SIDE
    assert t_map.shape == (expected_npix,), f"Temperature map shape mismatch: {t_map.shape}"
    assert e_map.shape == (expected_npix,), f"E-map shape mismatch: {e_map.shape}"
    assert b_map.shape == (expected_npix,), f"B-map shape mismatch: {b_map.shape}"

def test_generate_cmb_map_values():
    """Test that generated maps contain finite values."""
    seed = 42
    t_map, e_map, b_map = generate_cmb_map(seed, nside=N_SIDE)
    
    assert np.all(np.isfinite(t_map)), "Temperature map contains non-finite values"
    assert np.all(np.isfinite(e_map)), "E-map contains non-finite values"
    assert np.all(np.isfinite(b_map)), "B-map contains non-finite values"

def test_generate_cmb_map_seed_reproducibility():
    """Test that same seed produces same map."""
    seed = 123
    t_map_1, _, _ = generate_cmb_map(seed, nside=N_SIDE)
    t_map_2, _, _ = generate_cmb_map(seed, nside=N_SIDE)
    
    np.testing.assert_array_equal(t_map_1, t_map_2, "Maps with same seed are not identical")

def test_metadata_schema_keys():
    """Test that metadata writer includes required schema keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        realization_id = 99
        seed = 42
        params = COSMO_PARAMS
        camb_ver = get_camb_version()
        
        write_ground_truth_metadata(realization_id, seed, params, output_dir, camb_ver)
        
        metadata_path = output_dir / f"{realization_id}.json"
        assert metadata_path.exists(), "Metadata file not created"
        
        import json
        with open(metadata_path, 'r') as f:
            meta = json.load(f)
        
        required_keys = ["realization_id", "H0", "n_s", "tau", "seed", "camb_version"]
        for key in required_keys:
            assert key in meta, f"Missing required key in metadata: {key}"