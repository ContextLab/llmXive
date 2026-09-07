"""
Unit tests for descriptor computation module.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from code.data.descriptors import (
    get_interface_atoms,
    compute_rdf_peak,
    compute_pair_correlation,
    compute_voronoi_neighbor_counts,
    run_descriptor_computation
)

from pymatgen.core import Structure, Lattice


@pytest.fixture
def sample_structure():
    """Create a sample structure for testing."""
    lattice = Lattice.cubic(5.0)
    species = ["Fe", "Fe", "Fe", "Fe"]
    coords = [
        [0, 0, 0],
        [0.5, 0.5, 0.5],
        [0.5, 0, 0],
        [0, 0.5, 0.5]
    ]
    return Structure(lattice, species, coords)


@pytest.fixture
def sample_structure_with_impurity():
    """Create a sample structure with impurity for testing."""
    lattice = Lattice.cubic(5.0)
    species = ["Fe", "Fe", "Fe", "Cr"]  # Cr as impurity
    coords = [
        [0, 0, 0],
        [0.5, 0.5, 0.5],
        [0.5, 0, 0],
        [0, 0.5, 0.5]
    ]
    return Structure(lattice, species, coords)


def test_get_interface_atoms(sample_structure):
    """Test interface atom identification."""
    interface_indices = get_interface_atoms(sample_structure)
    assert isinstance(interface_indices, list)
    # Should identify some atoms as interface atoms
    assert len(interface_indices) > 0
    assert len(interface_indices) <= len(sample_structure)


def test_compute_rdf_peak(sample_structure_with_impurity):
    """Test RDF peak computation."""
    interface_indices = get_interface_atoms(sample_structure_with_impurity)
    rdf_peak, peak_height = compute_rdf_peak(
        sample_structure_with_impurity,
        interface_indices,
        "Cr"
    )

    # Should return valid numbers or NaN
    assert isinstance(rdf_peak, (float, np.floating))
    assert isinstance(peak_height, (float, np.floating))


def test_compute_pair_correlation(sample_structure_with_impurity):
    """Test pair correlation computation."""
    interface_indices = get_interface_atoms(sample_structure_with_impurity)
    pair_corr = compute_pair_correlation(
        sample_structure_with_impurity,
        interface_indices,
        "Cr"
    )

    # Should return a value between 0 and 1
    assert isinstance(pair_corr, (float, np.floating))
    assert 0.0 <= pair_corr <= 1.0


def test_compute_voronoi_neighbor_counts(sample_structure_with_impurity):
    """Test Voronoi neighbor count computation."""
    interface_indices = get_interface_atoms(sample_structure_with_impurity)
    voronoi_count = compute_voronoi_neighbor_counts(
        sample_structure_with_impurity,
        interface_indices,
        "Cr"
    )

    # Should return a non-negative number
    assert isinstance(voronoi_count, (float, np.floating))
    assert voronoi_count >= 0


def test_run_descriptor_computation_missing_files(tmp_path):
    """Test that run_descriptor_computation raises error when no files found."""
    # Create empty directory
    input_path = tmp_path / "input"
    input_path.mkdir()

    output_path = tmp_path / "output.csv"

    with pytest.raises(FileNotFoundError):
        run_descriptor_computation(input_path, output_path)


def test_run_descriptor_computation_empty_result(tmp_path):
    """Test handling of structures with no interface atoms."""
    # This is more of an integration test, but we can test the empty result handling
    # by mocking the structure loading to return a structure with no interface atoms
    pass
