"""
Unit tests for T017 validation logic.
"""
import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
import shutil

# We need to mock the config to point to temp dirs
# Since config.py uses global state or reads from env, we might need to mock it.
# However, for simplicity in this test, we will test the core functions directly
# by passing paths, assuming we can bypass the global get_path for the test.

# Import the validation logic
# We need to import the module, but it relies on config.
# Let's assume we can import the functions if we set up the environment correctly,
# or we test the pure logic by copying the function here if necessary.
# Better approach: Mock the config or pass paths directly.

# For this test, we will assume the validation logic is refactored to be testable
# or we mock the config.

# Let's try to import the module and see if it works with mocked config
# But since we can't easily mock the global config in the imported module without side effects,
# we will test the core validation function by passing a file path directly.

# We will create a temporary directory structure for testing.

def test_validate_matrix_correct_shape():
    """Test that a matrix with correct shape is valid."""
    # Create a temp matrix
    with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
        temp_path = Path(f.name)
        np.savez(f, matrix=np.eye(90))
    
    try:
        # We need to call the validation function.
        # Since validate_matrix is inside validate_matrices.py and relies on config for paths
        # but takes a file_path, we can test it if we import it.
        # However, the import of validate_matrices.py might fail if config is not set up.
        # Let's assume the function is pure enough to test.
        
        # Actually, the function validate_matrix in validate_matrices.py is pure regarding the file.
        # It only uses config for paths in main().
        # So we can import and call validate_matrix if we can import the module.
        
        # To avoid import issues, let's just test the logic manually here or assume the module loads.
        # For the sake of the test, let's assume we can import.
        from code.validate_matrices import validate_matrix, EXPECTED_NODES
        
        result = validate_matrix(temp_path, "sub-001", "aal90")
        assert result["valid"] is True
        assert result["shape"] == [90, 90]
        assert len(result["errors"]) == 0
    finally:
        temp_path.unlink()

def test_validate_matrix_wrong_shape():
    """Test that a matrix with wrong shape is invalid."""
    with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
        temp_path = Path(f.name)
        np.savez(f, matrix=np.eye(100)) # Should be 90 for aal90
    
    try:
        from code.validate_matrices import validate_matrix
        result = validate_matrix(temp_path, "sub-001", "aal90")
        assert result["valid"] is False
        assert any("Shape mismatch" in err for err in result["errors"])
    finally:
        temp_path.unlink()

def test_validate_matrix_zero_edges():
    """Test that a matrix with zero edges is invalid."""
    with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
        temp_path = Path(f.name)
        np.savez(f, matrix=np.zeros((90, 90)))
    
    try:
        from code.validate_matrices import validate_matrix
        result = validate_matrix(temp_path, "sub-001", "aal90")
        assert result["valid"] is False
        assert any("zero edges" in err for err in result["errors"])
    finally:
        temp_path.unlink()

def test_validate_matrix_nan_values():
    """Test that a matrix with NaN values is invalid."""
    with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
        temp_path = Path(f.name)
        mat = np.ones((90, 90))
        mat[0, 0] = np.nan
        np.savez(f, matrix=mat)
    
    try:
        from code.validate_matrices import validate_matrix
        result = validate_matrix(temp_path, "sub-001", "aal90")
        assert result["valid"] is False
        assert any("NaN" in err for err in result["errors"])
    finally:
        temp_path.unlink()

def test_validate_matrix_missing_file():
    """Test that a missing file is invalid."""
    from code.validate_matrices import validate_matrix
    result = validate_matrix(Path("/nonexistent/file.npz"), "sub-001", "aal90")
    assert result["valid"] is False
    assert any("does not exist" in err for err in result["errors"])