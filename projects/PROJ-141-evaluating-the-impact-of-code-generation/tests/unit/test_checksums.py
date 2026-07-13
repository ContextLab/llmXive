"""
Unit tests for checksum generation and state file update.
"""
import os
import sys
import tempfile
import hashlib
import csv
import yaml
from pathlib import Path
from datetime import datetime, timezone

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.checksums import compute_file_hash, write_checksums_csv, update_state_file


def test_compute_file_hash():
    """Test file hash computation."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("test content")
        temp_path = Path(f.name)

    try:
        file_hash = compute_file_hash(temp_path)
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        assert file_hash == expected_hash, f"Hash mismatch: {file_hash} != {expected_hash}"
        print("✓ test_compute_file_hash passed")
    finally:
        temp_path.unlink()


def test_compute_file_hash_nonexistent():
    """Test hash computation for non-existent file."""
    fake_path = Path("/nonexistent/file.txt")
    result = compute_file_hash(fake_path)
    assert result is None, "Should return None for non-existent file"
    print("✓ test_compute_file_hash_nonexistent passed")


def test_write_checksums_csv():
    """Test CSV writing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_checksums.csv"
        checksums = [
            {"file_path": "data1.txt", "algorithm": "sha256", "hash": "abc123", "size_bytes": 100, "timestamp": "2024-01-01T00:00:00Z"},
            {"file_path": "data2.txt", "algorithm": "sha256", "hash": "def456", "size_bytes": 200, "timestamp": "2024-01-01T00:00:00Z"}
        ]

        write_checksums_csv(checksums, output_path)

        assert output_path.exists(), "CSV file should be created"

        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
        assert rows[0]["file_path"] == "data1.txt"
        assert rows[0]["hash"] == "abc123"
        print("✓ test_write_checksums_csv passed")


def test_write_empty_checksums_csv():
    """Test CSV writing with empty list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_empty.csv"
        write_checksums_csv([], output_path)

        assert output_path.exists(), "CSV file should be created even if empty"

        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 0, "Should have no data rows"
        print("✓ test_write_empty_checksums_csv passed")


def test_update_state_file():
    """Test state file update."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        checksums = [
            {"file_path": "data1.txt", "algorithm": "sha256", "hash": "abc123"},
            {"file_path": "data2.txt", "algorithm": "sha256", "hash": "def456"}
        ]

        update_state_file(checksums, state_path)

        assert state_path.exists(), "State file should be created"

        with open(state_path, "r") as f:
            state_data = yaml.safe_load(f)

        assert "artifact_hashes" in state_data, "artifact_hashes should be present"
        assert state_data["artifact_hashes"]["data1.txt"] == "abc123"
        assert state_data["artifact_hashes"]["data2.txt"] == "def456"
        assert "last_checksum_update" in state_data, "last_checksum_update should be present"
        print("✓ test_update_state_file passed")


def test_update_state_file_existing():
    """Test updating existing state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"

        # Create initial state
        initial_data = {"existing_key": "existing_value", "updated_at": "2024-01-01T00:00:00Z"}
        with open(state_path, "w") as f:
            yaml.dump(initial_data, f)

        checksums = [{"file_path": "new.txt", "algorithm": "sha256", "hash": "xyz789"}]
        update_state_file(checksums, state_path)

        with open(state_path, "r") as f:
            state_data = yaml.safe_load(f)

        assert state_data["existing_key"] == "existing_value", "Existing data should be preserved"
        assert state_data["artifact_hashes"]["new.txt"] == "xyz789"
        print("✓ test_update_state_file_existing passed")


if __name__ == "__main__":
    test_compute_file_hash()
    test_compute_file_hash_nonexistent()
    test_write_checksums_csv()
    test_write_empty_checksums_csv()
    test_update_state_file()
    test_update_state_file_existing()
    print("\nAll checksums tests passed!")
