"""
Tests for data I/O utilities in src/utils/io.py.

These tests verify:
- Checksum computation and verification
- JSON/CSV serialization and deserialization
- Path validation and handling
- Error handling for invalid inputs
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.io import (
    validate_project_path,
    compute_file_checksum,
    verify_checksum,
    save_json,
    load_json,
    save_csv,
    load_csv,
    ensure_directory,
    get_file_size,
    list_files,
    atomic_write,
    get_relative_path,
    save_metadata,
    load_metadata,
    PROJECT_ROOT,
    DATA_DIR
)


class TestPathValidation:
    """Tests for path validation utilities."""

    def test_validate_project_path_valid(self):
        """Test validation of valid project paths."""
        result = validate_project_path("data")
        assert result.exists()
        assert result.is_dir()

    def test_validate_project_path_relative(self):
        """Test validation with relative paths."""
        result = validate_project_path("src/utils")
        assert result.exists()
        assert result.is_dir()

    def test_validate_project_path_outside_root(self):
        """Test that paths outside project root are rejected."""
        with pytest.raises(ValueError):
            validate_project_path("/etc/passwd", must_exist=True)

    def test_validate_project_path_nonexistent(self):
        """Test that nonexistent paths raise error when must_exist=True."""
        with pytest.raises(FileNotFoundError):
            validate_project_path("data/nonexistent_file.txt", must_exist=True)

    def test_validate_project_path_nonexistent_allowed(self):
        """Test that nonexistent paths are allowed when must_exist=False."""
        result = validate_project_path("data/new_file.txt", must_exist=False)
        assert not result.exists()

    def test_get_relative_path(self):
        """Test relative path conversion."""
        abs_path = PROJECT_ROOT / "data" / "test.txt"
        rel_path = get_relative_path(abs_path)
        assert str(rel_path) == "data/test.txt"


class TestChecksumming:
    """Tests for checksum utilities."""

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file for testing."""
        test_file = tmp_path / "test_checksum.txt"
        test_file.write_text("Hello, World!")
        return test_file

    def test_compute_checksum(self, temp_file):
        """Test checksum computation."""
        checksum = compute_file_checksum(temp_file)
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_verify_checksum_success(self, temp_file):
        """Test successful checksum verification."""
        checksum = compute_file_checksum(temp_file)
        assert verify_checksum(temp_file, checksum) is True

    def test_verify_checksum_failure(self, temp_file):
        """Test checksum verification failure."""
        with pytest.raises(ValueError):
            verify_checksum(temp_file, "invalid_checksum")

    def test_compute_checksum_nonexistent(self):
        """Test checksum computation on nonexistent file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("nonexistent_file.txt")

    def test_compute_checksum_invalid_algorithm(self, temp_file):
        """Test checksum with invalid algorithm."""
        with pytest.raises(ValueError):
            compute_file_checksum(temp_file, algorithm="invalid_algo")


class TestJSONOperations:
    """Tests for JSON serialization."""

    def test_save_and_load_json(self, tmp_path):
        """Test basic JSON save/load cycle."""
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        file_path = tmp_path / "test.json"

        saved_path = save_json(test_data, file_path)
        assert saved_path.exists()

        loaded_data = load_json(saved_path)
        assert loaded_data == test_data

    def test_save_json_creates_dirs(self, tmp_path):
        """Test that save_json creates parent directories."""
        test_data = {"data": "test"}
        file_path = tmp_path / "nested" / "dir" / "test.json"

        saved_path = save_json(test_data, file_path)
        assert saved_path.exists()

    def test_load_json_nonexistent_required(self):
        """Test loading nonexistent file with required=True."""
        with pytest.raises(FileNotFoundError):
            load_json("nonexistent.json", required=True)

    def test_load_json_nonexistent_optional(self):
        """Test loading nonexistent file with required=False."""
        result = load_json("nonexistent.json", required=False)
        assert result is None

    def test_save_invalid_json(self, tmp_path):
        """Test saving non-serializable data."""
        file_path = tmp_path / "test.json"
        with pytest.raises(TypeError):
            save_json(lambda x: x, file_path)


class TestCSVOperations:
    """Tests for CSV serialization."""

    def test_save_and_load_csv(self, tmp_path):
        """Test basic CSV save/load cycle."""
        test_data = [
            {"name": "Alice", "age": 30, "city": "NYC"},
            {"name": "Bob", "age": 25, "city": "LA"},
            {"name": "Charlie", "age": 35, "city": "Chicago"}
        ]
        file_path = tmp_path / "test.csv"

        saved_path = save_csv(test_data, file_path)
        assert saved_path.exists()

        loaded_data = load_csv(saved_path)
        assert len(loaded_data) == 3
        assert loaded_data[0]["name"] == "Alice"

    def test_save_csv_creates_dirs(self, tmp_path):
        """Test that save_csv creates parent directories."""
        test_data = [{"col": "val"}]
        file_path = tmp_path / "nested" / "test.csv"

        saved_path = save_csv(test_data, file_path)
        assert saved_path.exists()

    def test_load_csv_nonexistent_required(self):
        """Test loading nonexistent CSV with required=True."""
        with pytest.raises(FileNotFoundError):
            load_csv("nonexistent.csv", required=True)

    def test_load_csv_nonexistent_optional(self):
        """Test loading nonexistent CSV with required=False."""
        result = load_csv("nonexistent.csv", required=False)
        assert result == []

    def test_save_csv_empty_data(self, tmp_path):
        """Test saving empty CSV data."""
        file_path = tmp_path / "test.csv"
        with pytest.raises(ValueError):
            save_csv([], file_path)

    def test_save_csv_inconsistent_keys(self, tmp_path):
        """Test saving CSV with inconsistent row keys."""
        test_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "city": "LA"}  # Different keys
        ]
        file_path = tmp_path / "test.csv"
        with pytest.raises(ValueError):
            save_csv(test_data, file_path)

    def test_load_csv_type_conversion(self, tmp_path):
        """Test CSV type conversion."""
        test_data = [
            {"int_col": "42", "float_col": "3.14", "str_col": "hello"}
        ]
        file_path = tmp_path / "test.csv"
        save_csv(test_data, file_path)

        loaded = load_csv(file_path, convert_types=True)
        assert loaded[0]["int_col"] == 42
        assert loaded[0]["float_col"] == 3.14
        assert loaded[0]["str_col"] == "hello"


class TestDirectoryOperations:
    """Tests for directory utilities."""

    def test_ensure_directory(self, tmp_path):
        """Test directory creation."""
        new_dir = tmp_path / "new_dir"
        result = ensure_directory(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_ensure_directory_exists(self, tmp_path):
        """Test ensure_directory on existing directory."""
        result = ensure_directory(tmp_path)
        assert result.exists()

    def test_get_file_size(self, tmp_path):
        """Test file size retrieval."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello")

        size = get_file_size(test_file)
        assert size == 5

    def test_list_files(self, tmp_path):
        """Test file listing."""
        (tmp_path / "file1.txt").write_text("1")
        (tmp_path / "file2.csv").write_text("2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("3")

        files = list_files(tmp_path, pattern="*.txt")
        assert len(files) == 2

        files_recursive = list_files(tmp_path, pattern="*.txt", recursive=True)
        assert len(files_recursive) == 3


class TestAtomicWrite:
    """Tests for atomic write operations."""

    def test_atomic_write_text(self, tmp_path):
        """Test atomic write with text content."""
        file_path = tmp_path / "test.txt"
        content = "Hello, World!"

        result = atomic_write(content, file_path, mode='w')
        assert result.exists()
        assert result.read_text() == content

    def test_atomic_write_bytes(self, tmp_path):
        """Test atomic write with bytes content."""
        file_path = tmp_path / "test.bin"
        content = b"Binary content"

        result = atomic_write(content, file_path, mode='wb')
        assert result.exists()
        assert result.read_bytes() == content

    def test_atomic_write_creates_dirs(self, tmp_path):
        """Test atomic write creates parent directories."""
        file_path = tmp_path / "nested" / "dir" / "test.txt"
        content = "Test"

        result = atomic_write(content, file_path, mode='w')
        assert result.exists()


class TestMetadataOperations:
    """Tests for metadata utilities."""

    def test_save_and_load_metadata(self, tmp_path):
        """Test metadata save/load cycle."""
        metadata = {"experiment": "test", "version": 1}
        file_path = tmp_path / "metadata.json"

        saved_path = save_metadata(metadata, file_path)
        assert saved_path.exists()

        loaded = load_metadata(saved_path)
        assert loaded["experiment"] == "test"
        assert "created_at" in loaded

    def test_load_metadata_nonexistent(self, tmp_path):
        """Test loading nonexistent metadata file."""
        result = load_metadata(tmp_path / "nonexistent.json")
        assert result is None


class TestIntegration:
    """Integration tests combining multiple utilities."""

    def test_full_pipeline(self, tmp_path):
        """Test a complete data pipeline."""
        # Create test data
        test_data = [
            {"id": 1, "value": 10.5, "name": "Item 1"},
            {"id": 2, "value": 20.3, "name": "Item 2"},
            {"id": 3, "value": 30.7, "name": "Item 3"}
        ]

        # Save as CSV
        csv_path = tmp_path / "data.csv"
        save_csv(test_data, csv_path)

        # Verify checksum
        checksum = compute_file_checksum(csv_path)
        verify_checksum(csv_path, checksum)

        # Load and verify
        loaded_data = load_csv(csv_path)
        assert len(loaded_data) == 3
        assert loaded_data[0]["id"] == 1

        # Save metadata
        metadata = {
            "source": "test",
            "row_count": len(loaded_data),
            "checksum": checksum
        }
        meta_path = tmp_path / "metadata.json"
        save_metadata(metadata, meta_path)

        # Load metadata
        loaded_meta = load_metadata(meta_path)
        assert loaded_meta["row_count"] == 3
        assert loaded_meta["checksum"] == checksum

    def test_error_handling_chain(self, tmp_path):
        """Test error handling across multiple operations."""
        # Try to load nonexistent file
        with pytest.raises(FileNotFoundError):
            load_json("nonexistent.json", required=True)

        # Try to save invalid data
        file_path = tmp_path / "test.json"
        with pytest.raises(TypeError):
            save_json(lambda x: x, file_path)

        # Try to verify invalid checksum
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        with pytest.raises(ValueError):
            verify_checksum(test_file, "invalid")

        # Try to save empty CSV
        csv_path = tmp_path / "test.csv"
        with pytest.raises(ValueError):
            save_csv([], csv_path)