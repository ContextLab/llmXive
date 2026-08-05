"""
Tests for data validation utilities.
"""
import pytest
import os
import json
from pathlib import Path
import tempfile
import shutil

from code.utils.data_validator import (
    ensure_data_structure,
    validate_raw_data,
    validate_processed_data,
    refresh_manifests,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    MANIFEST_RAW,
    MANIFEST_PROCESSED
)
from code.utils.hasher import hash_file, generate_manifest


class TestDataValidator:
    """Test cases for data validation functions."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up temporary directories for testing."""
        # Store original paths
        self.original_raw = DATA_RAW_DIR
        self.original_processed = DATA_PROCESSED_DIR
        self.original_manifest_raw = MANIFEST_RAW
        self.original_manifest_processed = MANIFEST_PROCESSED
        
        # Create temporary directories
        self.temp_base = tmp_path / "data"
        self.temp_raw = self.temp_base / "raw"
        self.temp_processed = self.temp_base / "processed"
        
        # Create directories
        self.temp_raw.mkdir(parents=True, exist_ok=True)
        self.temp_processed.mkdir(parents=True, exist_ok=True)
        
        # Patch the module-level variables
        import code.utils.data_validator as dv
        dv.DATA_RAW_DIR = self.temp_raw
        dv.DATA_PROCESSED_DIR = self.temp_processed
        dv.MANIFEST_RAW = self.temp_raw / ".manifest.json"
        dv.MANIFEST_PROCESSED = self.temp_processed / ".manifest.json"
        
        yield
        
        # Restore original paths
        dv.DATA_RAW_DIR = self.original_raw
        dv.DATA_PROCESSED_DIR = self.original_processed
        dv.MANIFEST_RAW = self.original_manifest_raw
        dv.MANIFEST_PROCESSED = self.original_manifest_processed

    def test_ensure_data_structure_creates_directories(self):
        """Test that ensure_data_structure creates missing directories."""
        # Remove directories if they exist
        if self.temp_raw.exists():
            shutil.rmtree(self.temp_raw)
        if self.temp_processed.exists():
            shutil.rmtree(self.temp_processed)
        
        # Call the function
        result = ensure_data_structure()
        
        # Verify
        assert result is True
        assert self.temp_raw.exists()
        assert self.temp_processed.exists()
        assert self.temp_raw.is_dir()
        assert self.temp_processed.is_dir()

    def test_ensure_data_structure_creates_manifests(self):
        """Test that ensure_data_structure creates manifest files."""
        # Remove manifests if they exist
        if MANIFEST_RAW.exists():
            MANIFEST_RAW.unlink()
        if MANIFEST_PROCESSED.exists():
            MANIFEST_PROCESSED.unlink()
        
        # Call the function
        result = ensure_data_structure()
        
        # Verify
        assert result is True
        assert MANIFEST_RAW.exists()
        assert MANIFEST_PROCESSED.exists()
        
        # Verify manifest content
        with open(MANIFEST_RAW, 'r') as f:
            manifest_raw = json.load(f)
        assert "files" in manifest_raw
        assert "file_count" in manifest_raw

    def test_validate_raw_data_empty_directory(self):
        """Test validate_raw_data with an empty directory."""
        # Ensure structure exists
        ensure_data_structure()
        
        # Validate
        is_valid, failures = validate_raw_data()
        
        # Verify
        assert is_valid is True
        assert len(failures) == 0

    def test_validate_raw_data_with_file(self):
        """Test validate_raw_data with a file in the directory."""
        # Create a test file
        test_file = self.temp_raw / "test.txt"
        test_file.write_text("test content")
        
        # Generate manifest
        generate_manifest(self.temp_raw, MANIFEST_RAW)
        
        # Validate
        is_valid, failures = validate_raw_data()
        
        # Verify
        assert is_valid is True
        assert len(failures) == 0

    def test_validate_raw_data_modified_file(self):
        """Test validate_raw_data detects modified files."""
        # Create a test file
        test_file = self.temp_raw / "test.txt"
        test_file.write_text("test content")
        
        # Generate manifest
        generate_manifest(self.temp_raw, MANIFEST_RAW)
        
        # Modify the file
        test_file.write_text("modified content")
        
        # Validate
        is_valid, failures = validate_raw_data()
        
        # Verify
        assert is_valid is False
        assert len(failures) == 1
        assert "test.txt" in failures[0]

    def test_validate_processed_data_empty_directory(self):
        """Test validate_processed_data with an empty directory."""
        # Ensure structure exists
        ensure_data_structure()
        
        # Validate
        is_valid, failures = validate_processed_data()
        
        # Verify
        assert is_valid is True
        assert len(failures) == 0

    def test_refresh_manifests(self):
        """Test refresh_manifests updates manifests."""
        # Create test files
        test_file_raw = self.temp_raw / "test1.txt"
        test_file_raw.write_text("content1")
        
        test_file_processed = self.temp_processed / "test2.txt"
        test_file_processed.write_text("content2")
        
        # Generate initial manifests
        generate_manifest(self.temp_raw, MANIFEST_RAW)
        generate_manifest(self.temp_processed, MANIFEST_PROCESSED)
        
        # Modify files
        test_file_raw.write_text("modified1")
        test_file_processed.write_text("modified2")
        
        # Refresh manifests
        result = refresh_manifests()
        
        # Verify
        assert result is True
        
        # Verify manifests were updated
        with open(MANIFEST_RAW, 'r') as f:
            manifest_raw = json.load(f)
        assert manifest_raw["files"]["test1.txt"] == hash_file(test_file_raw)
        
        with open(MANIFEST_PROCESSED, 'r') as f:
            manifest_processed = json.load(f)
        assert manifest_processed["files"]["test2.txt"] == hash_file(test_file_processed)

    def test_validate_raw_data_missing_manifest(self):
        """Test validate_raw_data when manifest is missing."""
        # Remove manifest
        if MANIFEST_RAW.exists():
            MANIFEST_RAW.unlink()
        
        # Validate - should create new manifest
        is_valid, failures = validate_raw_data()
        
        # Verify
        assert is_valid is True
        assert len(failures) == 0
        assert MANIFEST_RAW.exists()