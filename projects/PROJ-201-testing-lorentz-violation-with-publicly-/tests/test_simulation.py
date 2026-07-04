"""
Tests for the simulation module.

These tests verify:
1. Isotropic null simulations are generated correctly
2. Files are written to the correct location
3. FITS files contain valid data
4. Noise is applied as expected
"""

import pytest
import numpy as np
import healpy as hp
import os
from pathlib import Path
import tempfile
import yaml

from code.data.simulation import (
    generate_isotropic_null,
    generate_isotropic_alm,
    construct_alpha_lm,
    inject_sme_coefficient,
    simulate_cmb_map
)
from code.config import load_config

@pytest.fixture
def temp_config():
    """Create a temporary config file for testing."""
    config = {
        'paths': {
            'raw': 'data/raw',
            'processed': 'data/processed',
            'results': 'data/results',
            'simulations': 'data/simulations'
        },
        'seeds': {
            'random': 42,
            'numpy': 42
        },
        'constants': {
            'sme_coefficient': [0.0, 0.1, 0.5],
            'l_max': 200,
            'noise_model': {
                'rms': 1e-5
            },
            'beam': {
                'sigma': None
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    os.unlink(config_path)

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_generate_isotropic_alm_basic():
    """Test basic alm generation."""
    nside = 32
    alm = generate_isotropic_alm(nside=nside, seed=42)
    
    # Check that alm is not empty
    assert alm is not None
    assert len(alm) > 0
    
    # Check that alm is a numpy array
    assert isinstance(alm, np.ndarray)
    
    # Check that values are finite
    assert np.all(np.isfinite(alm))

def test_generate_isotropic_alm_reproducibility():
    """Test that same seed produces same results."""
    nside = 32
    alm1 = generate_isotropic_alm(nside=nside, seed=123)
    alm2 = generate_isotropic_alm(nside=nside, seed=123)
    
    np.testing.assert_array_equal(alm1, alm2)

def test_construct_alpha_lm():
    """Test alpha_lm construction."""
    nside = 32
    k_value = 0.1
    alpha_alm = construct_alpha_lm(nside=nside, k_value=k_value, seed=42)
    
    assert alpha_alm is not None
    assert len(alpha_alm) > 0
    assert isinstance(alpha_alm, np.ndarray)
    assert np.all(np.isfinite(alpha_alm))

def test_inject_sme_coefficient():
    """Test SME coefficient injection."""
    nside = 32
    alm_iso = generate_isotropic_alm(nside=nside, seed=42)
    alpha_alm = construct_alpha_lm(nside=nside, k_value=0.1, seed=42)
    
    alm_aniso = inject_sme_coefficient(alm_iso, alpha_alm, nside)
    
    # Check that aniso alm is different from isotropic
    assert not np.array_equal(alm_iso, alm_aniso)
    
    # Check that values are finite
    assert np.all(np.isfinite(alm_aniso))

def test_simulate_cmb_map():
    """Test CMB map simulation."""
    nside = 32
    alm = generate_isotropic_alm(nside=nside, seed=42)
    
    cmb_map = simulate_cmb_map(alm, nside, seed=42)
    
    # Check that map has correct size
    n_pix = hp.nside2npix(nside)
    assert len(cmb_map) == n_pix
    
    # Check that values are finite
    assert np.all(np.isfinite(cmb_map))

def test_simulate_cmb_map_with_noise():
    """Test CMB map simulation with noise."""
    nside = 32
    alm = generate_isotropic_alm(nside=nside, seed=42)
    noise_rms = 1e-4
    
    cmb_map = simulate_cmb_map(alm, nside, noise_rms=noise_rms, seed=42)
    
    # Check that map has correct size
    n_pix = hp.nside2npix(nside)
    assert len(cmb_map) == n_pix
    
    # Check that values are finite
    assert np.all(np.isfinite(cmb_map))

def test_generate_isotropic_null_creates_files(temp_config, temp_output_dir):
    """Test that isotropic null simulations create FITS files."""
    # Update config to use temp output directory
    with open(temp_config, 'r') as f:
        config = yaml.safe_load(f)
    
    config['paths']['simulations'] = temp_output_dir
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        temp_config_path = f.name
    
    try:
        # Generate 3 simulations for testing
        files = generate_isotropic_null(
            n_simulations=3,
            nside=32,  # Small nside for fast testing
            output_dir=temp_output_dir,
            config_path=temp_config_path,
            seed_base=42
        )
        
        # Check that files were created
        assert len(files) == 3
        
        # Check that each file exists
        for filepath in files:
            assert os.path.exists(filepath)
            assert filepath.endswith('.fits')
        
        # Check that files are valid FITS files
        for filepath in files:
            map_data = hp.read_map(filepath)
            assert map_data is not None
            assert len(map_data) == hp.nside2npix(32)
            assert np.all(np.isfinite(map_data))
    finally:
        os.unlink(temp_config_path)

def test_generate_isotropic_null_nside_256(temp_config, temp_output_dir):
    """Test isotropic null simulations with Nside=256 as required."""
    # Update config to use temp output directory
    with open(temp_config, 'r') as f:
        config = yaml.safe_load(f)
    
    config['paths']['simulations'] = temp_output_dir
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        temp_config_path = f.name
    
    try:
        # Generate 1 simulation for testing (full 200 would be slow)
        files = generate_isotropic_null(
            n_simulations=1,
            nside=256,
            output_dir=temp_output_dir,
            config_path=temp_config_path,
            seed_base=42
        )
        
        # Check that file was created
        assert len(files) == 1
        assert os.path.exists(files[0])
        
        # Check that file is valid FITS with correct nside
        map_data = hp.read_map(files[0])
        assert len(map_data) == hp.nside2npix(256)
        assert np.all(np.isfinite(map_data))
    finally:
        os.unlink(temp_config_path)

def test_generate_isotropic_null_with_noise(temp_config, temp_output_dir):
    """Test that noise is applied to isotropic simulations."""
    # Update config with higher noise for testing
    with open(temp_config, 'r') as f:
        config = yaml.safe_load(f)
    
    config['paths']['simulations'] = temp_output_dir
    config['constants']['noise_model']['rms'] = 1e-3  # Higher noise for detection
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        temp_config_path = f.name
    
    try:
        # Generate 2 simulations
        files = generate_isotropic_null(
            n_simulations=2,
            nside=32,
            output_dir=temp_output_dir,
            config_path=temp_config_path,
            seed_base=42
        )
        
        # Read maps
        maps = [hp.read_map(f) for f in files]
        
        # Check that maps are different (due to different noise realizations)
        assert not np.array_equal(maps[0], maps[1])
    finally:
        os.unlink(temp_config_path)

def test_generate_isotropic_null_file_count(temp_config, temp_output_dir):
    """Test that the correct number of files is generated."""
    # Update config
    with open(temp_config, 'r') as f:
        config = yaml.safe_load(f)
    
    config['paths']['simulations'] = temp_output_dir
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        temp_config_path = f.name
    
    try:
        n_sims = 5
        files = generate_isotropic_null(
            n_simulations=n_sims,
            nside=32,
            output_dir=temp_output_dir,
            config_path=temp_config_path,
            seed_base=42
        )
        
        assert len(files) == n_sims
        
        # Count files in directory
        fits_files = list(Path(temp_output_dir).glob('*.fits'))
        assert len(fits_files) == n_sims
    finally:
        os.unlink(temp_config_path)

def test_generate_isotropic_null_invalid_n_simulations(temp_config):
    """Test that invalid n_simulations raises an error."""
    with pytest.raises(ValueError):
        generate_isotropic_null(
            n_simulations=0,
            nside=32,
            config_path=temp_config
        )
    
    with pytest.raises(ValueError):
        generate_isotropic_null(
            n_simulations=-1,
            nside=32,
            config_path=temp_config
        )

def test_generate_isotropic_null_reproducibility(temp_config, temp_output_dir):
    """Test that same seed produces same results."""
    # Update config
    with open(temp_config, 'r') as f:
        config = yaml.safe_load(f)
    
    config['paths']['simulations'] = temp_output_dir
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        temp_config_path = f.name
    
    try:
        # Generate first set
        files1 = generate_isotropic_null(
            n_simulations=2,
            nside=32,
            output_dir=temp_output_dir,
            config_path=temp_config_path,
            seed_base=42
        )
        
        # Read maps
        maps1 = [hp.read_map(f) for f in files1]
        
        # Clear directory
        for f in files1:
            os.remove(f)
        
        # Generate second set with same seed
        files2 = generate_isotropic_null(
            n_simulations=2,
            nside=32,
            output_dir=temp_output_dir,
            config_path=temp_config_path,
            seed_base=42
        )
        
        # Read maps
        maps2 = [hp.read_map(f) for f in files2]
        
        # Check that maps are identical
        for m1, m2 in zip(maps1, maps2):
            np.testing.assert_array_equal(m1, m2)
    finally:
        os.unlink(temp_config_path)