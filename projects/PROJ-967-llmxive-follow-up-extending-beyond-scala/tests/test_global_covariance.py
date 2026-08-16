"""
Tests for Global Covariance Matrix and Dominant Eigenvalue Calculation (T022b).
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from code.global_covariance import (
    calculate_global_covariance_and_eigenvalue,
    save_covariance_matrix,
    save_dominant_eigenvalue,
)

@pytest.fixture
def mock_teacher_data():
    """Create a mock DataFrame with teacher scores."""
    np.random.seed(42)
    n_samples = 100
    data = {
        "Alignment": np.random.normal(5, 1, n_samples),
        "Realism": np.random.normal(5, 1, n_samples),
        "Aesthetics": np.random.normal(5, 1, n_samples),
        "Plausibility": np.random.normal(5, 1, n_samples),
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_calculate_global_covariance_and_eigenvalue(mock_teacher_data):
    """Test that covariance and eigenvalue are calculated correctly."""
    import logging
    
    logger = logging.getLogger(__name__)
    cov_matrix, dominant_eig = calculate_global_covariance_and_eigenvalue(mock_teacher_data, logger)
    
    # Check dimensions
    assert cov_matrix.shape == (4, 4), "Covariance matrix should be 4x4"
    assert isinstance(dominant_eig, float), "Dominant eigenvalue should be a float"
    
    # Check symmetry
    assert np.allclose(cov_matrix, cov_matrix.T), "Covariance matrix must be symmetric"
    
    # Check positive semi-definiteness (eigenvalues >= 0)
    eigenvalues = np.linalg.eigvalsh(cov_matrix)
    assert np.all(eigenvalues >= -1e-10), "Covariance matrix should be positive semi-definite"
    
    # Check that dominant eigenvalue is indeed the largest
    assert dominant_eig == pytest.approx(np.max(eigenvalues), rel=1e-5), "Dominant eigenvalue mismatch"

def test_insufficient_samples():
    """Test that an error is raised when N < 4."""
    df = pd.DataFrame({
        "Alignment": [1.0, 2.0],
        "Realism": [1.0, 2.0],
        "Aesthetics": [1.0, 2.0],
        "Plausibility": [1.0, 2.0],
    })
    import logging
    logger = logging.getLogger(__name__)
    
    with pytest.raises(RuntimeError, match="Insufficient data points"):
        calculate_global_covariance_and_eigenvalue(df, logger)

def test_missing_columns(mock_teacher_data):
    """Test that an error is raised when required columns are missing."""
    df = mock_teacher_data.drop(columns=["Alignment"])
    import logging
    logger = logging.getLogger(__name__)
    
    with pytest.raises(RuntimeError, match="Missing required teacher score columns"):
        calculate_global_covariance_and_eigenvalue(df, logger)

def test_save_covariance_matrix(mock_teacher_data, temp_output_dir):
    """Test saving covariance matrix to JSON."""
    import logging
    logger = logging.getLogger(__name__)
    cov_matrix, _ = calculate_global_covariance_and_eigenvalue(mock_teacher_data, logger)
    
    output_path = temp_output_dir / "covariance_matrix.json"
    save_covariance_matrix(cov_matrix, output_path, logger)
    
    assert output_path.exists(), "Output file should exist"
    
    with open(output_path) as f:
        loaded_data = json.load(f)
    
    assert isinstance(loaded_data, list), "JSON should be a list of lists"
    assert len(loaded_data) == 4, "Should have 4 rows"
    assert all(len(row) == 4 for row in loaded_data), "Each row should have 4 columns"

def test_save_dominant_eigenvalue(mock_teacher_data, temp_output_dir):
    """Test saving dominant eigenvalue to JSON."""
    import logging
    logger = logging.getLogger(__name__)
    _, dominant_eig = calculate_global_covariance_and_eigenvalue(mock_teacher_data, logger)
    
    output_path = temp_output_dir / "dominant_eigenvalue.json"
    save_dominant_eigenvalue(dominant_eig, output_path, logger)
    
    assert output_path.exists(), "Output file should exist"
    
    with open(output_path) as f:
        loaded_data = json.load(f)
    
    assert "dominant_eigenvalue" in loaded_data, "JSON should contain dominant_eigenvalue key"
    assert isinstance(loaded_data["dominant_eigenvalue"], float), "Value should be a float"
    assert loaded_data["dominant_eigenvalue"] == pytest.approx(dominant_eig, rel=1e-5)