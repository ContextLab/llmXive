"""
Unit tests for synthetic data generation module.
"""
import os
import json
import tempfile
import numpy as np
import pytest
import healpy as hp

# Adjust import path if running from tests/
import sys
import pathlib
project_root = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.synthetic_data import (
    generate_theoretical_BB_spectrum,
    generate_gaussian_random_field,
    generate_inflation_synthetic,
    generate_null_synthetic,
    generate_pt_synthetic,
    serialize_inflation_ground_truth,
    serialize_null_ground_truth,
    serialize_pt_ground_truth
)


class TestTheoreticalSpectrum:
    def test_spectrum_shape(self):
        """Test that the spectrum has the expected shape."""
        l_vals, cl_vals = generate_theoretical_BB_spectrum(r=0.01)
        assert len(l_vals) == len(cl_vals)
        assert l_vals[0] >= 2
        assert np.all(cl_vals >= 0)

    def test_inflation_component(self):
        """Test that inflation component is present when r > 0."""
        l_vals, cl_vals = generate_theoretical_BB_spectrum(r=0.01)
        # Check that there is some power
        assert np.sum(cl_vals) > 0

    def test_null_component(self):
        """Test that null model produces only lensing power."""
        l_vals, cl_vals = generate_theoretical_BB_spectrum(r=0.0, E_PT=None)
        # Should still have lensing power
        assert np.sum(cl_vals) > 0


class TestGaussianRandomField:
    def test_map_shape(self):
        """Test that generated map has correct shape."""
        l_vals = np.arange(2, 100)
        cl_vals = np.ones_like(l_vals, dtype=float) * 1e-10
        nside = 16
        bmap = generate_gaussian_random_field(nside, cl_vals, l_vals, seed=42)
        expected_npix = hp.nside2npix(nside)
        assert bmap.shape == (expected_npix,)

    def test_reproducibility(self):
        """Test that same seed produces same map."""
        l_vals = np.arange(2, 100)
        cl_vals = np.ones_like(l_vals, dtype=float) * 1e-10
        nside = 16
        
        map1 = generate_gaussian_random_field(nside, cl_vals, l_vals, seed=123)
        map2 = generate_gaussian_random_field(nside, cl_vals, l_vals, seed=123)
        
        np.testing.assert_array_equal(map1, map2)


class TestInflationSynthetic:
    def test_file_creation(self):
        """Test that the function creates a FITS file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_inflation.fits")
            result_path = generate_inflation_synthetic(r=0.01, output_path=output_path)
            
            assert os.path.exists(result_path)
            assert result_path == output_path

    def test_map_validity(self):
        """Test that the generated map is a valid HEALPix map."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_inflation.fits")
            generate_inflation_synthetic(r=0.01, output_path=output_path)
            
            # Try to read the map
            bmap = hp.read_map(output_path)
            assert len(bmap) > 0


class TestNullSynthetic:
    def test_file_creation(self):
        """Test that the function creates a FITS file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_null.fits")
            result_path = generate_null_synthetic(output_path=output_path)
            
            assert os.path.exists(result_path)


class TestPTSynthetic:
    def test_file_creation(self):
        """Test that the function creates a FITS file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_pt.fits")
            result_path = generate_pt_synthetic(E_PT=1e15, output_path=output_path)
            
            assert os.path.exists(result_path)


class TestGroundTruthSerialization:
    def test_inflation_gt(self):
        """Test inflation ground truth JSON structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "gt_inflation.json")
            result_path = serialize_inflation_ground_truth(r=0.01, output_path=output_path)
            
            assert os.path.exists(result_path)
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            assert data["model_type"] == "inflation"
            assert "true_parameters" in data
            assert data["true_parameters"]["r"] == 0.01

    def test_null_gt(self):
        """Test null ground truth JSON structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "gt_null.json")
            result_path = serialize_null_ground_truth(output_path=output_path)
            
            assert os.path.exists(result_path)
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            assert data["model_type"] == "null"

    def test_pt_gt(self):
        """Test PT ground truth JSON structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "gt_pt.json")
            result_path = serialize_pt_ground_truth(E_PT=1e15, output_path=output_path)
            
            assert os.path.exists(result_path)
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            assert data["model_type"] == "phase_transition"
            assert data["true_parameters"]["E_PT"] == 1e15