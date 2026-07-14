"""
Unit tests for spectrum_computation.py
"""

import os
import sys
import numpy as np
import pytest
import healpy as hp

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from spectrum_computation import compute_bb_spectrum, validate_sky_coverage, save_spectrum_results


class TestComputeBB:
    def test_compute_bb_spectrum_basic(self):
        """Test basic spectrum computation with synthetic noise."""
        nside = 16
        n_pix = hp.nside2npix(nside)
        
        # Create synthetic Q and U maps with known noise
        np.random.seed(42)
        map_q = np.random.normal(0, 1e-6, n_pix)
        map_u = np.random.normal(0, 1e-6, n_pix)
        
        l_values, cl_bb, cl_err = compute_bb_spectrum(map_q, map_u, nside, l_max=10)
        
        assert len(l_values) > 0
        assert len(cl_bb) == len(l_values)
        assert len(cl_err) == len(l_values)
        assert np.all(l_values >= 2)
        # Cl values should be positive (or close to zero for noise)
        assert np.all(cl_bb >= -1e-15)  # Allow small numerical errors

    def test_compute_bb_spectrum_with_signal(self):
        """Test spectrum computation with a simulated signal."""
        nside = 32
        n_pix = hp.nside2npix(nside)
        
        # Create a simple signal (e.g., constant B-mode)
        # In reality, B-modes are not constant, but for testing the pipeline:
        np.random.seed(123)
        map_q = np.random.normal(0, 1e-5, n_pix)
        map_u = np.random.normal(0, 1e-5, n_pix)
        
        l_values, cl_bb, cl_err = compute_bb_spectrum(map_q, map_u, nside, l_max=20)
        
        assert len(cl_bb) == len(l_values)
        # Check that error estimation is reasonable
        assert np.all(cl_err > 0)


class TestValidateSkyCoverage:
    def test_validate_sky_coverage_pass(self):
        """Test validation with sufficient coverage."""
        nside = 16
        n_pix = hp.nside2npix(nside)
        # Create a mask with 80% coverage
        mask = np.ones(n_pix)
        mask[:int(n_pix * 0.2)] = 0.0  # Mask 20%
        
        coverage = validate_sky_coverage(mask, nside, min_coverage=0.70)
        assert coverage >= 0.70
        assert np.isclose(coverage, 0.80, atol=0.01)

    def test_validate_sky_coverage_fail(self):
        """Test validation with insufficient coverage."""
        nside = 16
        n_pix = hp.nside2npix(nside)
        # Create a mask with 50% coverage
        mask = np.ones(n_pix)
        mask[:int(n_pix * 0.5)] = 0.0
        
        with pytest.raises(ValueError, match="Sky coverage .* is below the minimum threshold"):
            validate_sky_coverage(mask, nside, min_coverage=0.70)


class TestSaveSpectrumResults:
    def test_save_spectrum_results(self, tmp_path):
        """Test saving spectrum results to JSON."""
        l_values = np.array([2, 3, 4])
        cl_bb = np.array([1.0, 2.0, 3.0])
        cl_err = np.array([0.1, 0.2, 0.3])
        output_path = os.path.join(tmp_path, "test_spectrum.json")
        metadata = {"nside": 16, "test": "unit"}
        
        save_spectrum_results(l_values, cl_bb, cl_err, output_path, metadata)
        
        assert os.path.exists(output_path)
        
        # Verify content
        import json
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["metadata"]["nside"] == 16
        assert len(data["l_values"]) == 3
        assert np.isclose(data["cl_bb"][0], 1.0)