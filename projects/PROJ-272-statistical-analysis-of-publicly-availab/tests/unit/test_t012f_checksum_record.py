import json
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from t012f_checksum_record import (
    compute_sha256,
    load_existing_checksums,
    save_checksums,
    find_dataset_archive
)
from config import ensure_dirs

class TestComputeSha256:
    def test_compute_sha256_valid_file(self):
        """Test computing SHA-256 for a valid file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Hello, World!")
            tmp_path = Path(tmp.name)
        
        try:
            expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
            result = compute_sha256(tmp_path)
            assert result == expected_hash
        finally:
            os.unlink(tmp_path)

    def test_compute_sha256_empty_file(self):
        """Test computing SHA-256 for an empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            expected_hash = hashlib.sha256(b"").hexdigest()
            result = compute_sha256(tmp_path)
            assert result == expected_hash
        finally:
            os.unlink(tmp_path)

    def test_compute_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / "nonexistent.txt"
            with pytest.raises(FileNotFoundError):
                compute_sha256(fake_path)

    def test_compute_sha256_large_file(self):
        """Test computing SHA-256 for a large file (chunking)."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Write 1MB of data
            large_data = b"0" * (1024 * 1024)
            tmp.write(large_data)
            tmp_path = Path(tmp.name)
        
        try:
            expected_hash = hashlib.sha256(large_data).hexdigest()
            result = compute_sha256(tmp_path)
            assert result == expected_hash
        finally:
            os.unlink(tmp_path)

class TestLoadExistingChecksums:
    def test_load_existing_checksums_file_exists(self):
        """Test loading checksums from an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump({"file1.txt": "hash1", "file2.txt": "hash2"}, tmp)
            tmp_path = Path(tmp.name)
        
        try:
            result = load_existing_checksums(tmp_path)
            assert result == {"file1.txt": "hash1", "file2.txt": "hash2"}
        finally:
            os.unlink(tmp_path)

    def test_load_existing_checksums_file_missing(self):
        """Test loading checksums from a missing file returns empty dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / "nonexistent.json"
            result = load_existing_checksums(fake_path)
            assert result == {}

class TestSaveChecksums:
    def test_save_checksums_creates_file(self):
        """Test that save_checksums creates the file and directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "checksums.json"
            checksums = {"test.txt": "abc123"}
            
            save_checksums(checksums, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == checksums

    def test_save_checksums_overwrites_existing(self):
        """Test that save_checksums overwrites an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump({"old": "hash"}, tmp)
            tmp_path = Path(tmp.name)
        
        try:
            new_checksums = {"new": "hash"}
            save_checksums(new_checksums, tmp_path)
            
            with open(tmp_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == new_checksums
            assert "old" not in loaded
        finally:
            os.unlink(tmp_path)

class TestFindDatasetArchive:
    def test_find_dataset_archive_finds_zip(self):
        """Test finding a .zip file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "data.zip").touch()
            (tmp_path / "readme.txt").touch()
            
            result = find_dataset_archive(tmp_path)
            assert result.name == "data.zip"

    def test_find_dataset_archive_finds_tar_gz(self):
        """Test finding a .tar.gz file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "data.tar.gz").touch()
            
            result = find_dataset_archive(tmp_path)
            assert result.name == "data.tar.gz"

    def test_find_dataset_archive_no_archive_fallbacks_to_recent(self):
        """Test fallback to most recent file when no archive found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create files with different timestamps
            file1 = tmp_path / "file1.txt"
            file2 = tmp_path / "file2.txt"
            file1.touch()
            # Sleep to ensure different timestamps
            import time
            time.sleep(0.1)
            file2.touch()
            
            result = find_dataset_archive(tmp_path)
            assert result.name == "file2.txt"

    def test_find_dataset_archive_empty_directory(self):
        """Test returning None for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            result = find_dataset_archive(tmp_path)
            assert result is None
