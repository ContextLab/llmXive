import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path
project_root = Path(__file__).resolve().parent.parent.parent
sys_path = str(project_root / "code")
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)

from utils.checksum_utils import (
    compute_file_checksum,
    generate_checksum_manifest,
    verify_checksums,
    initialize_data_structure
)

class TestChecksumUtils:
    
    def setup_method(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_root = Path(self.temp_dir) / "data"
        self.data_root.mkdir()
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_compute_file_checksum(self):
        """Test SHA-256 checksum computation."""
        test_file = self.data_root / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        checksum = compute_file_checksum(test_file)
        assert len(checksum) == 64  # SHA-256 hex length
        
        # Verify against known hash
        import hashlib
        expected = hashlib.sha256(content).hexdigest()
        assert checksum == expected
    
    def test_compute_file_checksum_missing(self):
        """Test checksum computation on missing file raises error."""
        missing_file = self.data_root / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_file)
    
    def test_initialize_data_structure(self):
        """Test that directory structure is created correctly."""
        initialize_data_structure(self.data_root)
        
        expected_dirs = ["raw", "processed", "validation"]
        for subdir in expected_dirs:
            dir_path = self.data_root / subdir
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"
            
            # Check for .gitkeep
            gitkeep = dir_path / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep missing in {dir_path}"
    
    def test_generate_checksum_manifest(self):
        """Test manifest generation."""
        # Create test files
        file1 = self.data_root / "raw" / "file1.txt"
        file1.parent.mkdir(parents=True, exist_ok=True)
        file1.write_text("content1")
        
        file2 = self.data_root / "processed" / "file2.txt"
        file2.parent.mkdir(parents=True, exist_ok=True)
        file2.write_text("content2")
        
        manifest_path = self.data_root / "manifest.json"
        relative_paths = [
            "raw/file1.txt",
            "processed/file2.txt"
        ]
        
        manifest = generate_checksum_manifest(self.data_root, relative_paths, manifest_path)
        
        assert manifest_path.exists()
        assert "files" in manifest
        assert "raw/file1.txt" in manifest["files"]
        assert "processed/file2.txt" in manifest["files"]
        
        # Verify checksums are valid hex
        for path, checksum in manifest["files"].items():
            assert len(checksum) == 64
            assert all(c in '0123456789abcdef' for c in checksum)
    
    def test_verify_checksums_success(self):
        """Test successful checksum verification."""
        # Create test file
        test_file = self.data_root / "raw" / "test.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("verify_me")
        
        # Generate manifest
        manifest_path = self.data_root / "manifest.json"
        generate_checksum_manifest(
            self.data_root, 
            ["raw/test.txt"], 
            manifest_path
        )
        
        # Verify
        all_valid, failed = verify_checksums(self.data_root, manifest_path)
        
        assert all_valid is True
        assert len(failed) == 0
    
    def test_verify_checksums_missing_file(self):
        """Test verification fails when file is missing."""
        # Create manifest referencing a non-existent file
        manifest = {
            "base_dir": str(self.data_root),
            "files": {
                "raw/missing.txt": "0000000000000000000000000000000000000000000000000000000000000000"
            }
        }
        manifest_path = self.data_root / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)
        
        all_valid, failed = verify_checksums(self.data_root, manifest_path)
        
        assert all_valid is False
        assert "raw/missing.txt" in failed
    
    def test_verify_checksums_corrupted(self):
        """Test verification fails when file content changes."""
        # Create file and manifest
        test_file = self.data_root / "raw" / "test.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("original")
        
        manifest_path = self.data_root / "manifest.json"
        generate_checksum_manifest(
            self.data_root, 
            ["raw/test.txt"], 
            manifest_path
        )
        
        # Corrupt file
        test_file.write_text("corrupted")
        
        all_valid, failed = verify_checksums(self.data_root, manifest_path)
        
        assert all_valid is False
        assert "raw/test.txt" in failed
    
    def test_verify_checksums_invalid_manifest(self):
        """Test verification fails with invalid JSON manifest."""
        manifest_path = self.data_root / "manifest.json"
        manifest_path.write_text("not valid json")
        
        all_valid, failed = verify_checksums(self.data_root, manifest_path)
        
        assert all_valid is False
        assert "Invalid manifest JSON" in failed
    
    def test_verify_checksums_missing_manifest(self):
        """Test verification fails if manifest file is missing."""
        missing_manifest = self.data_root / "nonexistent.json"
        
        all_valid, failed = verify_checksums(self.data_root, missing_manifest)
        
        assert all_valid is False
        assert "Manifest not found" in failed