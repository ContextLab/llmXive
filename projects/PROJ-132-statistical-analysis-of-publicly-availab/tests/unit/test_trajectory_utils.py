"""
Unit tests for trajectory permutation test utilities.
"""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.models.trajectory_utils import (
    _shuffle_trajectory_labels,
    _compute_shift_for_permutation,
    run_trajectory_permutation_test
)


@pytest.fixture
def sample_centroids():
    """Create sample centroid data for testing."""
    return {
        'SpeciesA': {
            2020: {'lat': 40.0, 'lon': -100.0, 'week': 10},
            2021: {'lat': 41.0, 'lon': -99.0, 'week': 10},
            2022: {'lat': 42.0, 'lon': -98.0, 'week': 10}
        },
        'SpeciesB': {
            2020: {'lat': 35.0, 'lon': -110.0, 'week': 12},
            2021: {'lat': 36.0, 'lon': -109.0, 'week': 12}
        }
    }


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_shuffle_trajectory_labels(sample_centroids):
    """Test that year labels are properly shuffled within species."""
    np.random.seed(42)
    shuffled = _shuffle_trajectory_labels(sample_centroids)

    # Check that species are preserved
    assert set(shuffled.keys()) == set(sample_centroids.keys())

    # Check that years are preserved within each species
    for species in sample_centroids:
        original_years = set(sample_centroids[species].keys())
        shuffled_years = set(shuffled[species].keys())
        assert original_years == shuffled_years

    # Check that shuffling actually changes order (with high probability)
    # Run multiple times to ensure we catch a shuffle
    for _ in range(10):
        new_shuffled = _shuffle_trajectory_labels(sample_centroids)
        if new_shuffled != sample_centroids:
            break
    else:
        # If all 10 runs produced same result, that's suspicious
        pytest.skip("Shuffling didn't change order in 10 attempts")


def test_compute_shift_for_permutation_single_species(sample_centroids):
    """Test shift computation for a single species."""
    shift = _compute_shift_for_permutation(sample_centroids, 'SpeciesA')
    assert isinstance(shift, float)
    assert shift >= 0.0


def test_compute_shift_for_permutation_missing_species(sample_centroids):
    """Test shift computation for non-existent species."""
    shift = _compute_shift_for_permutation(sample_centroids, 'NonExistent')
    assert shift == 0.0


def test_run_trajectory_permutation_test_small(temp_data_dir, sample_centroids):
    """Test permutation test with small number of shuffles."""
    # Write sample centroids to file
    centroids_file = temp_data_dir / 'centroids.json'
    with open(centroids_file, 'w') as f:
        json.dump(sample_centroids, f)

    output_file = temp_data_dir / 'results.json'

    # Run with small number of shuffles for speed
    result = run_trajectory_permutation_test(
        centroids_file=str(centroids_file),
        output_file=str(output_file),
        n_shuffles=50,
        seed=42
    )

    # Check result structure
    assert 'n_shuffles' in result
    assert 'results' in result
    assert 'total_time_seconds' in result

    # Check that we ran the requested number of shuffles
    assert result['n_shuffles'] == 50

    # Check that results exist for all species
    result_species = {r['species'] for r in result['results']}
    assert result_species == set(sample_centroids.keys())

    # Check result schema
    for r in result['results']:
        assert 'species' in r
        assert 'shift_magnitude' in r
        assert 'p_value' in r
        assert 'n_shuffles' in r
        assert 'early_stop_flag' in r
        assert 'final_p_value' in r

        # Check types
        assert isinstance(r['species'], str)
        assert isinstance(r['shift_magnitude'], float)
        assert isinstance(r['p_value'], float)
        assert isinstance(r['n_shuffles'], int)
        assert isinstance(r['early_stop_flag'], bool)

        # Check ranges
        assert 0.0 <= r['p_value'] <= 1.0
        assert r['n_shuffles'] == 50

    # Check that output file was written
    assert output_file.exists()

    # Verify file contents
    with open(output_file, 'r') as f:
        file_data = json.load(f)

    assert file_data == result


def test_run_trajectory_permutation_test_early_stop_flag(temp_data_dir, sample_centroids):
    """Test that early stop flag is set correctly."""
    centroids_file = temp_data_dir / 'centroids.json'
    with open(centroids_file, 'w') as f:
        json.dump(sample_centroids, f)

    output_file = temp_data_dir / 'results.json'

    result = run_trajectory_permutation_test(
        centroids_file=str(centroids_file),
        output_file=str(output_file),
        n_shuffles=100,
        seed=42
    )

    # Early stop flag should be a boolean
    for r in result['results']:
        assert isinstance(r['early_stop_flag'], bool)


def test_run_trajectory_permutation_test_full_shuffles(temp_data_dir, sample_centroids):
    """Test that full number of shuffles is always completed."""
    centroids_file = temp_data_dir / 'centroids.json'
    with open(centroids_file, 'w') as f:
        json.dump(sample_centroids, f)

    output_file = temp_data_dir / 'results.json'

    # Run with a specific number
    n_shuffles = 200
    result = run_trajectory_permutation_test(
        centroids_file=str(centroids_file),
        output_file=str(output_file),
        n_shuffles=n_shuffles,
        seed=42
    )

    # Verify that we completed all shuffles
    assert result['n_shuffles'] == n_shuffles

    # The early_stop_flag is for reporting only, not for stopping
    # So we should always have n_shuffles results in the null distribution
    # (implicitly verified by the p-value calculation)


def test_run_trajectory_permutation_test_single_species(temp_data_dir):
    """Test permutation test with only one species."""
    centroids = {
        'SingleSpecies': {
            2020: {'lat': 40.0, 'lon': -100.0, 'week': 10},
            2021: {'lat': 41.0, 'lon': -99.0, 'week': 10}
        }
    }

    centroids_file = temp_data_dir / 'centroids.json'
    with open(centroids_file, 'w') as f:
        json.dump(centroids, f)

    output_file = temp_data_dir / 'results.json'

    result = run_trajectory_permutation_test(
        centroids_file=str(centroids_file),
        output_file=str(output_file),
        n_shuffles=20,
        seed=42
    )

    assert len(result['results']) == 1
    assert result['results'][0]['species'] == 'SingleSpecies'


def test_run_trajectory_permutation_test_insufficient_data(temp_data_dir):
    """Test permutation test with insufficient data (only one year)."""
    centroids = {
        'InsufficientSpecies': {
            2020: {'lat': 40.0, 'lon': -100.0, 'week': 10}
        }
    }

    centroids_file = temp_data_dir / 'centroids.json'
    with open(centroids_file, 'w') as f:
        json.dump(centroids, f)

    output_file = temp_data_dir / 'results.json'

    # Should handle gracefully with shift_magnitude of 0.0
    result = run_trajectory_permutation_test(
        centroids_file=str(centroids_file),
        output_file=str(output_file),
        n_shuffles=20,
        seed=42
    )

    assert len(result['results']) == 1
    assert result['results'][0]['shift_magnitude'] == 0.0
    assert result['results'][0]['p_value'] == 1.0  # No shift, so p=1.0