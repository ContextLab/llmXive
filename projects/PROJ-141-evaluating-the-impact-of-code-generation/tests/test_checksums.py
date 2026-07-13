"""
Tests for checksum generation and state file update.
"""
import os
import sys
import tempfile
import shutil
import hashlib
import csv
import yaml
from pathlib import Path
from datetime import datetime

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from data.checksums import compute_file_hash, scan_data_directory, write_checksums_csv, update_state_file


class TestChecksumGeneration:
    """Test suite for checksum generation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()
        
        # Create test files
        self.test_file1 = self.data_dir / "test1.txt"
        self.test_file1.write_text("Hello, World!")
        
        self.test_file2 = self.data_dir / "test2.csv"
        self.test_file2.write_text("a,b,c\n1,2,3")
        
        self.subdir = self.data_dir / "subdir"
        self.subdir.mkdir()
        self.test_file3 = self.subdir / "test3.txt"
        self.test_file3.write_text("Nested file content")

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_compute_file_hash(self):
        """Test file hash computation."""
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = compute_file_hash(self.test_file1)
        assert actual_hash == expected_hash

    def test_compute_file_hash_binary(self):
        """Test file hash computation with binary data."""
        binary_content = b"\x00\x01\x02\x03\x04"
        test_file = self.data_dir / "binary.bin"
        test_file.write_bytes(binary_content)
        
        expected_hash = hashlib.sha256(binary_content).hexdigest()
        actual_hash = compute_file_hash(test_file)
        assert actual_hash == expected_hash

    def test_scan_data_directory(self):
        """Test scanning data directory for files."""
        checksums = scan_data_directory(self.data_dir)
        
        # Should find 3 files
        assert len(checksums) == 3
        
        # Check that all paths are present
        paths = [c["path"] for c in checksums]
        assert "test1.txt" in paths
        assert "test2.csv" in paths
        assert "subdir/test3.txt" in paths
        
        # Check that hashes are valid hex strings
        for entry in checksums:
            assert len(entry["hash"]) == 64  # SHA256 hex length
            assert entry["algorithm"] == "sha256"
            assert entry["size_bytes"] > 0

    def test_scan_data_directory_nonexistent(self):
        """Test scanning non-existent directory."""
        nonexistent = self.test_dir / "nonexistent"
        checksums = scan_data_directory(nonexistent)
        assert checksums == []

    def test_write_checksums_csv(self):
        """Test writing checksums to CSV."""
        output_file = self.test_dir / "checksums.csv"
        checksums = scan_data_directory(self.data_dir)
        
        write_checksums_csv(checksums, output_file)
        
        assert output_file.exists()
        
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        assert "path" in rows[0]
        assert "hash" in rows[0]
        assert "algorithm" in rows[0]
        assert "size_bytes" in rows[0]
        assert "timestamp" in rows[0]

    def test_update_state_file(self):
        """Test updating state file with artifact hashes."""
        state_file = self.test_dir / "state.yaml"
        checksums = scan_data_directory(self.data_dir)
        
        update_state_file(checksums, state_file)
        
        assert state_file.exists()
        
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f)
        
        assert "artifact_hashes" in state_data
        assert len(state_data["artifact_hashes"]) == 3
        assert "updated_at" in state_data
        
        # Check specific hash
        test1_hash = compute_file_hash(self.test_file1)
        assert state_data["artifact_hashes"]["test1.txt"] == test1_hash

    def test_update_state_file_existing(self):
        """Test updating existing state file."""
        state_file = self.test_dir / "state.yaml"
        
        # Create initial state
        initial_state = {
            "project_id": "TEST-001",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "artifact_hashes": {"old.txt": "oldhash"}
        }
        with open(state_file, "w") as f:
            yaml.dump(initial_state, f)
        
        checksums = scan_data_directory(self.data_dir)
        update_state_file(checksums, state_file)
        
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f)
        
        # Should preserve project_id and created_at
        assert state_data["project_id"] == "TEST-001"
        assert state_data["created_at"] == "2023-01-01T00:00:00"
        
        # Should update updated_at and artifact_hashes
        assert state_data["updated_at"] > "2023-01-01T00:00:00"
        assert len(state_data["artifact_hashes"]) == 3
        assert "old.txt" not in state_data["artifact_hashes"]

    def test_hash_consistency(self):
        """Test that hash computation is consistent."""
        hash1 = compute_file_hash(self.test_file1)
        hash2 = compute_file_hash(self.test_file1)
        assert hash1 == hash2