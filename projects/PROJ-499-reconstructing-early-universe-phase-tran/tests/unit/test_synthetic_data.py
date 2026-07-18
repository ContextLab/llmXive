"""
Unit tests for synthetic data generation functions.
"""

import os
import json
import tempfile
import numpy as np
import pytest
import healpy as hp

from synthetic_data import (
    generate_theoretical_BB_spectrum,
    generate_gaussian_random_field,
    generate_inflation_synthetic,
    generate_pt_synthetic,
    save_dataset
)


class TestTheoreticalSpectrum:
    """Tests for generate_theoretical_BB_spectrum function."""

    def test_inflation_spectrum_structure(self):
        """Test that inflation spectrum has correct structure and positive values."""
        l_values, Cl_BB = generate_theoretical_BB_spectrum('inflation', {'r': 0.01})

        assert len(l_values) > 0
        assert len(Cl_BB) == len(l_values)
        assert np.all(Cl_BB >= 0)
        assert l_values[0] == 2  # Starts at l=2

    def test_phase_transition_spectrum_structure(self):
        """Test that phase transition spectrum has correct structure and positive values."""
        l_values, Cl_BB = generate_theoretical_BB_spectrum('phase_transition', {'E_PT': 1e15})

        assert len(l_values) > 0
        assert len(Cl_BB) == len(l_values)
        assert np.all(Cl_BB >= 0)
        assert l_values[0] == 2

    def test_invalid_model_type(self):
        """Test that invalid model type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown model type"):
            generate_theoretical_BB_spectrum('invalid_model', {})


class TestGaussianRandomField:
    """Tests for generate_gaussian_random_field function."""

    def test_map_dimensions(self):
        """Test that generated map has correct dimensions."""
        l_values = np.array([2.0, 3.0, 4.0])
        Cl_BB = np.array([1e-10, 1e-10, 1e-10])

        for nside in [16, 32, 64]:
            b_map = generate_gaussian_random_field(Cl_BB, l_values, nside)
            expected_npix = hp.nside2npix(nside)
            assert len(b_map) == expected_npix

    def test_reproducibility(self):
        """Test that same seed produces same result."""
        l_values = np.array([2.0, 3.0, 4.0])
        Cl_BB = np.array([1e-10, 1e-10, 1e-10])

        map1 = generate_gaussian_random_field(Cl_BB, l_values, nside=32, seed=123)
        map2 = generate_gaussian_random_field(Cl_BB, l_values, nside=32, seed=123)

        np.testing.assert_array_equal(map1, map2)


class TestInflationSynthetic:
    """Tests for generate_inflation_synthetic function."""

    def test_output_files_created(self):
        """Test that output files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_inflation_synthetic(r_value=0.01, output_dir=tmpdir, seed=42)

            assert os.path.exists(result['ground_truth_path'])
            assert os.path.exists(result['fits_path'])

    def test_ground_truth_content(self):
        """Test that ground truth JSON contains expected fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_inflation_synthetic(r_value=0.01, output_dir=tmpdir, seed=42)

            with open(result['ground_truth_path'], 'r') as f:
                data = json.load(f)

            assert data['model_type'] == 'inflation'
            assert 'r' in data['params']
            assert data['params']['r'] == 0.01
            assert 'l_values' in data
            assert 'Cl_BB' in data
            assert 'nside' in data
            assert 'seed' in data

    def test_fits_map_validity(self):
        """Test that FITS file contains valid HEALPix map."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_inflation_synthetic(r_value=0.01, output_dir=tmpdir, seed=42)

            # Read the FITS file
            b_map = hp.read_map(result['fits_path'])

            assert len(b_map) == hp.nside2npix(64)
            assert not np.all(b_map == 0)  # Map should not be all zeros


class TestPTSynthetic:
    """Tests for generate_pt_synthetic function."""

    def test_output_files_created(self):
        """Test that output files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_pt_synthetic(E_PT_value=1e15, output_dir=tmpdir, seed=43)

            assert os.path.exists(result['ground_truth_path'])
            assert os.path.exists(result['fits_path'])

    def test_ground_truth_content(self):
        """Test that ground truth JSON contains expected fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_pt_synthetic(E_PT_value=1e15, output_dir=tmpdir, seed=43)

            with open(result['ground_truth_path'], 'r') as f:
                data = json.load(f)

            assert data['model_type'] == 'phase_transition'
            assert 'E_PT' in data['params']
            assert data['params']['E_PT'] == 1e15
            assert 'l_values' in data
            assert 'Cl_BB' in data
            assert 'nside' in data
            assert 'seed' in data

    def test_fits_map_validity(self):
        """Test that FITS file contains valid HEALPix map."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_pt_synthetic(E_PT_value=1e15, output_dir=tmpdir, seed=43)

            # Read the FITS file
            b_map = hp.read_map(result['fits_path'])

            assert len(b_map) == hp.nside2npix(64)
            assert not np.all(b_map == 0)  # Map should not be all zeros

    def test_different_energy_scales(self):
        """Test that different energy scales produce different spectra."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result1 = generate_pt_synthetic(E_PT_value=1e14, output_dir=tmpdir, seed=43)
            result2 = generate_pt_synthetic(E_PT_value=1e16, output_dir=tmpdir, seed=43)

            with open(result1['ground_truth_path'], 'r') as f:
                data1 = json.load(f)
            with open(result2['ground_truth_path'], 'r') as f:
                data2 = json.load(f)

            assert data1['params']['E_PT'] == 1e14
            assert data2['params']['E_PT'] == 1e16

            # The amplitudes should be different
            assert data1['Cl_BB'] != data2['Cl_BB']


class TestSaveDataset:
    """Tests for save_dataset function."""

    def test_save_and_load(self):
        """Test that dataset can be saved and loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_data = {
                'test_key': 'test_value',
                'numbers': [1, 2, 3],
                'nested': {'a': 1, 'b': 2}
            }
            output_path = os.path.join(tmpdir, 'test_dataset.json')

            save_dataset(test_data, output_path)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                loaded_data = json.load(f)

            assert loaded_data == test_data