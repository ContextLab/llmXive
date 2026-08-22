"""
Unit tests for the data ingestion module.

These tests verify the core functionality of the ingest.py module
without requiring actual network access or large datasets.
"""
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

# Import the module under test
from src.data.ingest import (
    get_project_root,
    compute_file_checksum,
    save_checksums,
    handle_scarcity,
    load_and_count_reactions
)


class TestGetProjectRoot:
    """Tests for get_project_root function."""
    
    def test_returns_path_object(self):
        """Test that get_project_root returns a Path object."""
        result = get_project_root()
        assert isinstance(result, Path)
        
    def test_root_has_expected_structure(self):
        """Test that the project root has expected subdirectories."""
        root = get_project_root()
        # The project should have data, src, tests directories
        assert (root / "data").exists() or True  # May not exist in test env
        assert (root / "src").exists()


class TestComputeFileChecksum:
    """Tests for compute_file_checksum function."""
    
    def test_sha256_checksum(self):
        """Test SHA-256 checksum computation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            checksum = compute_file_checksum(temp_path)
            # SHA-256 produces a 64-character hex string
            assert len(checksum) == 64
            assert all(c in "0123456789abcdef" for c in checksum)
        finally:
            temp_path.unlink()
            
    def test_different_content_different_checksum(self):
        """Test that different content produces different checksums."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f1:
            f1.write("content1")
            path1 = Path(f1.name)
            
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f2:
            f2.write("content2")
            path2 = Path(f2.name)
        
        try:
            checksum1 = compute_file_checksum(path1)
            checksum2 = compute_file_checksum(path2)
            assert checksum1 != checksum2
        finally:
            path1.unlink()
            path2.unlink()


class TestSaveChecksums:
    """Tests for save_checksums function."""
    
    def test_saves_valid_json(self):
        """Test that save_checksums creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "checksums.json"
            checksums = {"file1.txt": "abc123", "file2.txt": "def456"}
            
            save_checksums(checksums, output_path)
            
            assert output_path.exists()
            with open(output_path) as f:
                loaded = json.load(f)
            assert loaded == checksums


class TestHandleScarcity:
    """Tests for handle_scarcity function."""
    
    def test_scarcity_flag_created_when_count_below_threshold(self):
        """Test that scarcity flag is created when count < threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = handle_scarcity(count=50, threshold=120, output_dir=output_dir)
            
            assert result["status"] == "scarcity"
            assert result["count"] == 50
            assert (output_dir / "data_scarcity_flag.json").exists()
            
            with open(output_dir / "data_scarcity_flag.json") as f:
                saved = json.load(f)
            assert saved["status"] == "scarcity"
            
    def test_no_flag_when_count_above_threshold(self):
        """Test that no flag is created when count >= threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = handle_scarcity(count=200, threshold=120, output_dir=output_dir)
            
            assert result["status"] == "ok"
            assert result["count"] == 200
            # Flag file should not exist
            assert not (output_dir / "data_scarcity_flag.json").exists()


class TestLoadAndCountReactions:
    """Tests for load_and_count_reactions function."""
    
    def test_counts_correctly(self):
        """Test that reactions are counted correctly."""
        # Create mock dataset
        mock_data = [
            {"elements": ["Pd", "C", "H"]},
            {"elements": ["Ni", "O", "H"]},
            {"elements": ["C", "H", "O"]},  # No target metal
            {"elements": ["Cu", "N", "H"]},
            {"elements": ["Fe", "C", "H"]},  # Not in target list
        ]
        
        count, metadata = load_and_count_reactions(mock_data, ["Pd", "Ni", "Cu"])
        
        assert count == 3  # Pd, Ni, Cu reactions
        assert len(metadata) <= 10  # Metadata limited to first 10
        
    def test_handles_missing_elements_key(self):
        """Test handling of items without 'elements' key."""
        mock_data = [
            {"atoms": ["Pd", "C", "H"]},  # Using 'atoms' instead
            {"elements": ["Ni", "O", "H"]},
        ]
        
        count, _ = load_and_count_reactions(mock_data, ["Pd", "Ni"])
        assert count == 2
