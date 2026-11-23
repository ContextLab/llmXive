"""
Unit tests for the sample validator module.
"""
import json
import tempfile
from pathlib import Path
import pytest

from ingest.sample_validator import is_valid_xyz_file, scan_raw_directory, write_sample_count


def create_dummy_xyz_file(path: Path, atom_count: int, valid: bool = True):
    """Helper to create a dummy XYZ file for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(f"{atom_count}\n")
        f.write(f"Dummy comment line for {atom_count} atoms\n")
        for i in range(atom_count):
            f.write(f"Si {i*1.0:.4f} {i*1.0:.4f} {i*1.0:.4f}\n")
    if not valid:
        # Corrupt the file if requested
        with open(path, 'r') as f:
            content = f.read()
        with open(path, 'w') as f:
            f.write("Not a valid XYZ file")


class TestIsValidXyzFile:
    def test_valid_xyz_with_enough_atoms(self, tmp_path):
        file_path = tmp_path / "valid.xyz"
        create_dummy_xyz_file(file_path, 1000)
        assert is_valid_xyz_file(file_path) is True

    def test_valid_xyz_with_more_atoms(self, tmp_path):
        file_path = tmp_path / "valid_large.xyz"
        create_dummy_xyz_file(file_path, 2000)
        assert is_valid_xyz_file(file_path) is True

    def test_invalid_xyz_too_few_atoms(self, tmp_path):
        file_path = tmp_path / "small.xyz"
        create_dummy_xyz_file(file_path, 500)
        assert is_valid_xyz_file(file_path) is False

    def test_invalid_xyz_not_xyz_extension(self, tmp_path):
        file_path = tmp_path / "valid.txt"
        create_dummy_xyz_file(file_path, 1000)
        assert is_valid_xyz_file(file_path) is False

    def test_invalid_xyz_nonexistent(self, tmp_path):
        file_path = tmp_path / "nonexistent.xyz"
        assert is_valid_xyz_file(file_path) is False

    def test_invalid_xyz_malformed(self, tmp_path):
        file_path = tmp_path / "malformed.xyz"
        create_dummy_xyz_file(file_path, 1000, valid=False)
        assert is_valid_xyz_file(file_path) is False

    def test_invalid_xyz_missing_comment(self, tmp_path):
        file_path = tmp_path / "no_comment.xyz"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write("1000\n")
            # No comment line
        assert is_valid_xyz_file(file_path) is False

    def test_invalid_xyz_wrong_atom_count(self, tmp_path):
        file_path = tmp_path / "wrong_count.xyz"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write("10\n")  # Claims 10 atoms
            f.write("Comment\n")
            for i in range(20):  # But has 20 lines
                f.write(f"Si {i:.4f} {i:.4f} {i:.4f}\n")
        assert is_valid_xyz_file(file_path) is False


class TestScanRawDirectory:
    def test_scan_empty_directory(self, tmp_path):
        result = scan_raw_directory(tmp_path)
        assert result == []

    def test_scan_directory_with_valid_files(self, tmp_path):
        valid1 = tmp_path / "sample_01.xyz"
        valid2 = tmp_path / "sample_02.xyz"
        create_dummy_xyz_file(valid1, 1000)
        create_dummy_xyz_file(valid2, 1500)

        result = scan_raw_directory(tmp_path)
        assert len(result) == 2
        assert valid1 in result
        assert valid2 in result

    def test_scan_directory_mixed_validity(self, tmp_path):
        valid = tmp_path / "valid.xyz"
        invalid = tmp_path / "invalid.xyz"
        create_dummy_xyz_file(valid, 1000)
        create_dummy_xyz_file(invalid, 500)  # Too few atoms

        result = scan_raw_directory(tmp_path)
        assert len(result) == 1
        assert valid in result
        assert invalid not in result


class TestWriteSampleCount:
    def test_write_sample_count(self, tmp_path):
        output_file = tmp_path / "count.json"
        write_sample_count(10, output_file)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert data["count"] == 10
        assert data["expected"] == 10
        assert data["status"] == "VERIFIED"
        assert "10 valid samples" in data["message"]

    def test_write_sample_count_failure(self, tmp_path):
        output_file = tmp_path / "count.json"
        write_sample_count(5, output_file)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert data["count"] == 5
        assert data["expected"] == 10
        assert data["status"] == "FAILED"
        assert "ERROR" in data["message"]
