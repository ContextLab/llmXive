"""
Unit tests for synthetic data generation (T008).

These tests verify that the synthetic generator:
1. Produces data with the correct schema
2. Applies the controlled deviation to NFW concentration
3. Uses the fixed random seed for reproducibility
4. Writes a valid HDF5 file to the expected path
"""
import os
import sys
import tempfile
import h5py
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.synthetic_generator import (
    generate_halo_properties,
    save_to_hdf5,
    generate_synthetic_halos,
    RANDOM_SEED,
    NUM_HALOS,
    DEVIATION_OFFSET,
    BASE_CONCENTRATION_MEAN,
    MIN_PARTICLES,
    MAX_PARTICLES,
    BOX_SIZE
)


class TestSyntheticDataGeneration:
    """Tests for synthetic halo data generation."""

    def test_generate_halo_properties_structure(self):
        """Test that generate_halo_properties returns correct keys."""
        data = generate_halo_properties(10, seed=RANDOM_SEED)

        required_keys = [
            'halo_id', 'particle_count', 'mass',
            'position_x', 'position_y', 'position_z',
            'velocity_x', 'velocity_y', 'velocity_z',
            'concentration', 'spin', 'shape'
        ]

        for key in required_keys:
            assert key in data, f"Missing required key: {key}"
            assert isinstance(data[key], np.ndarray), f"Key {key} is not an array"

    def test_generate_halo_properties_count(self):
        """Test that the correct number of halos is generated."""
        n_test = 50
        data = generate_halo_properties(n_test, seed=RANDOM_SEED)

        assert len(data['halo_id']) == n_test
        assert len(data['mass']) == n_test
        assert len(data['concentration']) == n_test

    def test_particle_count_range(self):
        """Test that particle counts are within expected bounds."""
        data = generate_halo_properties(1000, seed=RANDOM_SEED)
        counts = data['particle_count']

        assert np.all(counts >= MIN_PARTICLES), "Some particle counts below minimum"
        assert np.all(counts <= MAX_PARTICLES), "Some particle counts above maximum"

    def test_concentration_deviation_offset(self):
        """
        Test that the NFW concentration has the controlled deviation offset applied.
        The mean concentration should be approximately BASE_CONCENTRATION_MEAN + DEVIATION_OFFSET.
        """
        n_halos = 10000  # Large sample for accurate mean estimation
        data = generate_halo_properties(n_halos, seed=RANDOM_SEED)
        concentrations = data['concentration']

        expected_mean = BASE_CONCENTRATION_MEAN + DEVIATION_OFFSET
        actual_mean = np.mean(concentrations)

        # Allow for some statistical variation (3 standard errors)
        std_error = BASE_CONCENTRATION_STD / np.sqrt(n_halos)
        tolerance = 3 * std_error

        assert abs(actual_mean - expected_mean) < tolerance, \
            f"Mean concentration {actual_mean:.4f} does not match expected {expected_mean:.4f} " \
            f"(tolerance: {tolerance:.4f})"

    def test_concentration_positive(self):
        """Test that all concentrations are positive."""
        data = generate_halo_properties(1000, seed=RANDOM_SEED)
        assert np.all(data['concentration'] > 0), "Found non-positive concentration"

    def test_concentration_clipped_range(self):
        """Test that concentrations are clipped to [1.0, 50.0]."""
        data = generate_halo_properties(10000, seed=RANDOM_SEED)
        concentrations = data['concentration']

        assert np.all(concentrations >= 1.0), "Concentration below lower bound"
        assert np.all(concentrations <= 50.0), "Concentration above upper bound"

    def test_positions_within_box(self):
        """Test that all positions are within the simulation box."""
        data = generate_halo_properties(1000, seed=RANDOM_SEED)

        for i, pos_key in enumerate(['position_x', 'position_y', 'position_z']):
            assert np.all(data[pos_key] >= 0), f"{pos_key} has negative values"
            assert np.all(data[pos_key] <= BOX_SIZE), f"{pos_key} exceeds box size"

    def test_spin_parameter_range(self):
        """Test that spin parameters are in valid range [0.001, 0.5]."""
        data = generate_halo_properties(1000, seed=RANDOM_SEED)
        spins = data['spin']

        assert np.all(spins >= 0.001), "Spin below minimum"
        assert np.all(spins <= 0.5), "Spin above maximum"

    def test_shape_parameter_range(self):
        """Test that shape parameters are in valid range [0.5, 1.0]."""
        data = generate_halo_properties(1000, seed=RANDOM_SEED)
        shapes = data['shape']

        assert np.all(shapes >= 0.5), "Shape below minimum"
        assert np.all(shapes <= 1.0), "Shape above maximum"

    def test_reproducibility_with_seed(self):
        """Test that the same seed produces identical results."""
        data1 = generate_halo_properties(100, seed=RANDOM_SEED)
        data2 = generate_halo_properties(100, seed=RANDOM_SEED)

        for key in data1.keys():
            np.testing.assert_array_equal(data1[key], data2[key],
                                        err_msg=f"Arrays differ for key {key}")

    def test_save_to_hdf5_creates_file(self):
        """Test that save_to_hdf5 creates a valid HDF5 file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_halos.h5")
            data = generate_halo_properties(10, seed=RANDOM_SEED)

            save_to_hdf5(data, output_path)

            assert os.path.exists(output_path), "HDF5 file was not created"

            with h5py.File(output_path, 'r') as f:
                # Check file attributes
                assert f.attrs['generator'] == 'synthetic_generator'
                assert f.attrs['seed'] == RANDOM_SEED
                assert f.attrs['deviation_offset'] == DEVIATION_OFFSET

                # Check datasets exist
                for key in data.keys():
                    assert key in f, f"Missing dataset: {key}"

    def test_save_to_hdf5_correct_data(self):
        """Test that the saved HDF5 file contains the correct data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_halos.h5")
            data = generate_halo_properties(10, seed=RANDOM_SEED)

            save_to_hdf5(data, output_path)

            with h5py.File(output_path, 'r') as f:
                for key in data.keys():
                    np.testing.assert_array_equal(
                        f[key][()],
                        data[key],
                        err_msg=f"Data mismatch for key {key}"
                    )

    def test_generate_synthetic_halos_default_path(self):
        """Test that generate_synthetic_halos uses the default path when not specified."""
        # This test just verifies the function runs without error
        # We don't check the actual file creation in the default location
        # to avoid polluting the workspace during unit tests
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = os.path.join(tmpdir, "custom_halos.h5")
            result_path = generate_synthetic_halos(output_path=custom_path)

            assert result_path == custom_path
            assert os.path.exists(result_path)

    def test_halo_id_sequence(self):
        """Test that halo IDs are a sequential range starting from 0."""
        data = generate_halo_properties(100, seed=RANDOM_SEED)
        expected_ids = np.arange(100)
        np.testing.assert_array_equal(data['halo_id'], expected_ids)

    def test_mass_positive(self):
        """Test that all masses are positive."""
        data = generate_halo_properties(1000, seed=RANDOM_SEED)
        assert np.all(data['mass'] > 0), "Found non-positive mass"

    def test_mass_minimum_bound(self):
        """Test that masses respect the minimum particle mass constraint."""
        data = generate_halo_properties(1000, seed=RANDOM_SEED)
        min_mass = MIN_PARTICLES * PARTICLE_MASS
        assert np.all(data['mass'] >= min_mass), "Mass below minimum constraint"

class TestSyntheticSchemaValidation:
    """Tests for schema validation of synthetic data."""

    def test_dtype_consistency(self):
        """Test that all arrays have consistent dtypes."""
        data = generate_halo_properties(100, seed=RANDOM_SEED)

        # Integer fields
        int_fields = ['halo_id', 'particle_count']
        for field in int_fields:
            assert np.issubdtype(data[field].dtype, np.integer), \
                f"{field} should be integer type, got {data[field].dtype}"

        # Float fields
        float_fields = ['mass', 'position_x', 'position_y', 'position_z',
                       'velocity_x', 'velocity_y', 'velocity_z',
                       'concentration', 'spin', 'shape']
        for field in float_fields:
            assert np.issubdtype(data[field].dtype, np.floating), \
                f"{field} should be float type, got {data[field].dtype}"

    def test_array_dimensions(self):
        """Test that all arrays have the correct dimensions."""
        n_halos = 500
        data = generate_halo_properties(n_halos, seed=RANDOM_SEED)

        # 1D arrays
        for key in data.keys():
            assert data[key].ndim == 1, f"{key} should be 1D, got {data[key].ndim}D"
            assert len(data[key]) == n_halos, \
                f"{key} length {len(data[key])} != {n_halos}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])