"""
Tests for T006: Data structure setup.

These tests verify that:
1. Required directories are created
2. checksums.txt is initialized with correct format
3. graph_metadata.json schema is created with required keys
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_data_structure import (
    ensure_directory,
    initialize_checksums_file,
    initialize_metadata_schema,
    METADATA_SCHEMA,
    CHECKSUMS_FILE
)

class TestDataStructureSetup:
    """Test suite for data structure setup functions."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up a temporary directory for testing."""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock PROJECT_ROOT to point to temp directory
        self.original_project_root = None
        
        # We need to patch the module's PROJECT_ROOT
        import setup_data_structure
        self.original_project_root = setup_data_structure.PROJECT_ROOT
        setup_data_structure.PROJECT_ROOT = Path(self.temp_dir)
        
        yield
        
        # Teardown: restore original and remove temp dir
        setup_data_structure.PROJECT_ROOT = self.original_project_root
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ensure_directory_creates_new_dir(self):
        """Test that ensure_directory creates a new directory."""
        test_path = Path(self.temp_dir) / "test_new_dir"
        assert not test_path.exists()
        
        ensure_directory(test_path)
        
        assert test_path.exists()
        assert test_path.is_dir()

    def test_ensure_directory_ignores_existing_dir(self):
        """Test that ensure_directory doesn't fail on existing directory."""
        test_path = Path(self.temp_dir) / "test_existing_dir"
        test_path.mkdir(parents=True, exist_ok=True)
        
        # Should not raise an exception
        ensure_directory(test_path)
        
        assert test_path.exists()
        assert test_path.is_dir()

    def test_initialize_checksums_file(self):
        """Test that checksums.txt is created with correct format."""
        initialize_checksums_file()
        
        checksums_file = Path(self.temp_dir) / "data" / "checksums.txt"
        assert checksums_file.exists()
        
        with open(checksums_file, 'r') as f:
            content = f.read()
        
        # Check required header lines
        assert "# Checksums for generated artifacts" in content
        assert "# Format: <algorithm> <relative_path>" in content
        assert "T006" in content
        assert "T018" in content

    def test_initialize_metadata_schema(self):
        """Test that graph_metadata.json is created with required keys."""
        initialize_metadata_schema()
        
        metadata_file = Path(self.temp_dir) / "data" / "processed" / "graph_metadata.json"
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Check required keys from schema
        required_keys = ["node_count", "avg_degree", "p", "seed", "checksum"]
        for key in required_keys:
            assert key in metadata, f"Missing required key: {key}"
        
        # Check types
        assert isinstance(metadata["node_count"], int)
        assert isinstance(metadata["avg_degree"], float)
        assert isinstance(metadata["p"], float)
        assert isinstance(metadata["seed"], int)
        assert isinstance(metadata["checksum"], str)

    def test_full_setup_flow(self):
        """Test the complete setup flow creates all required artifacts."""
        # Run all initialization functions
        ensure_directory(Path(self.temp_dir) / "data" / "processed")
        ensure_directory(Path(self.temp_dir) / "data" / "raw")
        ensure_directory(Path(self.temp_dir) / "data" / "checksums")
        initialize_checksums_file()
        initialize_metadata_schema()
        
        # Verify all directories exist
        assert (Path(self.temp_dir) / "data" / "processed").exists()
        assert (Path(self.temp_dir) / "data" / "raw").exists()
        assert (Path(self.temp_dir) / "data" / "checksums").exists()
        
        # Verify files exist
        assert (Path(self.temp_dir) / "data" / "checksums.txt").exists()
        assert (Path(self.temp_dir) / "data" / "processed" / "graph_metadata.json").exists()

    def test_metadata_schema_matches_spec(self):
        """Verify the metadata schema matches the task specification."""
        # From task description:
        # Schema: graph_metadata.json must contain keys:
        # node_count (int), avg_degree (float), p (float), seed (int), checksum (string)
        
        expected_types = {
            "node_count": int,
            "avg_degree": float,
            "p": float,
            "seed": int,
            "checksum": str
        }
        
        for key, expected_type in expected_types.items():
            assert key in METADATA_SCHEMA, f"Missing key: {key}"
            assert isinstance(METADATA_SCHEMA[key], expected_type), \
                f"Key {key} has wrong type: expected {expected_type}, got {type(METADATA_SCHEMA[key])}"

    def test_checksums_file_format(self):
        """Verify checksums.txt follows the required format."""
        initialize_checksums_file()
        
        checksums_file = Path(self.temp_dir) / "data" / "checksums.txt"
        
        with open(checksums_file, 'r') as f:
            lines = f.readlines()
        
        # First line should be a comment about the format
        assert lines[0].strip().startswith("#")
        
        # Should contain format specification
        format_line = next((line for line in lines if "Format:" in line), None)
        assert format_line is not None, "Missing format specification in checksums.txt"
        assert "algorithm" in format_line.lower()
        assert "relative_path" in format_line.lower()

    def test_directories_use_correct_structure(self):
        """Verify the directory structure matches the task requirements."""
        # Task requires: data/processed/, data/raw/, data/checksums/
        
        ensure_directory(Path(self.temp_dir) / "data" / "processed")
        ensure_directory(Path(self.temp_dir) / "data" / "raw")
        ensure_directory(Path(self.temp_dir) / "data" / "checksums")
        
        expected_dirs = [
            "data/processed",
            "data/raw",
            "data/checksums"
        ]
        
        for dir_str in expected_dirs:
            dir_path = Path(self.temp_dir) / dir_str
            assert dir_path.exists(), f"Missing required directory: {dir_str}"
            assert dir_path.is_dir(), f"Not a directory: {dir_str}"