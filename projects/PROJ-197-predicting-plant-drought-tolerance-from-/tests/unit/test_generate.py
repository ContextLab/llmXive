"""
Unit tests for data generation module.
"""
import os
import sys
import numpy as np
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from data.generate import generate_synthetic_phylogenetic_matrix, SPECIES_LIST, RANDOM_SEED

@pytest.fixture
def setup_validation_mode(monkeypatch):
    """Fixture to set VALIDATION_MODE to True for testing."""
    import config
    monkeypatch.setattr(config, 'get_config', lambda: {'VALIDATION_MODE': True})
    # Ensure directories exist
    os.makedirs("data/processed", exist_ok=True)
    yield
    # Cleanup
    if os.path.exists("data/processed/synthetic_phylo_matrix.npy"):
        os.remove("data/processed/synthetic_phylo_matrix.npy")

def test_generate_synthetic_phylogenetic_matrix_shape(setup_validation_mode):
    """Test that the generated matrix has the correct shape."""
    output_path = generate_synthetic_phylogenetic_matrix()
    assert os.path.exists(output_path), "Output file should exist."

    matrix = np.load(output_path)
    n_species = len(SPECIES_LIST)
    assert matrix.shape == (n_species, n_species), f"Matrix shape should be ({n_species}, {n_species})."

def test_generate_synthetic_phylogenetic_matrix_diagonal(setup_validation_mode):
    """Test that the diagonal of the matrix is zero."""
    output_path = generate_synthetic_phylogenetic_matrix()
    matrix = np.load(output_path)

    assert np.allclose(np.diag(matrix), 0.0), "Diagonal elements must be zero."

def test_generate_synthetic_phylogenetic_matrix_symmetry(setup_validation_mode):
    """Test that the matrix is symmetric."""
    output_path = generate_synthetic_phylogenetic_matrix()
    matrix = np.load(output_path)

    assert np.allclose(matrix, matrix.T), "Matrix must be symmetric."

def test_generate_synthetic_phylogenetic_matrix_range(setup_validation_mode):
    """Test that off-diagonal elements are within [0.01, 1.0]."""
    output_path = generate_synthetic_phylogenetic_matrix()
    matrix = np.load(output_path)

    # Get off-diagonal elements
    off_diag = matrix[np.triu_indices_from(matrix, k=1)]

    assert np.all(off_diag >= 0.01), "Off-diagonal elements must be >= 0.01."
    assert np.all(off_diag <= 1.0), "Off-diagonal elements must be <= 1.0."

def test_generate_synthetic_phylogenetic_matrix_determinism(setup_validation_mode):
    """Test that the generation is deterministic with the same seed."""
    # First run
    output_path_1 = generate_synthetic_phylogenetic_matrix()
    matrix_1 = np.load(output_path_1)

    # Second run (should be identical due to seed)
    output_path_2 = generate_synthetic_phylogenetic_matrix()
    matrix_2 = np.load(output_path_2)

    assert np.array_equal(matrix_1, matrix_2), "Matrix generation must be deterministic with the same seed."