import os
import sys
import pytest
import numpy as np
import healpy as hp
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.mode_coupling import (
    compute_mask_power_spectrum,
    compute_mode_coupling_matrix,
    calculate_leakage_matrix_from_mask,
    get_leakage_matrix_path,
    save_leakage_matrix,
    load_leakage_matrix,
    validate_leakage_matrix
)
from config import N_SIDE, DATA_DERIVED_DIR

class TestMaskPowerSpectrum:
    def test_compute_mask_power_spectrum_valid(self):
        """Test that mask power spectrum is computed correctly for a valid mask."""
        nside = N_SIDE
        npix = hp.nside2npix(nside)
        
        # Create a simple random mask (0s and 1s)
        np.random.seed(42)
        mask = np.random.choice([0, 1], size=npix).astype(np.float32)
        
        cl = compute_mask_power_spectrum(mask, nside)
        
        # Verify output shape and type
        assert isinstance(cl, np.ndarray)
        assert len(cl) > 0
        assert not np.any(np.isnan(cl))
        assert not np.any(np.isinf(cl))

    def test_compute_mask_power_spectrum_all_masked(self):
        """Test behavior when mask is all zeros."""
        nside = N_SIDE
        npix = hp.nside2npix(nside)
        
        mask = np.zeros(npix, dtype=np.float32)
        
        cl = compute_mask_power_spectrum(mask, nside)
        
        # Should return zeros or very small values, no NaNs
        assert isinstance(cl, np.ndarray)
        assert not np.any(np.isnan(cl))

class TestModeCouplingMatrix:
    def test_compute_mode_coupling_matrix_shape(self):
        """Test that mode coupling matrix has correct dimensions."""
        nside = N_SIDE
        l_max = 2 * nside - 1
        
        np.random.seed(42)
        mask = np.random.choice([0, 1], size=hp.nside2npix(nside)).astype(np.float32)
        
        coupling_matrix = compute_mode_coupling_matrix(mask, nside, l_max)
        
        expected_size = l_max + 1
        assert coupling_matrix.shape == (expected_size, expected_size)
        assert not np.any(np.isnan(coupling_matrix))

    def test_compute_mode_coupling_matrix_symmetry(self):
        """Test that mode coupling matrix is symmetric."""
        nside = N_SIDE
        l_max = 2 * nside - 1
        
        np.random.seed(42)
        mask = np.random.choice([0, 1], size=hp.nside2npix(nside)).astype(np.float32)
        
        coupling_matrix = compute_mode_coupling_matrix(mask, nside, l_max)
        
        # Check symmetry (allowing for small numerical errors)
        assert np.allclose(coupling_matrix, coupling_matrix.T, rtol=1e-5)

class TestLeakageMatrix:
    def test_calculate_leakage_matrix_from_mask(self):
        """Test leakage matrix calculation from a mask."""
        nside = N_SIDE
        l_max = 2 * nside - 1
        
        np.random.seed(42)
        mask = np.random.choice([0, 1], size=hp.nside2npix(nside)).astype(np.float32)
        
        leakage_matrix = calculate_leakage_matrix_from_mask(mask, nside, l_max)
        
        expected_size = l_max + 1
        assert leakage_matrix.shape == (expected_size, expected_size)
        assert not np.any(np.isnan(leakage_matrix))

    def test_save_and_load_leakage_matrix(self, tmp_path):
        """Test saving and loading leakage matrix."""
        nside = N_SIDE
        l_max = 2 * nside - 1
        
        np.random.seed(42)
        mask = np.random.choice([0, 1], size=hp.nside2npix(nside)).astype(np.float32)
        
        leakage_matrix = calculate_leakage_matrix_from_mask(mask, nside, l_max)
        
        # Save to temporary directory
        test_path = tmp_path / "test_leakage_matrix.npy"
        save_leakage_matrix(leakage_matrix, str(test_path))
        
        # Load back
        loaded_matrix = load_leakage_matrix(str(test_path))
        
        # Verify content
        assert np.allclose(leakage_matrix, loaded_matrix)
        assert loaded_matrix.shape == leakage_matrix.shape

    def test_validate_leakage_matrix(self):
        """Test leakage matrix validation."""
        nside = N_SIDE
        l_max = 2 * nside - 1
        
        np.random.seed(42)
        mask = np.random.choice([0, 1], size=hp.nside2npix(nside)).astype(np.float32)
        
        valid_matrix = calculate_leakage_matrix_from_mask(mask, nside, l_max)
        invalid_matrix = np.full((l_max + 1, l_max + 1), np.nan)
        
        assert validate_leakage_matrix(valid_matrix, l_max) is True
        assert validate_leakage_matrix(invalid_matrix, l_max) is False

    def test_get_leakage_matrix_path(self):
        """Test leakage matrix path generation."""
        realization_id = "test_123"
        
        path = get_leakage_matrix_path(realization_id)
        
        assert "leakage_matrix_test_123.npy" in str(path)
        assert path.parent == Path(DATA_DERIVED_DIR)

class TestIntegration:
    def test_full_leakage_computation_pipeline(self):
        """Test the full pipeline from mask to validated leakage matrix."""
        nside = N_SIDE
        l_max = 2 * nside - 1
        
        np.random.seed(123)
        mask = np.random.choice([0, 1], size=hp.nside2npix(nside)).astype(np.float32)
        
        # Compute mask power spectrum
        mask_cl = compute_mask_power_spectrum(mask, nside)
        assert len(mask_cl) > 0
        
        # Compute coupling matrix
        coupling_matrix = compute_mode_coupling_matrix(mask, nside, l_max)
        assert coupling_matrix.shape == (l_max + 1, l_max + 1)
        
        # Calculate leakage matrix
        leakage_matrix = calculate_leakage_matrix_from_mask(mask, nside, l_max)
        assert validate_leakage_matrix(leakage_matrix, l_max)
