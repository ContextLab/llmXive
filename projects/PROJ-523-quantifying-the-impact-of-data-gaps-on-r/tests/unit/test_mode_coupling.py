"""
Unit tests for mode_coupling.py.
"""
import numpy as np
import healpy as hp
import pytest
import os
from pathlib import Path

# Import the functions to test
from code.analysis.mode_coupling import compute_mode_coupling_matrix, calculate_leakage_matrix_for_realization, save_leakage_matrix
from code.config import N_SIDE, DATA_DERIVED_DIR
from code.simulation.utils import generate_random_mask


def test_compute_mode_coupling_matrix_shape():
    """Test that the output matrix has the correct shape."""
    nside = 32 # Use small Nside for speed
    l_max = 10
    mask = generate_random_mask(nside, 0.1, seed=42)

    matrix = compute_mode_coupling_matrix(mask, l_max)

    assert matrix.shape == (l_max + 1, l_max + 1), f"Expected shape ({l_max+1}, {l_max+1}), got {matrix.shape}"
    assert not np.any(np.isnan(matrix)), "Matrix contains NaN values"
    assert not np.any(np.isinf(matrix)), "Matrix contains Inf values"


def test_mode_coupling_matrix_symmetry():
    """Test that the mode-coupling matrix is symmetric (M_ell,ell' = M_ell',ell)."""
    nside = 32
    l_max = 10
    mask = generate_random_mask(nside, 0.1, seed=42)

    matrix = compute_mode_coupling_matrix(mask, l_max)

    # Check symmetry
    assert np.allclose(matrix, matrix.T), "Mode-coupling matrix is not symmetric"


def test_mode_coupling_matrix_positive_diagonal():
    """Test that the diagonal elements are positive (self-coupling)."""
    nside = 32
    l_max = 10
    mask = generate_random_mask(nside, 0.1, seed=42)

    matrix = compute_mode_coupling_matrix(mask, l_max)

    # Diagonal elements should be positive
    assert np.all(np.diag(matrix) > 0), "Diagonal elements should be positive"


def test_save_leakage_matrix(tmp_path):
    """Test saving the leakage matrix to disk."""
    nside = 32
    l_max = 10
    mask = generate_random_mask(nside, 0.1, seed=42)

    matrix = compute_mode_coupling_matrix(mask, l_max)
    realization_id = "test_001"

    output_dir = Path(tmp_path)
    output_path = save_leakage_matrix(matrix, realization_id, output_dir)

    assert os.path.exists(output_path), f"Saved file not found at {output_path}"

    # Load and verify
    loaded_matrix = np.load(output_path)
    assert np.allclose(matrix, loaded_matrix), "Loaded matrix does not match saved matrix"