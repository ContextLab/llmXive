"""
Unit tests for T013b: generate_multiL_pr_dataset.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# We mock the heavy dependencies to test the logic without running full diagonalization
# However, we ensure the file structure and output schema are correct.

@pytest.fixture
def mock_config():
    return {
        'W_LIST': [0.5, 1.0],
        'L_LIST': [100, 200],
        'NUM_REALIZATIONS': 2,
        'SEED': 42,
        'DATA_PROCESSED_DIR': '/tmp/test_data/processed'
    }

@pytest.fixture
def mock_hamiltonian():
    L = 100
    # Create a simple tridiagonal matrix for testing
    H = np.eye(L) * 0.0 + np.diag(np.ones(L-1), 1) + np.diag(np.ones(L-1), -1)
    return H

@pytest.fixture
def mock_eigenstates(mock_hamiltonian):
    # Return dummy eigenvalues and eigenvectors
    L = mock_hamiltonian.shape[0]
    eigvals = np.random.randn(L) * 0.5  # Some values near 0
    eigvecs = np.random.randn(L, L)
    return eigvals, eigvecs

def test_generate_multiL_pr_dataset_schema(mock_config, mock_hamiltonian, mock_eigenstates, tmp_path):
    """
    Test that the output file exists and matches the required schema:
    List of objects with W, L, realization_index, energy, pr.
    """
    # Patch dependencies
    with patch('code.generate_multiL_pr_dataset.get_config', return_value=mock_config), \
         patch('code.generate_multiL_pr_dataset.generate_hamiltonian', return_value=mock_hamiltonian), \
         patch('code.generate_multiL_pr_dataset.compute_eigenstates', return_value=mock_eigenstates), \
         patch('code.generate_multiL_pr_dataset.compute_participation_ratio', return_value=50.0), \
         patch('code.generate_multiL_pr_dataset.get_logger', return_value=MagicMock()), \
         patch('code.generate_multiL_pr_dataset.log_provenance_entry'), \
         patch('code.generate_multiL_pr_dataset.inject_log_residual'):

        # Set the output directory to tmp_path
        mock_config['DATA_PROCESSED_DIR'] = str(tmp_path)
        
        # Import and run
        from code.generate_multiL_pr_dataset import generate_multiL_pr_dataset
        
        output_path = generate_multiL_pr_dataset()
        
        assert os.path.exists(output_path), "Output file was not created"
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "Output must be a list"
        assert len(data) > 0, "Output must not be empty"
        
        # Check schema
        required_keys = {'W', 'L', 'realization_index', 'energy', 'pr'}
        for entry in data:
            assert set(entry.keys()) == required_keys, f"Entry missing keys: {entry.keys()}"
            assert isinstance(entry['W'], float)
            assert isinstance(entry['L'], int)
            assert isinstance(entry['realization_index'], int)
            assert isinstance(entry['energy'], float)
            assert isinstance(entry['pr'], float)

def test_generate_multiL_pr_dataset_combinations(mock_config, mock_hamiltonian, mock_eigenstates, tmp_path):
    """
    Test that all combinations of W and L are covered.
    """
    with patch('code.generate_multiL_pr_dataset.get_config', return_value=mock_config), \
         patch('code.generate_multiL_pr_dataset.generate_hamiltonian', return_value=mock_hamiltonian), \
         patch('code.generate_multiL_pr_dataset.compute_eigenstates', return_value=mock_eigenstates), \
         patch('code.generate_multiL_pr_dataset.compute_participation_ratio', return_value=50.0), \
         patch('code.generate_multiL_pr_dataset.get_logger', return_value=MagicMock()), \
         patch('code.generate_multiL_pr_dataset.log_provenance_entry'), \
         patch('code.generate_multiL_pr_dataset.inject_log_residual'):

        mock_config['DATA_PROCESSED_DIR'] = str(tmp_path)
        
        from code.generate_multiL_pr_dataset import generate_multiL_pr_dataset
        output_path = generate_multiL_pr_dataset()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Check that we have entries for every W, L, and realization
        combinations = set()
        for entry in data:
            combinations.add((entry['W'], entry['L'], entry['realization_index']))
        
        expected_combinations = set()
        for W in mock_config['W_LIST']:
            for L in mock_config['L_LIST']:
                for r in range(mock_config['NUM_REALIZATIONS']):
                    expected_combinations.add((float(W), int(L), int(r)))
        
        assert combinations == expected_combinations, f"Missing combinations: {expected_combinations - combinations}"