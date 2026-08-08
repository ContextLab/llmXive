"""
tests/unit/test_save_outputs.py
Unit tests for T017: Save processed matrices with provenance metadata.
"""
import os
import json
import numpy as np
import pytest
from pathlib import Path
import tempfile
import shutil

# Mock imports for testing
from unittest.mock import patch, MagicMock

# Import the module under test
from save_outputs import compute_sha256_file, save_with_provenance, load_provenance_info

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def sample_matrix(temp_dir):
    """Create a sample numpy matrix file."""
    matrix = np.random.rand(100, 100).astype(np.float32)
    matrix_path = os.path.join(temp_dir, "sample.npy")
    np.save(matrix_path, matrix)
    return matrix_path, matrix

def test_compute_sha256_file(sample_matrix):
    """Test SHA256 computation on a file."""
    matrix_path, _ = sample_matrix
    hash1 = compute_sha256_file(matrix_path)
    hash2 = compute_sha256_file(matrix_path)
    
    # Hash should be consistent
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex string length
    assert all(c in "0123456789abcdef" for c in hash1)

def test_save_with_provenance_creates_files(sample_matrix, temp_dir):
    """Test that save_with_provenance creates both .npy and _provenance.json files."""
    matrix_path, matrix = sample_matrix
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir)
    
    result = save_with_provenance(
        matrix_path=matrix_path,
        output_path=output_dir,
        matrix_name="test_structural.npy",
        description="Test description",
        extra_metadata={"test_key": "test_value"}
    )
    
    # Check .npy file exists
    npy_path = os.path.join(output_dir, "test_structural.npy")
    assert os.path.exists(npy_path)
    
    # Check provenance JSON exists
    json_path = os.path.join(output_dir, "test_structural_provenance.json")
    assert os.path.exists(json_path)
    
    # Check provenance content
    with open(json_path, "r") as f:
        provenance = json.load(f)
    
    assert provenance["file_name"] == "test_structural.npy"
    assert provenance["description"] == "Test description"
    assert provenance["test_key"] == "test_value"
    assert "file_hash_sha256" in provenance
    assert provenance["shape"] == list(matrix.shape)
    assert provenance["dtype"] == str(matrix.dtype)

def test_save_with_provenance_loads_correct_matrix(sample_matrix, temp_dir):
    """Test that the saved matrix can be loaded and matches the original."""
    matrix_path, original_matrix = sample_matrix
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir)
    
    save_with_provenance(
        matrix_path=matrix_path,
        output_path=output_dir,
        matrix_name="test_structural.npy",
        description="Test description"
    )
    
    # Load the saved matrix
    saved_path = os.path.join(output_dir, "test_structural.npy")
    loaded_matrix = np.load(saved_path)
    
    # Check equality
    np.testing.assert_array_equal(original_matrix, loaded_matrix)

def test_load_provenance_info_missing_file():
    """Test load_provenance_info when file doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        result = load_provenance_info()
        assert result == {}

def test_load_provenance_info_invalid_json(temp_dir):
    """Test load_provenance_info with invalid JSON."""
    # Create a fake state directory with invalid JSON
    state_dir = Path(temp_dir) / "state"
    state_dir.mkdir(exist_ok=True)
    provenance_file = state_dir / "provenance.json"
    provenance_file.write_text("{ invalid json }")
    
    with patch('pathlib.Path.exists', return_value=True):
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = load_provenance_info()
            assert result == {}