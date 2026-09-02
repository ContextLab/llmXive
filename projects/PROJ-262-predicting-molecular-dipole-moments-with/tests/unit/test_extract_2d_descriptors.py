import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

# Import the function to test
from code.data.extract_2d_descriptors import compute_coulomb_matrix, extract_2d_features, MAX_ATOMS

def test_coulomb_matrix_symmetry():
    """Test that the Topological Coulomb Matrix is symmetric."""
    atoms = ['C', 'O', 'H', 'H', 'H', 'H'] # Methanol
    coords = np.array([
        [0.0, 0.0, 0.0],
        [1.4, 0.0, 0.0],
        [-0.5, 0.9, 0.0],
        [-0.5, -0.9, 0.0],
        [0.0, 0.0, 1.1],
        [0.0, 0.0, -1.1]
    ])
    
    matrix = compute_coulomb_matrix(atoms, coords)
    
    # Check symmetry
    assert np.allclose(matrix, matrix.T), "Coulomb matrix must be symmetric"
    
    # Check diagonal is non-zero (0.5 * Z^2.4)
    assert matrix[0, 0] > 0, "Diagonal elements must be non-zero"

def test_coulomb_matrix_padding():
    """Test that the matrix is padded to MAX_ATOMS x MAX_ATOMS."""
    atoms = ['C', 'H', 'H', 'H', 'H'] # Methane
    coords = np.random.rand(5, 3)
    
    matrix = compute_coulomb_matrix(atoms, coords)
    
    assert matrix.shape == (MAX_ATOMS, MAX_ATOMS), f"Matrix shape must be {MAX_ATOMS}x{MAX_ATOMS}"
    # Check that the padded region is zero
    assert np.all(matrix[5:, :] == 0), "Padded rows must be zero"
    assert np.all(matrix[:, 5:] == 0), "Padded columns must be zero"

def test_morgan_fingerprint_length():
    """Test that the Morgan fingerprint has the correct length."""
    from code.data.extract_2d_descriptors import FINGERPRINT_BITS
    
    atoms = ['C', 'O']
    coords = np.array([[0.0, 0.0, 0.0], [1.2, 0.0, 0.0]])
    
    features = extract_2d_features("test_mol", atoms, coords)
    
    fp = features['features_2d_fp']
    assert len(fp) == FINGERPRINT_BITS, f"Fingerprint length must be {FINGERPRINT_BITS}"
    
    # Check values are 0 or 1
    assert all(x in [0.0, 1.0] for x in fp), "Fingerprint bits must be 0 or 1"

def test_coulomb_matrix_flattening():
    """Test that the Coulomb matrix is flattened correctly."""
    atoms = ['C', 'H']
    coords = np.array([[0.0, 0.0, 0.0], [1.1, 0.0, 0.0]])
    
    features = extract_2d_features("test_mol", atoms, coords)
    
    cm = features['features_2d_cm']
    expected_length = MAX_ATOMS * MAX_ATOMS
    assert len(cm) == expected_length, f"Flattened matrix length must be {expected_length}"

def test_extract_2d_features_handles_empty_atoms():
    """Test handling of empty molecule (edge case)."""
    atoms = []
    coords = np.array([]).reshape(0, 3)
    
    # This should not crash, but return a zero matrix
    features = extract_2d_features("empty_mol", atoms, coords)
    
    assert features['features_2d_cm'] == [0.0] * (MAX_ATOMS * MAX_ATOMS)
    assert len(features['features_2d_fp']) == 2048 # Should still be valid length

def test_integration_with_pandas():
    """Test that the output can be loaded into a pandas DataFrame."""
    atoms = ['C', 'O', 'H', 'H', 'H']
    coords = np.random.rand(5, 3)
    
    features = extract_2d_features("test_id", atoms, coords)
    
    df = pd.DataFrame([features])
    
    assert 'molecule_id' in df.columns
    assert 'features_2d_fp' in df.columns
    assert 'features_2d_cm' in df.columns
    assert len(df) == 1