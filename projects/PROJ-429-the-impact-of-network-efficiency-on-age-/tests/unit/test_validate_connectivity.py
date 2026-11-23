import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

from validate_connectivity_output import (
    load_connectivity_matrix,
    validate_matrix_dimensions,
    validate_non_nan_values,
    validate_connectivity_matrices
)

class TestValidateConnectivity:
    """Unit tests for connectivity output validation functions."""

    def test_load_connectivity_matrix_success(self, tmp_path):
        """Test successful loading of a valid .npy file."""
        test_matrix = np.array([[0.5, 0.2], [0.2, 0.5]])
        file_path = tmp_path / "test_matrix.npy"
        np.save(file_path, test_matrix)
        
        loaded = load_connectivity_matrix(file_path)
        np.testing.assert_array_equal(loaded, test_matrix)

    def test_load_connectivity_matrix_not_found(self, tmp_path):
        """Test loading a non-existent file raises FileNotFoundError."""
        file_path = tmp_path / "nonexistent.npy"
        with pytest.raises(FileNotFoundError):
            load_connectivity_matrix(file_path)

    def test_validate_matrix_dimensions_valid(self):
        """Test validation of a valid square matrix with correct dimensions."""
        matrix = np.random.rand(21, 21)
        is_valid, msg = validate_matrix_dimensions(matrix, Path("test.npy"))
        assert is_valid
        assert "Valid dimensions" in msg

    def test_validate_matrix_dimensions_non_square(self):
        """Test validation of a non-square matrix."""
        matrix = np.random.rand(10, 20)
        is_valid, msg = validate_matrix_dimensions(matrix, Path("test.npy"))
        assert not is_valid
        assert "must be square" in msg

    def test_validate_matrix_dimensions_invalid_size(self):
        """Test validation of a matrix with invalid dimensions."""
        matrix = np.random.rand(5, 5)  # 5 is not in VALID_DIMENSIONS
        is_valid, msg = validate_matrix_dimensions(matrix, Path("test.npy"))
        assert not is_valid
        assert "not in expected range" in msg

    def test_validate_non_nan_values_clean(self):
        """Test validation of a matrix without NaN values."""
        matrix = np.array([[0.5, 0.2], [0.2, 0.5]])
        is_valid, msg = validate_non_nan_values(matrix, Path("test.npy"))
        assert is_valid
        assert "No NaN or Inf values" in msg

    def test_validate_non_nan_values_with_nan(self):
        """Test validation of a matrix with NaN values."""
        matrix = np.array([[0.5, np.nan], [0.2, 0.5]])
        is_valid, msg = validate_non_nan_values(matrix, Path("test.npy"))
        assert not is_valid
        assert "NaN values" in msg

    def test_validate_non_nan_values_with_inf(self):
        """Test validation of a matrix with Inf values."""
        matrix = np.array([[0.5, np.inf], [0.2, 0.5]])
        is_valid, msg = validate_non_nan_values(matrix, Path("test.npy"))
        assert not is_valid
        assert "Inf values" in msg

    def test_validate_connectivity_matrices_empty_dir(self, tmp_path):
        """Test validation of an empty directory."""
        report = validate_connectivity_matrices(tmp_path)
        assert report["status"] == "warning"
        assert report["files_checked"] == 0

    def test_validate_connectivity_matrices_all_valid(self, tmp_path):
        """Test validation of a directory with all valid matrices."""
        # Create valid matrices
        for i in range(3):
            matrix = np.random.rand(21, 21)
            np.save(tmp_path / f"matrix_{i}.npy", matrix)
        
        report = validate_connectivity_matrices(tmp_path)
        assert report["status"] == "passed"
        assert report["files_checked"] == 3
        assert report["valid_count"] == 3
        assert report["invalid_count"] == 0

    def test_validate_connectivity_matrices_with_invalid(self, tmp_path):
        """Test validation of a directory with some invalid matrices."""
        # Create one valid matrix
        valid_matrix = np.random.rand(21, 21)
        np.save(tmp_path / "valid.npy", valid_matrix)
        
        # Create one invalid matrix (NaN)
        invalid_matrix = np.random.rand(21, 21)
        invalid_matrix[0, 0] = np.nan
        np.save(tmp_path / "invalid.npy", invalid_matrix)
        
        report = validate_connectivity_matrices(tmp_path)
        assert report["status"] == "failed"
        assert report["files_checked"] == 2
        assert report["valid_count"] == 1
        assert report["invalid_count"] == 1