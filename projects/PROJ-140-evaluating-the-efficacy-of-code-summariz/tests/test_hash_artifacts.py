"""
Unit tests for hash_artifacts.py
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from utils.hash_artifacts import (
    compute_file_hash,
    hash_directory,
    hash_artifacts,
    verify_artifact_integrity,
    HASHED_EXTENSIONS
)


class TestComputeFileHash:
    """Tests for compute_file_hash function."""
    
    def test_hash_simple_file(self, tmp_path):
        """Test hashing a simple text file."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        hash1 = compute_file_hash(test_file)
        hash2 = compute_file_hash(test_file)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in hash1)
    
    def test_hash_python_file(self, tmp_path):
        """Test hashing a Python file."""
        test_file = tmp_path / "test.py"
        content = "def hello():\n    return 'World'\n"
        test_file.write_text(content)
        
        hash_val = compute_file_hash(test_file)
        assert len(hash_val) == 64
    
    def test_hash_empty_file(self, tmp_path):
        """Test hashing an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()
        
        hash_val = compute_file_hash(test_file)
        # SHA-256 of empty string
        assert hash_val == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    def test_hash_nonexistent_file(self, tmp_path):
        """Test hashing a non-existent file raises error."""
        test_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_hash(test_file)
    
    def test_hash_large_file(self, tmp_path):
        """Test hashing a larger file."""
        test_file = tmp_path / "large.txt"
        content = "x" * (1024 * 1024)  # 1MB
        test_file.write_text(content)
        
        hash_val = compute_file_hash(test_file)
        assert len(hash_val) == 64
        
        # Verify hash is consistent
        assert compute_file_hash(test_file) == hash_val


class TestHashDirectory:
    """Tests for hash_directory function."""
    
    def test_hash_single_file(self, tmp_path):
        """Test hashing a directory with a single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        hashes = hash_directory(tmp_path)
        
        assert len(hashes) == 1
        assert "test.txt" in hashes[0] if isinstance(hashes, list) else "test.txt" in list(hashes.keys())[0]
    
    def test_hash_multiple_files(self, tmp_path):
        """Test hashing a directory with multiple files."""
        (tmp_path / "file1.py").write_text("code1")
        (tmp_path / "file2.txt").write_text("text2")
        (tmp_path / "file3.md").write_text("md3")
        
        hashes = hash_directory(tmp_path)
        
        assert len(hashes) == 3
        assert "file1.py" in [Path(k).name for k in hashes.keys()]
        assert "file2.txt" in [Path(k).name for k in hashes.keys()]
        assert "file3.md" in [Path(k).name for k in hashes.keys()]
    
    def test_hash_excludes_unsupported_extensions(self, tmp_path):
        """Test that unsupported extensions are excluded."""
        (tmp_path / "supported.py").write_text("code")
        (tmp_path / "unsupported.xyz").write_text("data")
        
        hashes = hash_directory(tmp_path)
        
        assert "supported.py" in [Path(k).name for k in hashes.keys()]
        assert "unsupported.xyz" not in [Path(k).name for k in hashes.keys()]
    
    def test_hash_nested_directories(self, tmp_path):
        """Test hashing nested directory structure."""
        nested = tmp_path / "subdir" / "nested"
        nested.mkdir(parents=True)
        (nested / "deep.py").write_text("deep code")
        (tmp_path / "root.py").write_text("root code")
        
        hashes = hash_directory(tmp_path)
        
        assert len(hashes) == 2
        # Check that both files are present
        file_names = [Path(k).name for k in hashes.keys()]
        assert "deep.py" in file_names
        assert "root.py" in file_names
    
    def test_nonexistent_directory(self, tmp_path):
        """Test hashing a non-existent directory raises error."""
        with pytest.raises(FileNotFoundError):
            hash_directory(tmp_path / "nonexistent")


class TestVerifyArtifactIntegrity:
    """Tests for verify_artifact_integrity function."""
    
    def test_verify_correct_hash(self, tmp_path):
        """Test verifying a file with correct hash."""
        test_file = tmp_path / "test.txt"
        content = "Test content"
        test_file.write_text(content)
        
        actual_hash = compute_file_hash(test_file)
        
        assert verify_artifact_integrity(test_file, actual_hash) is True
    
    def test_verify_incorrect_hash(self, tmp_path):
        """Test verifying a file with incorrect hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        assert verify_artifact_integrity(test_file, "wronghash123") is False
    
    def test_verify_nonexistent_file(self, tmp_path):
        """Test verifying a non-existent file returns False."""
        test_file = tmp_path / "nonexistent.txt"
        
        assert verify_artifact_integrity(test_file, "anyhash") is False


class TestHashArtifacts:
    """Tests for hash_artifacts function."""
    
    def test_hash_default_directories(self, tmp_path):
        """Test hashing default directories."""
        # Create a mock project structure
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "test.py").write_text("code")
        
        # Temporarily override PROJECT_ROOT
        import utils.hash_artifacts as ha
        original_root = ha.PROJECT_ROOT
        ha.PROJECT_ROOT = tmp_path
        
        try:
            hashes = hash_artifacts([code_dir])
            
            assert len(hashes) > 0
            assert any("code" in k for k in hashes.keys())
        finally:
            ha.PROJECT_ROOT = original_root
    
    def test_hash_nonexistent_directory(self, tmp_path):
        """Test that nonexistent directories are handled gracefully."""
        import utils.hash_artifacts as ha
        original_root = ha.PROJECT_ROOT
        ha.PROJECT_ROOT = tmp_path
        
        try:
            hashes = hash_artifacts([tmp_path / "nonexistent"])
            # Should not raise, just skip
            assert isinstance(hashes, dict)
        finally:
            ha.PROJECT_ROOT = original_root


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
