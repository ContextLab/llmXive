import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Adjust import based on project structure
# Assuming tests are in tests/unit/ and code is in code/
# We need to ensure 'code' is in the path or use relative imports if running from project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.load_matrices import MatrixLoader, verify_matrices, load_matrices_from_path
from config import Config

@pytest.fixture
def mock_clustering_report(tmp_path):
    """Creates a valid mock clustering report JSON file."""
    report_data = {
        "layers": ["layer_0", "layer_1", "layer_2"],
        "matrices": {
            "layer_0": [[1.0, 0.0], [0.0, 1.0]],
            "layer_1": [[0.7, 0.1], [0.1, 0.7]],
            "layer_2": [[0.5, 0.5], [0.5, 0.5]]
        },
        "boundaries": [0.0, 1.5, 3.0, 5.0],
        "layer_dims": {
            "layer_0": [2, 2],
            "layer_1": [2, 2],
            "layer_2": [2, 2]
        }
    }
    report_path = tmp_path / "clustering_report.json"
    with open(report_path, 'w') as f:
        json.dump(report_data, f)
    return str(report_path)

@pytest.fixture
def mock_clustering_report_invalid(tmp_path):
    """Creates an invalid mock clustering report (missing keys)."""
    report_data = {
        "layers": ["layer_0"],
        # Missing 'matrices' and 'boundaries'
    }
    report_path = tmp_path / "invalid_report.json"
    with open(report_path, 'w') as f:
        json.dump(report_data, f)
    return str(report_path)

def test_matrix_loader_load_success(mock_clustering_report):
    """Test that MatrixLoader successfully loads a valid report."""
    config = Config()
    config.CLUSTERING_REPORT_PATH = mock_clustering_report
    loader = MatrixLoader(config)

    report = loader.load()
    assert "layers" in report
    assert "matrices" in report
    assert "boundaries" in report
    assert len(report["layers"]) == 3

def test_matrix_loader_get_matrices(mock_clustering_report):
    """Test that get_matrices returns numpy arrays."""
    config = Config()
    config.CLUSTERING_REPORT_PATH = mock_clustering_report
    loader = MatrixLoader(config)

    matrices = loader.get_matrices()
    assert isinstance(matrices, dict)
    assert len(matrices) == 3
    assert "layer_0" in matrices
    assert isinstance(matrices["layer_0"], np.ndarray)
    assert matrices["layer_0"].shape == (2, 2)

def test_matrix_loader_get_boundaries(mock_clustering_report):
    """Test that get_boundaries returns the correct list."""
    config = Config()
    config.CLUSTERING_REPORT_PATH = mock_clustering_report
    loader = MatrixLoader(config)

    boundaries = loader.get_boundaries()
    assert boundaries == [0.0, 1.5, 3.0, 5.0]

def test_matrix_loader_file_not_found():
    """Test that MatrixLoader raises FileNotFoundError for missing file."""
    config = Config()
    config.CLUSTERING_REPORT_PATH = "/nonexistent/path/report.json"
    loader = MatrixLoader(config)

    with pytest.raises(FileNotFoundError):
        loader.load()

def test_matrix_loader_invalid_structure(mock_clustering_report_invalid):
    """Test that MatrixLoader raises ValueError for missing keys."""
    config = Config()
    config.CLUSTERING_REPORT_PATH = mock_clustering_report_invalid
    loader = MatrixLoader(config)

    with pytest.raises(ValueError):
        loader.load()

def test_verify_matrices_valid():
    """Test verify_matrices with valid data."""
    valid_matrices = {
        "layer_1": np.array([[1.0, 0.0], [0.0, 1.0]]),
        "layer_2": np.array([[0.5, 0.5], [0.5, 0.5]])
    }
    assert verify_matrices(valid_matrices) is True

def test_verify_matrices_invalid_shape():
    """Test verify_matrices with invalid shape (1D array)."""
    invalid_matrices = {
        "layer_1": np.array([1.0, 0.0, 0.0, 1.0])
    }
    assert verify_matrices(invalid_matrices) is False

def test_verify_matrices_nan_values():
    """Test verify_matrices with NaN values."""
    invalid_matrices = {
        "layer_1": np.array([[1.0, np.nan], [0.0, 1.0]])
    }
    assert verify_matrices(invalid_matrices) is False

def test_verify_matrices_empty_dict():
    """Test verify_matrices with empty dict."""
    assert verify_matrices({}) is False

def test_load_matrices_from_path(mock_clustering_report):
    """Test the convenience function load_matrices_from_path."""
    matrices = load_matrices_from_path(mock_clustering_report)
    assert isinstance(matrices, dict)
    assert "layer_0" in matrices
    assert isinstance(matrices["layer_0"], np.ndarray)