"""
Unit tests for synthetic data generator (T008)
"""
import os
import sys
import tempfile
import numpy as np
import h5py
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.synthetic_generator import (
    generate_halo_properties,
    save_to_hdf5,
    generate_synthetic_halos,
    DEVIATION_OFFSET,
    RANDOM_SEED,
    NUM_HALOS,
    MIN_PARTICLES,
    MAX_PARTICLES
)

def test_synthetic_data_deviation_injection():
    """
    Test that the synthetic generator applies the controlled deviation offset
    to the NFW concentration parameter as specified in T008.
    """
    data = generate_halo_properties(n_halos=1000, seed=RANDOM_SEED)
    concentrations = data['concentration']

    # The mean concentration should be offset from the base mean by DEVIATION_OFFSET
    base_mean = 10.0
    expected_mean = base_mean + DEVIATION_OFFSET

    # Allow some tolerance for random variation (3 standard errors)
    tolerance = 3 * 2.0 / np.sqrt(1000)  # 3 * std / sqrt(n)

    assert abs(np.mean(concentrations) - expected_mean) < tolerance, \
        f"Mean concentration {np.mean(concentrations):.2f} not within expected range " \
        f"around {expected_mean:.2f} +/- {tolerance:.2f}"

    # Verify all concentrations are positive and within physical bounds
    assert np.all(concentrations > 0), "Concentrations must be positive"
    assert np.all(concentrations <= 50.0), "Concentrations must not exceed 50"

def test_synthetic_schema_validation():
    """
    Test that the generated data conforms to the expected HDF5 schema.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_synthetic.h5")

        data = generate_halo_properties(n_halos=100, seed=RANDOM_SEED)
        save_to_hdf5(data, output_path)

        # Verify file exists
        assert os.path.exists(output_path), "Output file was not created"

        # Verify HDF5 structure
        with h5py.File(output_path, 'r') as f:
            # Check metadata attributes
            assert f.attrs['generator'] == 'synthetic_generator'
            assert f.attrs['seed'] == RANDOM_SEED
            assert f.attrs['deviation_offset'] == DEVIATION_OFFSET
            assert f.attrs['num_halos'] == 100
            assert f.attrs['box_size'] == 100.0

            # Check required datasets exist
            required_keys = [
                'halo_id', 'particle_count', 'mass',
                'position_x', 'position_y', 'position_z',
                'velocity_x', 'velocity_y', 'velocity_z',
                'concentration', 'spin', 'shape'
            ]

            for key in required_keys:
                assert key in f, f"Missing required dataset: {key}"
                assert len(f[key]) == 100, f"Dataset {key} has wrong length"

            # Verify data types and ranges
            assert f['particle_count'][0] >= MIN_PARTICLES
            assert f['particle_count'][0] <= MAX_PARTICLES
            assert f['concentration'][0] > 0
            assert f['spin'][0] > 0
            assert 0.5 <= f['shape'][0] <= 1.0

def test_particle_count_bounds():
    """
    Test that particle counts respect the minimum threshold (>=300).
    """
    data = generate_halo_properties(n_halos=1000, seed=RANDOM_SEED)
    particle_counts = data['particle_count']

    assert np.all(particle_counts >= MIN_PARTICLES), \
        f"Some particle counts ({np.min(particle_counts)}) are below minimum {MIN_PARTICLES}"
    assert np.all(particle_counts <= MAX_PARTICLES), \
        f"Some particle counts ({np.max(particle_counts)}) exceed maximum {MAX_PARTICLES}"

def test_reproducibility():
    """
    Test that the same seed produces identical results.
    """
    data1 = generate_halo_properties(n_halos=100, seed=42)
    data2 = generate_halo_properties(n_halos=100, seed=42)

    for key in data1:
        np.testing.assert_array_equal(data1[key], data2[key],
                                    err_msg=f"Arrays for {key} differ between runs with same seed")

def test_output_file_creation():
    """
    Test that generate_synthetic_halos creates the expected output file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_output.h5")
        result_path = generate_synthetic_halos(output_path)

        assert result_path == output_path
        assert os.path.exists(output_path)

        # Verify it's a valid HDF5 file
        with h5py.File(output_path, 'r'):
            pass  # If we can open it, it's valid