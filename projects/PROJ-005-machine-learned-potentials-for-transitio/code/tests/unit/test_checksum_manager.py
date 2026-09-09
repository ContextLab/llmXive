"""
Unit tests for the checksum_manager module.
"""

import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import os

from src.data.checksum_manager import (
    compute_file_checksum,
    load_checksum_manifest,
    save_checksum_manifest,
    verify_checksum,
    verify_all_files,
    update_checksum_for_file,
    get_project_root
)


class TestComputeFileChecksum:
    def test_compute_checksum_valid_file(self, tmp_path):
        """Test computing checksum for a valid file"""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_file_checksum(test_file)
        
        # Verify against hashlib directly
        expected = hashlib.sha256(test_content).hexdigest()
        assert checksum == expected
        assert len(checksum) == 64  # SHA256 hex length
    
    def test_compute_checksum_binary_file(self, tmp_path):
        """Test computing checksum for a binary file"""
        test_file = tmp_path / "binary.bin"
        binary_content = bytes(range(256))
        test_file.write_bytes(binary_content)
        
        checksum = compute_file_checksum(test_file)
        expected = hashlib.sha256(binary_content).hexdigest()
        assert checksum == expected
    
    def test_compute_checksum_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError"""
        missing_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_file)


class TestChecksumManifest:
    def test_save_and_load_manifest(self, tmp_path):
        """Test saving and loading a checksum manifest"""
        manifest_path = tmp_path / "checksums.json"
        manifest_data = {
            'files': {
                'test.txt': {
                    'checksum': 'abc123',
                    'algorithm': 'sha256',
                    'size': 100
                }
            },
            'metadata': {
                'version': '1.0'
            }
        }
        
        save_checksum_manifest(manifest_path, manifest_data)
        assert manifest_path.exists()
        
        loaded = load_checksum_manifest(manifest_path)
        assert loaded == manifest_data
    
    def test_load_manifest_missing_file(self, tmp_path):
        """Test loading a non-existent manifest raises error"""
        missing_path = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_checksum_manifest(missing_path)
    
    def test_save_creates_parent_dirs(self, tmp_path):
        """Test that save creates parent directories"""
        nested_path = tmp_path / "subdir" / "nested" / "checksums.json"
        manifest_data = {'files': {}}
        
        save_checksum_manifest(nested_path, manifest_data)
        assert nested_path.exists()


class TestVerifyChecksum:
    def test_verify_checksum_valid(self, tmp_path):
        """Test verifying a file with correct checksum"""
        test_file = tmp_path / "test.txt"
        content = b"Test content"
        test_file.write_bytes(content)
        
        checksum = hashlib.sha256(content).hexdigest()
        is_valid, computed = verify_checksum(test_file, checksum)
        
        assert is_valid
        assert computed == checksum
    
    def test_verify_checksum_invalid(self, tmp_path):
        """Test verifying a file with wrong checksum"""
        test_file = tmp_path / "test.txt"
        content = b"Test content"
        test_file.write_bytes(content)
        
        wrong_checksum = "0" * 64
        is_valid, computed = verify_checksum(test_file, wrong_checksum)
        
        assert not is_valid
        assert computed != wrong_checksum


class TestVerifyAllFiles:
    def test_verify_all_files_empty_dir(self, tmp_path):
        """Test verification in empty directory"""
        manifest_path = tmp_path / "checksums.json"
        
        result = verify_all_files(tmp_path, manifest_path)
        
        assert result['all_valid'] is False  # No manifest
        assert len(result['missing_files']) == 0
        assert len(result['new_files']) == 0
    
    def test_verify_all_files_with_manifest(self, tmp_path):
        """Test verification with valid manifest"""
        # Create test file
        test_file = tmp_path / "test.txt"
        content = b"Test"
        test_file.write_bytes(content)
        
        # Create manifest
        checksum = hashlib.sha256(content).hexdigest()
        manifest = {
            'files': {
                'test.txt': {
                    'checksum': checksum,
                    'algorithm': 'sha256',
                    'size': len(content)
                }
            }
        }
        manifest_path = tmp_path / "checksums.json"
        save_checksum_manifest(manifest_path, manifest)
        
        result = verify_all_files(tmp_path, manifest_path)
        
        assert result['all_valid'] is True
        assert len(result['verified_files']) == 1
        assert result['verified_files'][0] == ('test.txt', 'valid')
    
    def test_verify_all_files_missing_file(self, tmp_path):
        """Test verification with missing file in manifest"""
        # Create manifest referencing non-existent file
        manifest = {
            'files': {
                'missing.txt': {
                    'checksum': 'abc',
                    'algorithm': 'sha256'
                }
            }
        }
        manifest_path = tmp_path / "checksums.json"
        save_checksum_manifest(manifest_path, manifest)
        
        result = verify_all_files(tmp_path, manifest_path)
        
        assert result['all_valid'] is False
        assert 'missing.txt' in result['missing_files']


class TestUpdateChecksumForFile:
    def test_update_checksum_new_file(self, tmp_path):
        """Test updating checksum for a new file"""
        test_file = tmp_path / "new.txt"
        test_file.write_bytes(b"New content")
        
        manifest_path = tmp_path / "checksums.json"
        update_checksum_for_file(test_file, manifest_path)
        
        assert manifest_path.exists()
        manifest = load_checksum_manifest(manifest_path)
        assert 'new.txt' in manifest['files']
        assert len(manifest['files']['new.txt']['checksum']) == 64
    
    def test_update_checksum_existing_file(self, tmp_path):
        """Test updating checksum for an existing file"""
        test_file = tmp_path / "existing.txt"
        test_file.write_bytes(b"Content 1")
        
        manifest_path = tmp_path / "checksums.json"
        
        # First update
        update_checksum_for_file(test_file, manifest_path)
        manifest1 = load_checksum_manifest(manifest_path)
        checksum1 = manifest1['files']['existing.txt']['checksum']
        
        # Change file content
        test_file.write_bytes(b"Content 2")
        
        # Second update
        update_checksum_for_file(test_file, manifest_path)
        manifest2 = load_checksum_manifest(manifest_path)
        checksum2 = manifest2['files']['existing.txt']['checksum']
        
        assert checksum1 != checksum2


class TestGetProjectRoot:
    def test_get_project_root_returns_path(self):
        """Test that get_project_root returns a Path object"""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()