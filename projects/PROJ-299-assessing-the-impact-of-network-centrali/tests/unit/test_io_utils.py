"""
Unit tests for io_utils.py (CSV read/write and checksum validation).
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from code.utils.io_utils import (
    calculate_file_checksum,
    verify_file_checksum,
    read_csv_as_dicts,
    write_dicts_to_csv,
    read_json,
    write_json,
    generate_checksum_file,
    verify_checksum_file,
)


class TestChecksumFunctions:
    """Tests for checksum calculation and verification."""

    def test_calculate_sha256_checksum(self, tmp_path):
        """Test SHA256 checksum calculation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = calculate_file_checksum(test_file, 'sha256')
        assert len(checksum) == 64  # SHA256 produces 64 hex chars
        assert isinstance(checksum, str)

    def test_calculate_md5_checksum(self, tmp_path):
        """Test MD5 checksum calculation."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test data")

        checksum = calculate_file_checksum(test_file, 'md5')
        assert len(checksum) == 32  # MD5 produces 32 hex chars

    def test_verify_correct_checksum(self, tmp_path):
        """Test verifying a correct checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Verify this")

        checksum = calculate_file_checksum(test_file)
        assert verify_file_checksum(test_file, checksum) is True

    def test_verify_wrong_checksum(self, tmp_path):
        """Test verifying an incorrect checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Original")

        fake_checksum = "a" * 64
        assert verify_file_checksum(test_file, fake_checksum) is False

    def test_calculate_checksum_nonexistent_file(self):
        """Test that checksum calculation raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            calculate_file_checksum("/nonexistent/file.txt")

    def test_verify_checksum_nonexistent_file(self):
        """Test that checksum verification raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            verify_file_checksum("/nonexistent/file.txt", "fake_checksum")

    def test_invalid_hash_algorithm(self, tmp_path):
        """Test that invalid algorithm raises ValueError."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Data")

        with pytest.raises(ValueError):
            calculate_file_checksum(test_file, 'invalid_algo')


class TestCSVFunctions:
    """Tests for CSV reading and writing."""

    def test_write_and_read_csv(self, tmp_path):
        """Test writing and reading back a CSV file."""
        test_data = [
            {"id": 1, "name": "Alice", "score": 95.5},
            {"id": 2, "name": "Bob", "score": 87.3},
            {"id": 3, "name": "Charlie", "score": 92.1},
        ]
        output_file = tmp_path / "test.csv"

        write_dicts_to_csv(test_data, output_file)
        assert output_file.exists()

        read_data = read_csv_as_dicts(output_file)
        
        assert len(read_data) == 3
        assert read_data[0]["id"] == "1"  # CSV reads as strings
        assert read_data[0]["name"] == "Alice"
        assert read_data[1]["name"] == "Bob"

    def test_read_nonexistent_csv(self):
        """Test reading a nonexistent CSV file."""
        with pytest.raises(FileNotFoundError):
            read_csv_as_dicts("/nonexistent/file.csv")

    def test_write_empty_csv(self, tmp_path):
        """Test writing an empty list to CSV."""
        output_file = tmp_path / "empty.csv"
        write_dicts_to_csv([], output_file)
        assert output_file.exists()
        assert output_file.stat().st_size == 0

    def test_csv_overwrite_false(self, tmp_path):
        """Test that overwrite=False raises error on existing file."""
        test_data = [{"col": "value"}]
        output_file = tmp_path / "test.csv"
        
        write_dicts_to_csv(test_data, output_file)
        
        with pytest.raises(FileExistsError):
            write_dicts_to_csv(test_data, output_file, overwrite=False)

    def test_csv_delimiter_custom(self, tmp_path):
        """Test CSV writing with custom delimiter."""
        test_data = [{"a": 1, "b": 2}]
        output_file = tmp_path / "test.tsv"
        
        write_dicts_to_csv(test_data, output_file, delimiter='\t')
        content = output_file.read_text()
        assert '\t' in content
        assert ',' not in content


class TestJSONFunctions:
    """Tests for JSON reading and writing."""

    def test_write_and_read_json(self, tmp_path):
        """Test writing and reading back a JSON file."""
        test_data = {
            "participants": [
                {"id": 1, "name": "Alice", "age": 65},
                {"id": 2, "name": "Bob", "age": 72}
            ],
            "metadata": {"version": "1.0"}
        }
        output_file = tmp_path / "test.json"

        write_json(test_data, output_file)
        assert output_file.exists()

        read_data = read_json(output_file)
        assert read_data == test_data
        assert len(read_data["participants"]) == 2

    def test_read_nonexistent_json(self):
        """Test reading a nonexistent JSON file."""
        with pytest.raises(FileNotFoundError):
            read_json("/nonexistent/file.json")

    def test_write_json_overwrite_false(self, tmp_path):
        """Test that overwrite=False raises error on existing file."""
        output_file = tmp_path / "test.json"
        write_json({"key": "value"}, output_file)
        
        with pytest.raises(FileExistsError):
            write_json({"key": "value"}, output_file, overwrite=False)

    def test_write_json_no_indent(self, tmp_path):
        """Test writing JSON without indentation (compact)."""
        test_data = {"a": 1, "b": 2}
        output_file = tmp_path / "compact.json"
        
        write_json(test_data, output_file, indent=None)
        content = output_file.read_text()
        assert '\n' not in content  # Should be single line
        assert ' ' in content  # But spaces after separators


class TestChecksumFileFunctions:
    """Tests for checksum file generation and verification."""

    def test_generate_and_verify_checksum_file(self, tmp_path):
        """Test generating and verifying a checksum file."""
        source_file = tmp_path / "source.txt"
        source_file.write_bytes(b"Content to checksum")
        
        checksum_file = tmp_path / "checksums.txt"
        generate_checksum_file(source_file, checksum_file)
        
        assert checksum_file.exists()
        
        # Verify the checksum
        results = verify_checksum_file(checksum_file, tmp_path)
        assert len(results) == 1
        assert results["source.txt"] is True

    def test_verify_checksum_file_nonexistent_source(self, tmp_path):
        """Test verifying checksum file when source is missing."""
        source_file = tmp_path / "source.txt"
        source_file.write_bytes(b"Original")
        
        checksum_file = tmp_path / "checksums.txt"
        generate_checksum_file(source_file, checksum_file)
        
        # Delete the source file
        source_file.unlink()
        
        results = verify_checksum_file(checksum_file, tmp_path)
        assert results["source.txt"] is False

    def test_verify_checksum_file_nonexistent_checksum_file(self):
        """Test verifying a nonexistent checksum file."""
        with pytest.raises(FileNotFoundError):
            verify_checksum_file("/nonexistent/checksums.txt")

    def test_generate_checksum_file_creates_directory(self, tmp_path):
        """Test that generate_checksum_file creates parent directories."""
        source_file = tmp_path / "source.txt"
        source_file.write_bytes(b"Data")
        
        nested_checksum_file = tmp_path / "subdir" / "nested" / "checksums.txt"
        generate_checksum_file(source_file, nested_checksum_file)
        
        assert nested_checksum_file.exists()
        assert nested_checksum_file.parent.exists()