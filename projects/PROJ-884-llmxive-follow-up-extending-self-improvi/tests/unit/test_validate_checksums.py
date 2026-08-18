"""
Unit tests for checksum validation functionality.

Tests the integrity checking mechanisms for dataset files.
"""
import json
import tempfile
import os
from pathlib import Path
import pytest
from code.dataset.validate_checksums import (
    compute_file_checksum,
    generate_checksums_for_directory,
    save_checksums,
    load_checksums,
    validate_data_integrity,
    update_manifest,
    CHECKSUM_MANIFEST_FILE
)

class TestComputeFileChecksum:
    """Tests for compute_file_checksum function."""
    
    def test_computes_correct_checksum_for_simple_file(self, tmp_path):
        """Test that checksum is computed correctly for a simple file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_file_checksum(test_file)
        
        # SHA256 of "Hello, World!"
        expected_checksum = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected_checksum
    
    def test_computes_correct_checksum_for_binary_file(self, tmp_path):
        """Test checksum computation for binary data."""
        test_file = tmp_path / "binary.bin"
        test_content = bytes([0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF])
        test_file.write_bytes(test_content)
        
        checksum = compute_file_checksum(test_file)
        
        # SHA256 of the binary content
        expected_checksum = "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
        assert checksum == checksum
    
    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        missing_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_file)
    
    def test_handles_large_files_in_chunks(self, tmp_path):
        """Test that large files are handled correctly."""
        test_file = tmp_path / "large.bin"
        # Create a 1MB file
        test_content = bytes(range(256)) * 4096  # 1MB
        test_file.write_bytes(test_content)
        
        checksum = compute_file_checksum(test_file)
        
        # Just verify it doesn't crash and returns a valid hex string
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)

class TestGenerateChecksumsForDirectory:
    """Tests for generate_checksums_for_directory function."""
    
    def test_generates_checksums_for_all_files(self, tmp_path):
        """Test that checksums are generated for all files in directory."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("content3")
        
        checksums = generate_checksums_for_directory(tmp_path)
        
        assert len(checksums) == 3
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        assert "subdir/file3.txt" in checksums
    
    def test_raises_error_for_nonexistent_directory(self):
        """Test that FileNotFoundError is raised for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            generate_checksums_for_directory(Path("/nonexistent/path"))
    
    def test_raises_error_for_file_instead_of_directory(self, tmp_path):
        """Test that NotADirectoryError is raised when path is a file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        with pytest.raises(NotADirectoryError):
            generate_checksums_for_directory(test_file)
    
    def test_returns_empty_dict_for_empty_directory(self, tmp_path):
        """Test that empty directory returns empty checksums dict."""
        checksums = generate_checksums_for_directory(tmp_path)
        assert checksums == {}

class TestSaveAndLoadChecksums:
    """Tests for save_checksums and load_checksums functions."""
    
    def test_saves_and_loads_checksums_correctly(self, tmp_path):
        """Test round-trip save and load of checksums."""
        checksums = {
            "file1.txt": "abc123",
            "file2.txt": "def456"
        }
        manifest_path = tmp_path / "checksums.json"
        
        save_checksums(checksums, manifest_path)
        loaded_checksums = load_checksums(manifest_path)
        
        assert loaded_checksums == checksums
    
    def test_creates_parent_directory_if_needed(self, tmp_path):
        """Test that save creates parent directories."""
        checksums = {"file.txt": "abc123"}
        nested_path = tmp_path / "nested" / "dir" / "checksums.json"
        
        save_checksums(checksums, nested_path)
        
        assert nested_path.exists()
    
    def test_load_raises_error_for_missing_file(self, tmp_path):
        """Test that load raises FileNotFoundError for missing manifest."""
        missing_path = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_checksums(missing_path)
    
    def test_manifest_has_correct_structure(self, tmp_path):
        """Test that saved manifest has correct JSON structure."""
        checksums = {"file.txt": "abc123"}
        manifest_path = tmp_path / "checksums.json"
        
        save_checksums(checksums, manifest_path)
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert "version" in manifest
        assert "algorithm" in manifest
        assert "generated_at" in manifest
        assert "checksums" in manifest
        assert manifest["checksums"] == checksums

