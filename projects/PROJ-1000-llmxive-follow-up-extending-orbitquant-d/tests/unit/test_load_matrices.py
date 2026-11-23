"""
Unit tests for the matrix loader functionality (T028).

These tests verify that load_matrices.py correctly:
- Loads matrices from a valid JSON file
- Raises appropriate errors for missing files
- Raises appropriate errors for invalid data structures
- Validates matrix properties (shape, dtype, NaN/Inf)
"""

import os
import json
import tempfile
import pytest
import numpy as np
from pathlib import Path

# Import the module under test
from analysis.load_matrices import (
    MatrixLoader,
    load_matrices_from_path,
    verify_matrices,
    EXPECTED_MATRIX_COUNT,
    EXPECTED_KEYS
)
from config import Config

# Sample valid clustering report data
def create_valid_clustering_report(num_matrices=EXPECTED_MATRIX_COUNT, 
                                   matrix_shape=(64, 64)):
    """Create a valid clustering report for testing."""
    matrices = []
    for _ in range(num_matrices):
        # Create a valid rotation matrix (orthogonal-ish, unit norm-ish)
        matrix = np.random.randn(*matrix_shape).astype(np.float32)
        # Normalize to unit norm for each row
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0  # Avoid division by zero
        matrix = matrix / norms
        matrices.append(matrix.tolist())
    
    return {
        'layers': ['layer1', 'layer2'],
        'subsets': [{'id': 0, 'size': 100}, {'id': 1, 'size': 200}],
        'boundaries': [0.5, 1.0, 1.5],
        'matrices': matrices
    }

class TestMatrixLoader:
    """Tests for the MatrixLoader class."""
    
    def test_load_from_valid_file(self, tmp_path):
        """Test loading matrices from a valid JSON file."""
        # Create a temporary valid clustering report
        report_data = create_valid_clustering_report()
        report_file = tmp_path / "clustering_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f)
        
        # Load matrices
        loader = MatrixLoader()
        matrices = loader.load(str(report_file))
        
        # Verify results
        assert len(matrices) == EXPECTED_MATRIX_COUNT
        assert all(isinstance(m, np.ndarray) for m in matrices)
        assert all(m.shape == (64, 64) for m in matrices)
        assert all(m.dtype == np.float32 for m in matrices)
        
        # Verify metadata
        metadata = loader.get_metadata()
        assert 'layers' in metadata
        assert 'matrices' in metadata
    
    def test_load_from_default_path(self, tmp_path, monkeypatch):
        """Test loading from the default config path."""
        # Create a valid report at the default location
        report_data = create_valid_clustering_report()
        default_path = tmp_path / "data" / "processed" / "clustering_report.json"
        default_path.parent.mkdir(parents=True)
        
        with open(default_path, 'w') as f:
            json.dump(report_data, f)
        
        # Monkeypatch the config to use our temp directory
        config = Config()
        config._clustering_report_path = str(default_path)
        
        loader = MatrixLoader(config=config)
        matrices = loader.load()
        
        assert len(matrices) == EXPECTED_MATRIX_COUNT
    
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        loader = MatrixLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/path/clustering_report.json")
    
    def test_missing_required_keys(self, tmp_path):
        """Test that ValueError is raised for missing required keys."""
        # Create a report with missing keys
        report_data = {
            'layers': ['layer1'],
            # Missing 'subsets', 'boundaries', 'matrices'
        }
        report_file = tmp_path / "invalid_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f)
        
        loader = MatrixLoader()
        
        with pytest.raises(ValueError) as exc_info:
            loader.load(str(report_file))
        
        assert "missing required keys" in str(exc_info.value).lower()
    
    def test_matrices_not_a_list(self, tmp_path):
        """Test that ValueError is raised when matrices is not a list."""
        report_data = create_valid_clustering_report()
        report_data['matrices'] = "not a list"  # Invalid
        
        report_file = tmp_path / "invalid_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f)
        
        loader = MatrixLoader()
        
        with pytest.raises(ValueError) as exc_info:
            loader.load(str(report_file))
        
        assert "expected 'matrices' to be a list" in str(exc_info.value).lower()
    
    def test_wrong_matrix_count(self, tmp_path):
        """Test that ValueError is raised for wrong number of matrices."""
        # Create report with only 8 matrices instead of 16
        report_data = create_valid_clustering_report(num_matrices=8)
        
        report_file = tmp_path / "invalid_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f)
        
        loader = MatrixLoader()
        
        with pytest.raises(ValueError) as exc_info:
            loader.load(str(report_file))
        
        assert f"Expected {EXPECTED_MATRIX_COUNT} rotation matrices" in str(exc_info.value)
    
    def test_invalid_matrix_conversion(self, tmp_path):
        """Test that ValueError is raised for unconvertible matrix data."""
        report_data = create_valid_clustering_report()
        # Replace one matrix with invalid data
        report_data['matrices'][0] = "not a valid matrix"
        
        report_file = tmp_path / "invalid_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f)
        
        loader = MatrixLoader()
        
        with pytest.raises(ValueError) as exc_info:
            loader.load(str(report_file))
        
        assert "Failed to convert matrix" in str(exc_info.value)
    
    def test_get_matrices_before_load(self):
        """Test that RuntimeError is raised when getting matrices before loading."""
        loader = MatrixLoader()
        
        with pytest.raises(RuntimeError) as exc_info:
            loader.get_matrices()
        
        assert "not loaded" in str(exc_info.value).lower()
    
    def test_get_metadata_before_load(self):
        """Test that RuntimeError is raised when getting metadata before loading."""
        loader = MatrixLoader()
        
        with pytest.raises(RuntimeError) as exc_info:
            loader.get_metadata()
        
        assert "not loaded" in str(exc_info.value).lower()

