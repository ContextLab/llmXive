"""
Unit tests for config_validator module.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from utils.config_validator import (
    validate_dataset_paths,
    validate_hash_registry,
    compute_file_hash,
    validate_config,
    ConfigValidationError
)


class TestValidateDatasetPaths:
    """Tests for validate_dataset_paths function."""
    
    def test_empty_paths_ci_mode(self):
        """Empty paths should be valid in CI mode."""
        is_valid, errors = validate_dataset_paths({}, "CI")
        assert is_valid is True
        assert len(errors) == 0
    
    def test_empty_paths_research_mode(self):
        """Empty paths should be invalid in RESEARCH mode."""
        is_valid, errors = validate_dataset_paths({}, "RESEARCH")
        assert is_valid is False
        assert len(errors) == 1
        assert "RESEARCH mode requires dataset_paths" in errors[0]
    
    def test_existing_directory(self, tmp_path):
        """Valid existing directory should pass."""
        test_dir = tmp_path / "test_dataset"
        test_dir.mkdir()
        
        is_valid, errors = validate_dataset_paths({"test": str(test_dir)}, "CI")
        assert is_valid is True
        assert len(errors) == 0
    
    def test_non_existing_directory_ci_mode(self, tmp_path):
        """Non-existing directory in CI mode should create path."""
        non_existing = tmp_path / "non_existing"
        
        is_valid, errors = validate_dataset_paths({"test": str(non_existing)}, "CI")
        assert is_valid is True
        assert non_existing.exists()
    
    def test_non_existing_directory_research_mode(self, tmp_path):
        """Non-existing directory in RESEARCH mode should fail."""
        non_existing = tmp_path / "non_existing"
        
        is_valid, errors = validate_dataset_paths({"test": str(non_existing)}, "RESEARCH")
        assert is_valid is False
        assert len(errors) == 1
        assert "does not exist" in errors[0]
    
    def test_file_instead_of_directory(self, tmp_path):
        """File instead of directory should fail."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test")
        
        is_valid, errors = validate_dataset_paths({"test": str(test_file)}, "CI")
        assert is_valid is False
        assert len(errors) == 1
        assert "is not a directory" in errors[0]


class TestValidateHashRegistry:
    """Tests for validate_hash_registry function."""
    
    def test_empty_registry(self):
        """Empty hash registry should be valid."""
        is_valid, errors = validate_hash_registry({}, {})
        assert is_valid is True
        assert len(errors) == 0
    
    def test_file_not_found(self, tmp_path):
        """Missing file in hash registry should not invalidate."""
        registry = {"missing_file": "abc123"}
        is_valid, errors = validate_hash_registry(registry, {})
        # Should not be invalid, just warn
        assert len(errors) == 1
        assert "not found" in errors[0]
    
    def test_hash_mismatch(self, tmp_path):
        """Hash mismatch should be detected."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Compute actual hash
        actual_hash = compute_file_hash(test_file)
        
        # Create registry with wrong hash
        registry = {"test.txt": "wrong_hash"}
        dataset_paths = {"test": str(tmp_path)}
        
        is_valid, errors = validate_hash_registry(registry, dataset_paths)
        assert is_valid is False
        assert len(errors) == 1
        assert "Hash mismatch" in errors[0]
    
    def test_hash_match(self, tmp_path):
        """Matching hash should pass."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Compute actual hash
        actual_hash = compute_file_hash(test_file)
        
        # Create registry with correct hash
        registry = {"test.txt": actual_hash}
        dataset_paths = {"test": str(tmp_path)}
        
        is_valid, errors = validate_hash_registry(registry, dataset_paths)
        assert is_valid is True
        assert len(errors) == 0


class TestComputeFileHash:
    """Tests for compute_file_hash function."""
    
    def test_sha256_hash(self, tmp_path):
        """Test SHA256 hash computation."""
        test_file = tmp_path / "test.txt"
        content = "test content for hashing"
        test_file.write_text(content)
        
        hash_result = compute_file_hash(test_file, "sha256")
        
        # Verify it's a valid hex string
        assert len(hash_result) == 64  # SHA256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in hash_result)
    
    def test_consistency(self, tmp_path):
        """Hash should be consistent for same content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("consistent content")
        
        hash1 = compute_file_hash(test_file)
        hash2 = compute_file_hash(test_file)
        
        assert hash1 == hash2
    
    def test_different_content_different_hash(self, tmp_path):
        """Different content should produce different hashes."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")
        
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        
        assert hash1 != hash2


class TestValidateConfig:
    """Tests for validate_config function."""
    
    @patch('utils.config_validator.get_mode')
    @patch('utils.config_validator.get_config_summary')
    def test_valid_config_ci_mode(self, mock_summary, mock_mode):
        """Test validation with valid CI configuration."""
        mock_mode.return_value = "CI"
        mock_summary.return_value = {
            "dataset_paths": {},
            "hash_registry": {}
        }
        
        is_valid, errors = validate_config()
        assert is_valid is True
        assert len(errors) == 0
    
    @patch('utils.config_validator.get_mode')
    @patch('utils.config_validator.get_config_summary')
    def test_invalid_config_research_mode(self, mock_summary, mock_mode):
        """Test validation with invalid RESEARCH configuration."""
        mock_mode.return_value = "RESEARCH"
        mock_summary.return_value = {
            "dataset_paths": {},
            "hash_registry": {}
        }
        
        is_valid, errors = validate_config()
        assert is_valid is False
        assert len(errors) > 0