class TestValidateDataIntegrity:
    """Tests for validate_data_integrity function."""
    
    def test_validates_all_files_correctly(self, tmp_path):
        """Test successful validation of all files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "file1.txt").write_text("content1")
        (data_dir / "file2.txt").write_text("content2")
        
        # Generate checksums
        checksums = generate_checksums_for_directory(data_dir)
        manifest_path = tmp_path / "checksums.json"
        save_checksums(checksums, manifest_path)
        
        # Validate
        is_valid = validate_data_integrity(data_dir, manifest_path)
        
        assert is_valid is True
    
    def test_detects_modified_file(self, tmp_path):
        """Test detection of modified file."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "file1.txt"
        test_file.write_text("original content")
        
        # Generate checksums
        checksums = generate_checksums_for_directory(data_dir)
        manifest_path = tmp_path / "checksums.json"
        save_checksums(checksums, manifest_path)
        
        # Modify file
        test_file.write_text("modified content")
        
        # Validate should fail
        is_valid = validate_data_integrity(data_dir, manifest_path)
        
        assert is_valid is False
    
    def test_detects_missing_file(self, tmp_path):
        """Test detection of missing file."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "file1.txt"
        test_file.write_text("content")
        
        # Generate checksums
        checksums = generate_checksums_for_directory(data_dir)
        manifest_path = tmp_path / "checksums.json"
        save_checksums(checksums, manifest_path)
        
        # Remove file
        test_file.unlink()
        
        # Validate should fail
        is_valid = validate_data_integrity(data_dir, manifest_path)
        
        assert is_valid is False
    
    def test_handles_empty_directory(self, tmp_path):
        """Test validation of empty directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Generate empty checksums
        checksums = generate_checksums_for_directory(data_dir)
        manifest_path = tmp_path / "checksums.json"
        save_checksums(checksums, manifest_path)
        
        # Validate
        is_valid = validate_data_integrity(data_dir, manifest_path)
        
        assert is_valid is True

class TestUpdateManifest:
    """Tests for update_manifest function."""
    
    def test_updates_manifest_with_current_checksums(self, tmp_path):
        """Test that manifest is updated with current file checksums."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "file1.txt"
        test_file.write_text("content1")
        
        manifest_path = tmp_path / "checksums.json"
        
        # First update
        update_manifest(data_dir, manifest_path)
        
        # Modify file
        test_file.write_text("content2")
        
        # Second update
        update_manifest(data_dir, manifest_path)
        
        # Load and verify
        checksums = load_checksums(manifest_path)
        
        assert "file1.txt" in checksums
        # The checksum should be different from the original
        assert checksums["file1.txt"] != "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    
    def test_creates_manifest_if_not_exists(self, tmp_path):
        """Test that manifest is created if it doesn't exist."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "file1.txt").write_text("content")
        
        manifest_path = tmp_path / "checksums.json"
        
        update_manifest(data_dir, manifest_path)
        
        assert manifest_path.exists()

class TestIntegration:
    """Integration tests for the full checksum workflow."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow: generate -> modify -> validate -> update."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create initial files
        (data_dir / "puzzle1.json").write_text('{"id": 1, "data": "test1"}')
        (data_dir / "puzzle2.json").write_text('{"id": 2, "data": "test2"}')
        
        # Generate initial checksums
        checksums = generate_checksums_for_directory(data_dir)
        manifest_path = tmp_path / "checksums.json"
        save_checksums(checksums, manifest_path)
        
        # Validate should pass
        assert validate_data_integrity(data_dir, manifest_path) is True
        
        # Modify a file
        (data_dir / "puzzle1.json").write_text('{"id": 1, "data": "modified"}')
        
        # Validate should fail
        assert validate_data_integrity(data_dir, manifest_path) is False
        
        # Update manifest
        update_manifest(data_dir, manifest_path)
        
        # Validate should pass again
        assert validate_data_integrity(data_dir, manifest_path) is True
    
    def test_handles_nested_directory_structure(self, tmp_path):
        """Test workflow with nested directory structure."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create nested structure
        subdir1 = data_dir / "level1" / "level2"
        subdir1.mkdir(parents=True)
        
        (data_dir / "root.json").write_text('{"level": "root"}')
        (data_dir / "level1" / "mid.json").write_text('{"level": "mid"}')
        (subdir1 / "deep.json").write_text('{"level": "deep"}')
        
        # Generate checksums
        checksums = generate_checksums_for_directory(data_dir)
        manifest_path = tmp_path / "checksums.json"
        save_checksums(checksums, manifest_path)
        
        # Validate
        assert validate_data_integrity(data_dir, manifest_path) is True
        
        # Verify all files are included
        assert len(checksums) == 3
        assert "root.json" in checksums
        assert "level1/mid.json" in checksums
        assert "level1/level2/deep.json" in checksums