"""
Unit tests for connectivity output validation.

Tests the validate_connectivity_output function and related validation logic.
"""
import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import os

# Import the functions to test
from validate_connectivity_output import (
    validate_matrix_shape,
    validate_matrix_values,
    validate_matrix_symmetry,
    validate_channel_names,
    validate_connectivity_output,
    STANDARD_10_20_ELECTRODES
)

class TestMatrixShapeValidation:
    """Test matrix shape validation."""
    
    def test_square_matrix_correct_size(self):
        """Test that a square matrix of correct size passes."""
        matrix = np.eye(28)
        valid, msg = validate_matrix_shape(matrix, 28)
        assert valid
        assert "Shape valid" in msg
    
    def test_non_square_matrix(self):
        """Test that a non-square matrix fails."""
        matrix = np.random.rand(30, 28)
        valid, msg = validate_matrix_shape(matrix, 28)
        assert not valid
        assert "not square" in msg
    
    def test_wrong_size_matrix(self):
        """Test that a matrix of wrong size fails."""
        matrix = np.eye(30)
        valid, msg = validate_matrix_shape(matrix, 28)
        assert not valid
        assert "size" in msg

class TestMatrixValueValidation:
    """Test matrix value validation."""
    
    def test_valid_coherence_values(self):
        """Test that valid coherence values pass."""
        matrix = np.eye(28) * 0.5 + np.eye(28) * 0.5  # Values between 0 and 1
        np.fill_diagonal(matrix, 1.0)
        valid, msg = validate_matrix_values(matrix)
        assert valid
        assert "Values valid" in msg
    
    def test_nan_values_fail(self):
        """Test that NaN values fail."""
        matrix = np.eye(28)
        matrix[0, 1] = np.nan
        valid, msg = validate_matrix_values(matrix)
        assert not valid
        assert "NaN" in msg
    
    def test_values_out_of_range_fail(self):
        """Test that values outside [0, 1] fail."""
        matrix = np.eye(28) * 1.5
        valid, msg = validate_matrix_values(matrix)
        assert not valid
        assert "out of range" in msg
    
    def test_diagonal_not_one_fails(self):
        """Test that diagonal values not close to 1 fail."""
        matrix = np.eye(28) * 0.5
        valid, msg = validate_matrix_values(matrix)
        assert not valid
        assert "Diagonal" in msg

class TestMatrixSymmetryValidation:
    """Test matrix symmetry validation."""
    
    def test_symmetric_matrix_passes(self):
        """Test that a symmetric matrix passes."""
        matrix = np.random.rand(28, 28)
        matrix = (matrix + matrix.T) / 2  # Make symmetric
        np.fill_diagonal(matrix, 1.0)
        valid, msg = validate_matrix_symmetry(matrix)
        assert valid
        assert "Symmetry valid" in msg
    
    def test_asymmetric_matrix_fails(self):
        """Test that an asymmetric matrix fails."""
        matrix = np.random.rand(28, 28)
        valid, msg = validate_matrix_symmetry(matrix)
        assert not valid
        assert "not symmetric" in msg

class TestConnectivityOutputValidation:
    """Test the full connectivity output validation."""
    
    def test_empty_directory(self):
        """Test validation on an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            results = validate_connectivity_output(output_dir)
            assert results["total_files"] == 0
            assert results["valid_files"] == 0
            assert "error" in results
    
    def test_invalid_matrix_file(self):
        """Test validation with an invalid matrix file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            # Create an invalid matrix (wrong size)
            invalid_matrix = np.random.rand(10, 10)
            np.save(output_dir / "invalid.npy", invalid_matrix)
            
            results = validate_connectivity_output(output_dir)
            assert results["total_files"] == 1
            assert results["invalid_files"] == 1
            assert results["valid_files"] == 0

class TestStandardElectrodes:
    """Test the standard 10-20 electrode list."""
    
    def test_correct_number_of_electrodes(self):
        """Test that we have the expected number of electrodes."""
        assert len(STANDARD_10_20_ELECTRODES) == 28
    
    def test_all_standard_electrodes_present(self):
        """Test that all standard electrodes are present."""
        expected = ['FP1', 'FP2', 'F7', 'F3', 'FZ', 'F4', 'F8',
                   'FC5', 'FC1', 'FC2', 'FC6',
                   'T7', 'C3', 'CZ', 'C4', 'T8',
                   'CP5', 'CP1', 'CP2', 'CP6',
                   'P7', 'P3', 'PZ', 'P4', 'P8',
                   'O1', 'OZ', 'O2']
        assert set(STANDARD_10_20_ELECTRODES) == set(expected)
