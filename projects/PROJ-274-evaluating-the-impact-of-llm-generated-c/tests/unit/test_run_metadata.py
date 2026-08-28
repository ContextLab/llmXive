"""
Unit tests for the run_metadata module.

Tests the generation and persistence of run metadata.
"""
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.run_metadata import (
    generate_run_metadata,
    save_metadata,
    load_metadata,
    ensure_metadata_dir
)

class TestRunMetadata:
    """Test cases for run metadata generation and storage."""

    def test_generate_run_metadata_structure(self):
        """Test that generated metadata contains required fields."""
        metadata = generate_run_metadata()
        
        assert "RUN_ID" in metadata
        assert "start_time" in metadata
        assert "project_version" in metadata
        
        # Validate RUN_ID is a valid UUID string
        try:
            uuid.UUID(metadata["RUN_ID"])
        except ValueError:
            pytest.fail("RUN_ID is not a valid UUID string")
        
        # Validate start_time is ISO8601 format
        try:
            datetime.fromisoformat(metadata["start_time"])
        except ValueError:
            pytest.fail("start_time is not a valid ISO8601 datetime string")

    def test_save_and_load_metadata(self, tmp_path):
        """Test saving and loading metadata to/from a file."""
        metadata = generate_run_metadata()
        output_file = tmp_path / "test_run_metadata.json"
        
        # Save metadata
        save_metadata(metadata, output_file)
        
        # Verify file exists
        assert output_file.exists()
        
        # Load metadata
        loaded_metadata = load_metadata(output_file)
        
        # Verify content matches
        assert loaded_metadata == metadata
        assert loaded_metadata["RUN_ID"] == metadata["RUN_ID"]

    def test_save_metadata_creates_directory(self):
        """Test that save_metadata creates the state directory if it doesn't exist."""
        metadata = generate_run_metadata()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_state_dir = Path(tmp_dir) / "state"
            test_file = test_state_dir / "run_metadata.json"
            
            # Ensure directory doesn't exist yet
            assert not test_state_dir.exists()
            
            # Save metadata (should create directory)
            save_metadata(metadata, test_file)
            
            # Verify directory and file exist
            assert test_state_dir.exists()
            assert test_file.exists()

    def test_load_metadata_missing_file(self):
        """Test that loading a missing file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_file = Path(tmp_dir) / "nonexistent.json"
            
            with pytest.raises(FileNotFoundError):
                load_metadata(missing_file)

    def test_metadata_json_validity(self, tmp_path):
        """Test that saved metadata is valid JSON."""
        metadata = generate_run_metadata()
        output_file = tmp_path / "test_run_metadata.json"
        
        save_metadata(metadata, output_file)
        
        # Verify it's valid JSON
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert isinstance(loaded, dict)
        assert loaded == metadata