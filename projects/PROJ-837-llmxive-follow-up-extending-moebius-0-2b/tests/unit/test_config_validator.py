import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config_validator import (
    ConfigValidationError, validate_dataset_paths,
    validate_hash_registry, compute_file_hash,
    validate_config, run_validation
)

class TestConfigValidator:
    def test_validate_dataset_paths_exist(self):
        """Test validation when paths exist"""
        valid_paths = {
            'raw': '/tmp',
            'processed': '/tmp'
        }
        
        result = validate_dataset_paths(valid_paths)
        assert result is True

    def test_validate_dataset_paths_missing(self):
        """Test validation when paths don't exist"""
        invalid_paths = {
            'raw': '/nonexistent/path/xyz',
            'processed': '/tmp'
        }
        
        with pytest.raises(ConfigValidationError):
            validate_dataset_paths(invalid_paths)

    def test_compute_file_hash(self):
        """Test file hash computation"""
        # Create a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash1 = compute_file_hash(temp_path)
            hash2 = compute_file_hash(temp_path)
            
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_compute_file_hash_different_content(self):
        """Test that different content produces different hashes"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write("content 1")
            path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write("content 2")
            path2 = f2.name
        
        try:
            hash1 = compute_file_hash(path1)
            hash2 = compute_file_hash(path2)
            
            assert hash1 != hash2
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_validate_hash_registry_valid(self):
        """Test hash registry validation with valid data"""
        import tempfile
        import hashlib
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_path = f.name
        
        try:
            correct_hash = compute_file_hash(temp_path)
            registry = {temp_path: correct_hash}
            
            result = validate_hash_registry(registry)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_validate_hash_registry_invalid(self):
        """Test hash registry validation with invalid data"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_path = f.name
        
        try:
            wrong_hash = "0" * 64
            registry = {temp_path: wrong_hash}
            
            with pytest.raises(ConfigValidationError):
                validate_hash_registry(registry)
        finally:
            os.unlink(temp_path)

    def test_config_validation_error_message(self):
        """Test that ConfigValidationError has proper message"""
        try:
            raise ConfigValidationError("Test error message")
        except ConfigValidationError as e:
            assert "Test error message" in str(e)