class TestLoadMatricesFromPath:
    """Tests for the load_matrices_from_path convenience function."""
    
    def test_load_valid_file(self, tmp_path):
        """Test loading a valid file."""
        report_data = create_valid_clustering_report()
        report_file = tmp_path / "clustering_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f)
        
        matrices = load_matrices_from_path(str(report_file))
        
        assert len(matrices) == EXPECTED_MATRIX_COUNT
        assert all(isinstance(m, np.ndarray) for m in matrices)
    
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            load_matrices_from_path("/nonexistent/path.json")

class TestVerifyMatrices:
    """Tests for the verify_matrices function."""
    
    def test_valid_matrices(self):
        """Test verification of valid matrices."""
        matrices = [np.random.randn(64, 64).astype(np.float32) 
                   for _ in range(EXPECTED_MATRIX_COUNT)]
        
        is_valid, errors = verify_matrices(matrices)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_wrong_count(self):
        """Test verification with wrong matrix count."""
        matrices = [np.random.randn(64, 64).astype(np.float32) 
                   for _ in range(8)]  # Only 8 instead of 16
        
        is_valid, errors = verify_matrices(matrices)
        
        assert not is_valid
        assert any("Expected 16 matrices" in error for error in errors)
    
    def test_non_numpy_array(self):
        """Test verification with non-numpy array."""
        matrices = [np.random.randn(64, 64).astype(np.float32) 
                   for _ in range(EXPECTED_MATRIX_COUNT - 1)]
        matrices.append("not a numpy array")  # Invalid
        
        is_valid, errors = verify_matrices(matrices)
        
        assert not is_valid
        assert any("not a numpy array" in error for error in errors)
    
    def test_wrong_dimensions(self):
        """Test verification with wrong dimensions."""
        matrices = [np.random.randn(64, 64).astype(np.float32) 
                   for _ in range(EXPECTED_MATRIX_COUNT - 1)]
        matrices.append(np.random.randn(3, 4, 5).astype(np.float32))  # 3D
        
        is_valid, errors = verify_matrices(matrices)
        
        assert not is_valid
        assert any("3 dimensions" in error for error in errors)
    
    def test_nan_values(self):
        """Test verification with NaN values."""
        matrices = [np.random.randn(64, 64).astype(np.float32) 
                   for _ in range(EXPECTED_MATRIX_COUNT - 1)]
        nan_matrix = np.random.randn(64, 64).astype(np.float32)
        nan_matrix[0, 0] = np.nan
        matrices.append(nan_matrix)
        
        is_valid, errors = verify_matrices(matrices)
        
        assert not is_valid
        assert any("contains NaN" in error for error in errors)
    
    def test_inf_values(self):
        """Test verification with Inf values."""
        matrices = [np.random.randn(64, 64).astype(np.float32) 
                   for _ in range(EXPECTED_MATRIX_COUNT - 1)]
        inf_matrix = np.random.randn(64, 64).astype(np.float32)
        inf_matrix[0, 0] = np.inf
        matrices.append(inf_matrix)
        
        is_valid, errors = verify_matrices(matrices)
        
        assert not is_valid
        assert any("contains Inf" in error for error in errors)
    
    def test_zero_matrix(self):
        """Test verification with a zero matrix."""
        matrices = [np.random.randn(64, 64).astype(np.float32) 
                   for _ in range(EXPECTED_MATRIX_COUNT - 1)]
        matrices.append(np.zeros((64, 64), dtype=np.float32))
        
        is_valid, errors = verify_matrices(matrices)
        
        assert not is_valid
        assert any("zero matrix" in error for error in errors)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])