import json
import os
import tempfile
from pathlib import Path

import pytest

from checksums_generator import compute_file_checksum, generate_checksums, save_checksums
from config import get_path


def test_compute_file_checksum():
    """Test that checksum computation works for a known file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        checksum = compute_file_checksum(temp_path)
        assert len(checksum) == 64  # SHA-256 hex length
        assert isinstance(checksum, str)

        # Verify consistency
        checksum2 = compute_file_checksum(temp_path)
        assert checksum == checksum2
    finally:
        os.unlink(temp_path)


def test_compute_file_checksum_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("/nonexistent/file.txt"))


def test_generate_checksums():
    """Test generating checksums for multiple files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        # Temporarily modify get_path to use our temp directory
        original_get_path = get_path

        def mock_get_path(key):
            if key == "project_root":
                return tmp_path
            return original_get_path(key)

        # Patch the function in the module
        import checksums_generator
        original_func = checksums_generator.get_path
        checksums_generator.get_path = mock_get_path

        try:
            checksums = generate_checksums([file1, file2])
            assert len(checksums) == 2
            assert all(len(v) == 64 for v in checksums.values())
        finally:
            checksums_generator.get_path = original_func


def test_save_and_load_checksums():
    """Test that checksums can be saved and loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "checksums.json"
        test_checksums = {
            "file1.txt": "a" * 64,
            "file2.txt": "b" * 64
        }

        save_checksums(test_checksums, output_path)

        assert output_path.exists()

        with open(output_path, "r") as f:
            data = json.load(f)

        assert data["algorithm"] == "sha256"
        assert data["files"] == test_checksums