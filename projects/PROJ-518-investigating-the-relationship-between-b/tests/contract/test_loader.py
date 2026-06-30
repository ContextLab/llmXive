"""
Contract tests for the data loader module.

These tests verify that the loader raises appropriate exceptions
when required data fields are missing.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path

# Import the function to test
from code.data.loader import validate_caq_availability
from code.errors import DataMissingCreativityError


def test_loader_raises_on_missing_caq():
    """
    Test that DataMissingCreativityError is raised when CAQ is missing.
    
    This is a contract test ensuring the validation logic correctly
    identifies missing critical fields.
    """
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.json")
        behavioral_path = os.path.join(tmpdir, "behavioral.json")
        
        # Create a manifest file
        manifest_data = {
            "version": "1.0",
            "files": {
                "behavioral": "behavioral.json"
            }
        }
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Create a behavioral file WITHOUT CAQ field
        behavioral_data = {
            "subject_id": "sub_001",
            "age": 25,
            "sex": "M",
            "education": 16
            # CAQ is intentionally missing
        }
        with open(behavioral_path, 'w') as f:
            json.dump(behavioral_data, f)
        
        # Verify that the function raises DataMissingCreativityError
        with pytest.raises(DataMissingCreativityError) as exc_info:
            validate_caq_availability(manifest_path, behavioral_path)
        
        # Verify the error message contains information about the missing field
        assert "CAQ" in str(exc_info.value)
        assert "missing" in str(exc_info.value).lower()


def test_loader_valid_with_caq():
    """
    Test that validate_caq_availability returns True when CAQ is present.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.json")
        behavioral_path = os.path.join(tmpdir, "behavioral.json")
        
        # Create manifest
        manifest_data = {
            "version": "1.0",
            "files": {
                "behavioral": "behavioral.json"
            }
        }
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Create behavioral file WITH CAQ field
        behavioral_data = {
            "subject_id": "sub_001",
            "age": 25,
            "sex": "M",
            "education": 16,
            "CAQ": 12
        }
        with open(behavioral_path, 'w') as f:
            json.dump(behavioral_data, f)
        
        # Should return True without raising
        result = validate_caq_availability(manifest_path, behavioral_path)
        assert result is True


def test_loader_raises_on_nonexistent_file():
    """
    Test that FileNotFoundError is raised when the behavioral file doesn't exist.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.json")
        behavioral_path = os.path.join(tmpdir, "nonexistent.json")
        
        # Create manifest
        manifest_data = {
            "version": "1.0",
            "files": {
                "nonexistent.json": "nonexistent.json"
            }
        }
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            validate_caq_availability(manifest_path, behavioral_path)
