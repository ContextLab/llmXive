"""
Unit tests for the PSD validation and regularization module.
"""
import os
import json
import tempfile
import pytest
import numpy as np
from pathlib import Path

# Import the module under test
# Assuming the module is in code/preprocessing/psd_validator.py
# We need to add the parent directory to sys.path if running directly
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing.psd_validator import (
    is_symmetric,
    make_symmetric,
    is_positive_semi_definite,
    regularize_matrix,
    validate_and_regularize_matrix
)

class TestSymmetry:
    def test_symmetric_matrix(self):
        """Test detection of a symmetric matrix."""
        matrix = np.array([[1.0, 0.5], [0.5, 2.0]])
        assert is_symmetric(matrix) is True

    def test_non_symmetric_matrix(self):
        """Test detection of a non-symmetric matrix."""
        matrix = np.array([[1.0, 0.5], [0.6, 2.0]])
        assert is_symmetric(matrix) is False

    def test_make_symmetric(self):
        """Test enforcement of symmetry."""
        matrix = np.array([[1.0, 0.5], [0.6, 2.0]])
        symmetric = make_symmetric(matrix)
        expected = np.array([[1.0, 0.55], [0.55, 2.0]])
        assert np.allclose(symmetric, expected)

class TestPSD:
    def test_psd_matrix(self):
        """Test detection of a PSD matrix."""
        # Identity matrix is PSD
        matrix = np.eye(3)
        assert is_positive_semi_definite(matrix) is True

        # Positive definite matrix
        matrix = np.array([[2.0, 0.5], [0.5, 2.0]])
        assert is_positive_semi_definite(matrix) is True

    def test_non_psd_matrix(self):
        """Test detection of a non-PSD matrix."""
        # Matrix with negative eigenvalues
        matrix = np.array([[1.0, 2.0], [2.0, 1.0]])
        # Eigenvalues are 3 and -1 -> Not PSD
        assert is_positive_semi_definite(matrix) is False

    def test_zero_matrix(self):
        """Test zero matrix (PSD)."""
        matrix = np.zeros((3, 3))
        assert is_positive_semi_definite(matrix) is True

class TestRegularization:
    def test_already_psd_no_change(self):
        """Test that a PSD matrix is not modified."""
        matrix = np.eye(3)
        regularized, iterations = regularize_matrix(matrix)
        assert iterations == 0
        assert np.allclose(regularized, matrix)

    def test_regularization_fixes_non_psd(self):
        """Test that regularization fixes a non-PSD matrix."""
        # Create a matrix that is known to be non-PSD
        # A simple example: [[1, 2], [2, 1]] has eigenvalues 3, -1
        matrix = np.array([[1.0, 2.0], [2.0, 1.0]])
        
        regularized, iterations = regularize_matrix(matrix, epsilon=1e-4)
        
        assert iterations > 0
        assert is_positive_semi_definite(regularized) is True
        
        # Check that diagonal was increased
        original_diag = np.diag(matrix)
        reg_diag = np.diag(regularized)
        assert np.all(reg_diag >= original_diag)

    def test_regularization_limits(self):
        """Test that regularization respects max_iterations."""
        # Use a pathological matrix if needed, but standard logic should hold
        matrix = np.array([[1.0, 10.0], [10.0, 1.0]]) # Very negative eigenvalue
        regularized, iterations = regularize_matrix(matrix, max_iterations=2)
        
        # It might not be fully fixed in 2 iterations, but the function should return
        assert iterations == 2

class TestValidationPipeline:
    def test_validate_and_regularize(self, tmp_path):
        """Test the full validation pipeline."""
        # Create a non-PSD matrix
        matrix = np.array([[1.0, 2.0], [2.0, 1.0]])
        subject_id = "test_sub_001"
        anomaly_log = tmp_path / "anomalies.json"
        
        result_matrix, was_regularized = validate_and_regularize_matrix(
            matrix, subject_id, None, anomaly_log
        )
        
        assert was_regularized is True
        assert is_positive_semi_definite(result_matrix) is True
        
        # Check log file
        assert anomaly_log.exists()
        with open(anomaly_log, 'r') as f:
            log_data = json.load(f)
        
        assert "records" in log_data
        assert len(log_data["records"]) == 1
        assert log_data["records"][0]["subject_id"] == subject_id
        assert log_data["records"][0]["issue"] == "non_psd"

    def test_validate_already_psd(self, tmp_path):
        """Test validation on an already PSD matrix."""
        matrix = np.eye(3)
        subject_id = "test_sub_002"
        anomaly_log = tmp_path / "anomalies2.json"
        
        result_matrix, was_regularized = validate_and_regularize_matrix(
            matrix, subject_id, None, anomaly_log
        )
        
        assert was_regularized is False
        assert np.allclose(result_matrix, matrix)
        
        # Log file should exist but be empty or have no new records
        # (Implementation creates empty log if not exists, so check structure)
        assert anomaly_log.exists()
        with open(anomaly_log, 'r') as f:
            log_data = json.load(f)
        # Should have 0 records for this specific run if it was already valid
        # (Unless previous tests ran, but in a fresh tmp_path it should be 0)
        # Note: The implementation appends. If we run this test in isolation:
        assert len(log_data["records"]) == 0