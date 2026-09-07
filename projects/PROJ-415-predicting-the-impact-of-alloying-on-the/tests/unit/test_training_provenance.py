"""
tests/unit/test_training_provenance.py
Unit tests for T072: Data Provenance Verification in training.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open

# We need to mock the config imports to avoid path issues in unit tests
# But since we are testing the function directly, we can patch the file reading

# Import the function to test
# Note: In a real scenario, we might need to adjust imports if the module structure is complex
# For now, assuming we can import directly or via a relative path if in the same package
# Since this is a unit test file, we will mock the dependencies of training.py

@pytest.fixture
def mock_provenance_file(tmp_path):
    """Creates a temporary data_provenance.json file."""
    file_path = tmp_path / "data_provenance.json"
    return file_path

def test_verify_data_provenance_real_source(mock_provenance_file):
    """Test that verification passes for 'real' source_type."""
    # Arrange
    data = {
        "source_type": "real",
        "source_url": "https://nist.gov/diffusion",
        "row_count": 100
    }
    with open(mock_provenance_file, 'w') as f:
        json.dump(data, f)

    # Mock the DATA_DIR path in training.py to point to our temp directory
    # We need to patch the function to use our temp file
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    
    # We need to reload the module to pick up the new path or patch the path directly
    # Since we can't easily reload, we will patch the function's internal logic
    # But for this test, let's assume we can pass the path as an argument or patch the global
    
    # Alternative: Patch the open call and the path check
    with patch('models.training.DATA_DIR', mock_provenance_file.parent):
        from models.training import verify_data_provenance
        
        # Act & Assert
        # The function should not raise an exception
        result = verify_data_provenance()
        assert result is True

def test_verify_data_provenance_mock_source(mock_provenance_file):
    """Test that verification fails for 'mock' source_type."""
    # Arrange
    data = {
        "source_type": "mock",
        "source_url": "local/mock_data.csv",
        "row_count": 100
    }
    with open(mock_provenance_file, 'w') as f:
        json.dump(data, f)

    with patch('models.training.DATA_DIR', mock_provenance_file.parent):
        from models.training import verify_data_provenance
        
        # Act & Assert
        with pytest.raises(SystemExit) as excinfo:
            verify_data_provenance()
        
        assert "Cannot train on synthetic data" in str(excinfo.value)

def test_verify_data_provenance_missing_file(tmp_path):
    """Test that verification fails if provenance file is missing."""
    # Arrange: Create a temp dir but do NOT create the file
    with patch('models.training.DATA_DIR', tmp_path):
        from models.training import verify_data_provenance
        
        # Act & Assert
        with pytest.raises(SystemExit) as excinfo:
            verify_data_provenance()
        
        assert "missing provenance file" in str(excinfo.value).lower()

def test_verify_data_provenance_invalid_json(tmp_path):
    """Test that verification fails if provenance file is invalid JSON."""
    # Arrange
    file_path = tmp_path / "data_provenance.json"
    with open(file_path, 'w') as f:
        f.write("{ invalid json }")

    with patch('models.training.DATA_DIR', tmp_path):
        from models.training import verify_data_provenance
        
        # Act & Assert
        with pytest.raises(SystemExit) as excinfo:
            verify_data_provenance()
        
        assert "invalid provenance file" in str(excinfo.value).lower()