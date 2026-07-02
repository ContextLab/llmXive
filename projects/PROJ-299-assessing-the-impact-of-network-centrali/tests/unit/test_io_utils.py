"""
Unit tests for io_utils module (T008).
Tests CSV reading/writing and checksum validation.
"""
import csv
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.io_utils import (
    calculate_checksum,
    read_csv,
    write_csv,
    validate_csv_integrity,
    write_checksum_file,
    load_checksum_file
)


class TestCalculateChecksum:
    def test_checksum_sha256(self, tmp_path):
        """Test SHA256 checksum calculation."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        checksum = calculate_checksum(test_file, 'sha256')
        # Known SHA256 for "Hello, World!"
        expected = "7f83b1657ff1fc53b92dc18148a1d65dfa7d5f3d5c8d4e0c1f5f5f5f5f5f5f5f"
        # Actually calculate expected
        import hashlib
        expected = hashlib.sha256(content).hexdigest()

        assert checksum == expected
        assert len(checksum) == 64  # SHA256 hex length

    def test_checksum_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_checksum("/nonexistent/file.txt")

    def test_checksum_invalid_algorithm(self, tmp_path):
        """Test error handling for invalid algorithm."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with pytest.raises(ValueError):
            calculate_checksum(test_file, 'invalid_algo')


class TestReadCsv:
    def test_read_csv_basic(self, tmp_path):
        """Test basic CSV reading."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name,value\n1,Alice,100\n2,Bob,200\n")

        data = read_csv(csv_file)

        assert len(data) == 2
        assert data[0]['id'] == '1'
        assert data[0]['name'] == 'Alice'
        assert data[1]['name'] == 'Bob'

    def test_read_csv_required_columns(self, tmp_path):
        """Test required column validation."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name\n1,Alice\n")

        # Should pass
        data = read_csv(csv_file, required_columns=['id', 'name'])
        assert len(data) == 1

        # Should fail
        with pytest.raises(ValueError) as exc_info:
            read_csv(csv_file, required_columns=['id', 'missing_col'])
        assert 'missing_col' in str(exc_info.value)

    def test_read_csv_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            read_csv("/nonexistent/file.csv")

    def test_read_csv_empty_file(self, tmp_path):
        """Test handling of empty CSV file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")

        with pytest.raises(ValueError):
            read_csv(csv_file)


class TestWriteCsv:
    def test_write_csv_basic(self, tmp_path):
        """Test basic CSV writing."""
        output_file = tmp_path / "output.csv"
        data = [
            {'id': '1', 'name': 'Alice', 'value': '100'},
            {'id': '2', 'name': 'Bob', 'value': '200'}
        ]

        result = write_csv(output_file, data)

        assert result.exists()
        with open(result, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['name'] == 'Alice'

    def test_write_csv_fieldnames(self, tmp_path):
        """Test writing with explicit fieldnames."""
        output_file = tmp_path / "output.csv"
        data = [
            {'name': 'Alice', 'id': '1'},  # Different order
            {'name': 'Bob', 'id': '2'}
        ]
        fieldnames = ['id', 'name']

        write_csv(output_file, data, fieldnames=fieldnames)

        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == fieldnames

    def test_write_csv_no_overwrite(self, tmp_path):
        """Test overwrite behavior."""
        output_file = tmp_path / "output.csv"
        output_file.write_text("existing")

        with pytest.raises(FileExistsError):
            write_csv(output_file, [{'id': '1'}], overwrite=False)

    def test_write_csv_empty_data(self, tmp_path):
        """Test writing empty data."""
        output_file = tmp_path / "output.csv"
        result = write_csv(output_file, [])

        assert result.exists()
        assert result.stat().st_size == 0  # Empty file


class TestValidateCsvIntegrity:
    def test_validate_integrity_success(self, tmp_path):
        """Test successful integrity validation."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name\n1,Alice\n")

        checksum = calculate_checksum(csv_file)

        assert validate_csv_integrity(csv_file, checksum) is True

    def test_validate_integrity_failure(self, tmp_path):
        """Test failed integrity validation."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name\n1,Alice\n")

        assert validate_csv_integrity(csv_file, "wrong_checksum") is False

    def test_validate_integrity_file_not_found(self, tmp_path):
        """Test integrity check on missing file."""
        assert validate_csv_integrity(tmp_path / "missing.csv", "checksum") is False


class TestWriteChecksumFile:
    def test_write_checksum_file(self, tmp_path):
        """Test writing checksum file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        checksum_file = write_checksum_file(test_file)

        assert checksum_file.exists()
        content = checksum_file.read_text()
        assert test_file.name in content

    def test_write_checksum_custom_path(self, tmp_path):
        """Test writing checksum to custom path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        custom_path = tmp_path / "custom.sha256"
        result = write_checksum_file(test_file, custom_path)

        assert result == custom_path
        assert custom_path.exists()


class TestLoadChecksumFile:
    def test_load_checksum_file(self, tmp_path):
        """Test loading checksum file."""
        checksum_file = tmp_path / "checksums.sha256"
        checksum_file.write_text("abc123  file1.txt\ndef456  file2.txt\n")

        checksums = load_checksum_file(checksum_file)

        assert checksums['file1.txt'] == 'abc123'
        assert checksums['file2.txt'] == 'def456'

    def test_load_checksum_file_missing(self, tmp_path):
        """Test loading missing checksum file."""
        with pytest.raises(FileNotFoundError):
            load_checksum_file(tmp_path / "missing.sha256")