"""
Unit tests for the verify_checksums script logic.
"""
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.checksum_manager import compute_file_checksum, save_checksum_manifest

def test_verify_all_files_valid():
    """Test verification of valid checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        data_dir = tmpdir_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        
        # Create a test file
        test_file = data_dir / "test.txt"
        test_content = b"Hello World"
        test_file.write_bytes(test_content)
        
        expected_hash = compute_file_checksum(test_file)
        
        # Create manifest
        manifest = {
            "data/raw/test.txt": expected_hash
        }
        manifest_file = data_dir / "checksums.json"
        save_checksum_manifest(manifest_file, manifest)
        
        # Import and run verification logic
        from src.data.checksum_manager import load_checksum_manifest, verify_all_files
        
        loaded_manifest = load_checksum_manifest(manifest_file)
        results = verify_all_files(loaded_manifest, data_dir)
        
        assert len(results) == 1
        file_path, (exp, act, is_valid) = list(results.items())[0]
        assert is_valid
        assert exp == act

def test_verify_all_files_mismatch():
    """Test verification detects mismatched checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        data_dir = tmpdir_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        
        # Create a test file
        test_file = data_dir / "test.txt"
        test_content = b"Hello World"
        test_file.write_bytes(test_content)
        
        # Create manifest with WRONG hash
        wrong_hash = hashlib.sha256(b"Wrong Content").hexdigest()
        manifest = {
            "data/raw/test.txt": wrong_hash
        }
        manifest_file = data_dir / "checksums.json"
        save_checksum_manifest(manifest_file, manifest)
        
        from src.data.checksum_manager import load_checksum_manifest, verify_all_files
        
        loaded_manifest = load_checksum_manifest(manifest_file)
        results = verify_all_files(loaded_manifest, data_dir)
        
        assert len(results) == 1
        file_path, (exp, act, is_valid) = list(results.items())[0]
        assert not is_valid
        assert exp != act

def test_verify_all_files_missing():
    """Test verification handles missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        data_dir = tmpdir_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        
        # Create manifest for a file that doesn't exist
        manifest = {
            "data/raw/missing.txt": "somehash"
        }
        manifest_file = data_dir / "checksums.json"
        save_checksum_manifest(manifest_file, manifest)
        
        from src.data.checksum_manager import load_checksum_manifest, verify_all_files
        
        loaded_manifest = load_checksum_manifest(manifest_file)
        results = verify_all_files(loaded_manifest, data_dir)
        
        assert len(results) == 1
        file_path, (exp, act, is_valid) = list(results.items())[0]
        assert not is_valid
        assert act is None