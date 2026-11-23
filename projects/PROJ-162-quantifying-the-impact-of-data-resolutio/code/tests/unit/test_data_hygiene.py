import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data_hygiene import (
    calculate_sha256,
    load_checksums,
    save_checksums,
    update_checksum,
    verify_checksum,
    verify_all_checksums,
    clean_state_file,
    get_state_summary,
    generate_all_checksums
)


class TestDataHygiene:

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_file(self, temp_dir):
        """Create a sample file with known content."""
        file_path = temp_dir / "test_file.txt"
        content = b"Hello, World! This is a test."
        file_path.write_bytes(content)
        return file_path

    def test_calculate_sha256(self, sample_file):
        """Test SHA256 calculation against a known value."""
        # The hash of b"Hello, World! This is a test."
        expected_hash = "8371319478335985797753730393757793039375779303937577930393757793" # Placeholder, calculate real one
        # Real hash calculation
        import hashlib
        real_hash = hashlib.sha256(b"Hello, World! This is a test.").hexdigest()

        calculated_hash = calculate_sha256(sample_file)
        assert calculated_hash == real_hash

    def test_calculate_sha256_file_not_found(self, temp_dir):
        """Test that FileNotFoundError is raised for missing files."""
        missing_file = temp_dir / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            calculate_sha256(missing_file)

    def test_load_checksums_empty(self, temp_dir):
        """Test loading checksums from a non-existent file."""
        state_path = temp_dir / "checksums.json"
        checksums = load_checksums(state_path)
        assert checksums == {}

    def test_load_checksums_valid(self, temp_dir):
        """Test loading valid checksums from a file."""
        state_path = temp_dir / "checksums.json"
        data = {"file1.txt": "hash1", "file2.txt": "hash2"}
        with open(state_path, "w") as f:
            json.dump(data, f)

        checksums = load_checksums(state_path)
        assert checksums == data

    def test_save_checksums(self, temp_dir):
        """Test saving checksums to a file."""
        state_path = temp_dir / "checksums.json"
        data = {"file1.txt": "hash1"}
        save_checksums(data, state_path)

        assert state_path.exists()
        with open(state_path, "r") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_verify_checksum_valid(self, sample_file):
        """Test verification of a valid checksum."""
        import hashlib
        real_hash = hashlib.sha256(sample_file.read_bytes()).hexdigest()
        assert verify_checksum(sample_file, real_hash) is True

    def test_verify_checksum_invalid(self, sample_file):
        """Test verification of an invalid checksum."""
        assert verify_checksum(sample_file, "invalid_hash") is False

    def test_verify_all_checksums(self, temp_dir):
        """Test verifying all checksums in a state file."""
        # Create files
        file1 = temp_dir / "f1.txt"
        file1.write_bytes(b"content1")
        file2 = temp_dir / "f2.txt"
        file2.write_bytes(b"content2")

        # Create state file with correct and incorrect hashes
        import hashlib
        h1 = hashlib.sha256(b"content1").hexdigest()
        h2_wrong = "wrong_hash"

        state_path = temp_dir / "checksums.json"
        data = {
            str(file1): h1,
            str(file2): h2_wrong
        }
        with open(state_path, "w") as f:
            json.dump(data, f)

        results = verify_all_checksums(state_path)
        assert results[str(file1)] is True
        assert results[str(file2)] is False

    def test_clean_state_file(self, temp_dir):
        """Test removing the state file."""
        state_path = temp_dir / "checksums.json"
        state_path.touch()
        assert state_path.exists()

        clean_state_file(state_path)
        assert not state_path.exists()

    def test_get_state_summary_empty(self, temp_dir):
        """Test summary when state file does not exist."""
        state_path = temp_dir / "checksums.json"
        summary = get_state_summary(state_path)
        assert summary["exists"] is False
        assert summary["file_count"] == 0

    def test_generate_all_checksums(self, temp_dir):
        """Test generating checksums for all files in a directory."""
        # Create files
        (temp_dir / "f1.txt").write_bytes(b"content1")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "f2.txt").write_bytes(b"content2")

        state_path = temp_dir / "state" / "checksums.json"

        checksums = generate_all_checksums(temp_dir, state_path)

        assert len(checksums) == 2
        assert state_path.exists()

        # Verify one hash
        import hashlib
        f1_path = temp_dir / "f1.txt"
        expected_h1 = hashlib.sha256(f1_path.read_bytes()).hexdigest()
        assert checksums[str(f1_path)] == expected_h1

    def test_generate_all_checksums_skips_self(self, temp_dir):
        """Test that the checksums file itself is not included in the scan."""
        (temp_dir / "f1.txt").write_bytes(b"content1")
        state_path = temp_dir / "state" / "checksums.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.touch() # Create the file first

        checksums = generate_all_checksums(temp_dir, state_path)

        # Should only contain f1.txt, not checksums.json
        assert len(checksums) == 1
        assert str(state_path) not in checksums