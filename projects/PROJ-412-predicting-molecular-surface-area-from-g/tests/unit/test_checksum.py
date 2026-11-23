"""
Unit tests for the checksum utility module.
"""

import os
import tempfile
import json
from pathlib import Path
import pytest

from code.utils.checksum import (
    calculate_file_checksum,
    calculate_directory_checksum,
    verify_file_checksum,
    verify_directory_checksum,
    save_checksum_manifest,
    load_checksum_manifest,
    verify_manifest_checksums,
    SUPPORTED_ALGORITHMS,
    DEFAULT_ALGORITHM
)

@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_directory():
    """Create a temporary directory with test files."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test files
    (Path(temp_dir) / "file1.txt").write_text("Content 1")
    (Path(temp_dir) / "file2.txt").write_text("Content 2")
    (Path(temp_dir) / "subdir").mkdir()
    (Path(temp_dir) / "subdir" / "file3.txt").write_text("Content 3")
    
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

class TestCalculateFileChecksum:
    def test_sha256_checksum(self, temp_file):
        """Test SHA256 checksum calculation."""
        checksum = calculate_file_checksum(temp_file, 'sha256')
        assert len(checksum) == 64  # SHA256 produces 64 hex characters
        assert isinstance(checksum, str)
    
    def test_md5_checksum(self, temp_file):
        """Test MD5 checksum calculation."""
        checksum = calculate_file_checksum(temp_file, 'md5')
        assert len(checksum) == 32  # MD5 produces 32 hex characters
        assert isinstance(checksum, str)
    
    def test_known_file_content(self, temp_file):
        """Test checksum against known content."""
        # "Hello, World!" SHA256
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        checksum = calculate_file_checksum(temp_file, 'sha256')
        assert checksum == expected
    
    def test_nonexistent_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_file_checksum("/nonexistent/file.txt")
    
    def test_unsupported_algorithm(self, temp_file):
        """Test that ValueError is raised for unsupported algorithm."""
        with pytest.raises(ValueError):
            calculate_file_checksum(temp_file, 'unsupported')

class TestCalculateDirectoryChecksum:
    def test_directory_checksum(self, temp_directory):
        """Test directory checksum calculation."""
        result = calculate_directory_checksum(temp_directory, 'sha256')
        
        assert 'dir_checksum' in result
        assert 'files' in result
        assert 'file_count' in result
        assert 'algorithm' in result
        
        assert result['file_count'] == 3
        assert result['algorithm'] == 'sha256'
        assert len(result['files']) == 3
    
    def test_directory_checksum_filter_extensions(self, temp_directory):
        """Test directory checksum with extension filter."""
        result = calculate_directory_checksum(temp_directory, 'sha256', extensions=['.txt'])
        assert result['file_count'] == 3
    
    def test_nonexistent_directory(self):
        """Test that FileNotFoundError is raised for missing directory."""
        with pytest.raises(FileNotFoundError):
            calculate_directory_checksum("/nonexistent/directory")

class TestVerifyFileChecksum:
    def test_verify_correct_checksum(self, temp_file):
        """Test verification with correct checksum."""
        checksum = calculate_file_checksum(temp_file, 'sha256')
        assert verify_file_checksum(temp_file, checksum, 'sha256') is True
    
    def test_verify_incorrect_checksum(self, temp_file):
        """Test verification with incorrect checksum."""
        assert verify_file_checksum(temp_file, "wrong_checksum", 'sha256') is False

class TestVerifyDirectoryChecksum:
    def test_verify_correct_directory_checksum(self, temp_directory):
        """Test directory verification with correct checksum."""
        result = calculate_directory_checksum(temp_directory, 'sha256')
        assert verify_directory_checksum(temp_directory, result['dir_checksum'], 'sha256') is True
    
    def test_verify_incorrect_directory_checksum(self, temp_directory):
        """Test directory verification with incorrect checksum."""
        assert verify_directory_checksum(temp_directory, "wrong_checksum", 'sha256') is False

class TestChecksumManifest:
    def test_save_and_load_manifest(self, temp_file, temp_directory):
        """Test saving and loading a checksum manifest."""
        with tempfile.TemporaryDirectory() as temp_out:
            manifest_path = os.path.join(temp_out, "manifest.json")
            
            # Save manifest
            save_checksum_manifest([temp_file, os.path.join(temp_directory, "file1.txt")], manifest_path)
            
            # Load manifest
            manifest = load_checksum_manifest(manifest_path)
            
            assert 'created_at' in manifest
            assert 'algorithm' in manifest
            assert 'files' in manifest
            assert len(manifest['files']) == 2
    
    def test_verify_manifest_checksums(self, temp_file):
        """Test verifying all checksums in a manifest."""
        with tempfile.TemporaryDirectory() as temp_out:
            manifest_path = os.path.join(temp_out, "manifest.json")
            
            # Save manifest
            save_checksum_manifest([temp_file], manifest_path)
            
            # Verify checksums
            results = verify_manifest_checksums(manifest_path)
            
            assert results['all_passed'] is True
            assert results['total_files'] == 1
            assert results['passed_count'] == 1
            assert len(results['failed_files']) == 0

class TestEdgeCases:
    def test_empty_file(self):
        """Test checksum of an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            checksum = calculate_file_checksum(temp_path, 'sha256')
            # SHA256 of empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert checksum == expected
        finally:
            os.unlink(temp_path)
    
    def test_large_file_chunking(self):
        """Test that large files are processed in chunks."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            # Write 1MB of data
            f.write(b'x' * (1024 * 1024))
            temp_path = f.name
        
        try:
            checksum = calculate_file_checksum(temp_path, 'sha256', chunk_size=4096)
            assert len(checksum) == 64
        finally:
            os.unlink(temp_path)
