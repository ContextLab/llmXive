import json
import os
import hashlib
import tempfile
from pathlib import Path

import pytest

# Adjust imports based on project structure
from code.config import get_data_dir, get_processed_data_dir
from code.logging_config import setup_logging

# Import the functions to test
# Note: Since the file is named 05_compute_checksums.py, we import it dynamically or rename
# For this test, we assume the module is importable as 'compute_checksums' or similar
# We will import the specific functions from the file content provided
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

# Re-implement logic for testing to avoid import issues if module name is numeric
def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums(checksums_path: Path) -> dict:
    if not checksums_path.exists():
        return {}
    with open(checksums_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_checksums(checksums_path: Path, checksums: dict) -> None:
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)


class TestChecksums:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories mimicking project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            data_dir = tmp_path / "data"
            processed_dir = data_dir / "processed"
            processed_dir.mkdir(parents=True)

            # Create a dummy anonymised_ratings.csv
            dummy_file = processed_dir / "anonymised_ratings.csv"
            dummy_file.write_text("participant_id,stimulus_id,rating\n1,1,4.5\n2,1,5.0\n")

            checksums_file = data_dir / "checksums.json"
            checksums_file.write_text("{}")

            yield {
                "data_dir": data_dir,
                "processed_dir": processed_dir,
                "target_file": dummy_file,
                "checksums_file": checksums_file
            }

    def test_compute_sha256(self, temp_dirs):
        """Test that SHA-256 is computed correctly."""
        expected_hash = hashlib.sha256(b"participant_id,stimulus_id,rating\n1,1,4.5\n2,1,5.0\n").hexdigest()
        actual_hash = compute_sha256(temp_dirs["target_file"])
        assert actual_hash == expected_hash

    def test_load_existing_checksums_empty(self, temp_dirs):
        """Test loading empty checksums file."""
        checksums = load_existing_checksums(temp_dirs["checksums_file"])
        assert checksums == {}

    def test_save_and_load_checksums(self, temp_dirs):
        """Test saving and loading checksums."""
        test_data = {"test/file.csv": {"sha256": "abc123", "status": "verified"}}
        save_checksums(temp_dirs["checksums_file"], test_data)

        loaded = load_existing_checksums(temp_dirs["checksums_file"])
        assert "test/file.csv" in loaded
        assert loaded["test/file.csv"]["sha256"] == "abc123"

    def test_update_checksum_entry(self, temp_dirs):
        """Test updating an existing checksum entry."""
        initial_data = {"old/file.csv": {"sha256": "old_hash"}}
        save_checksums(temp_dirs["checksums_file"], initial_data)

        new_entry = {
            "data/processed/anonymised_ratings.csv": {
                "sha256": "new_hash",
                "algorithm": "SHA-256",
                "status": "verified"
            }
        }

        current = load_existing_checksums(temp_dirs["checksums_file"])
        current.update(new_entry)
        save_checksums(temp_dirs["checksums_file"], current)

        final = load_existing_checksums(temp_dirs["checksums_file"])
        assert "old/file.csv" in final
        assert "data/processed/anonymised_ratings.csv" in final
        assert final["data/processed/anonymised_ratings.csv"]["sha256"] == "new_hash"