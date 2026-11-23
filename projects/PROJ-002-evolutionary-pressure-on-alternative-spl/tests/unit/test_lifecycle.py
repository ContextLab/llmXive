"""
Unit tests for lifecycle management retention hooks.

Tests for check_file_age, record_metadata, get_file_metadata, and list_files_by_age.
"""
import os
import json
import time
import tempfile
from pathlib import Path
import pytest
from datetime import datetime

from code.pipeline.lifecycle import (
    check_file_age,
    record_metadata,
    get_file_metadata,
    list_files_by_age
)


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix="lifecycle_test_")
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_file(temp_test_dir):
    """Create a sample file for testing."""
    test_file = temp_test_dir / "sample.txt"
    test_file.write_text("Test content for lifecycle tests")
    return test_file


class TestCheckFileAge:
    """Tests for check_file_age function."""

    def test_file_is_fresh(self, sample_file):
        """Test that a newly created file is considered fresh."""
        # File was just created, should be fresh with 10 second threshold
        is_old = check_file_age(sample_file, age_threshold_seconds=10.0)
        assert is_old is False

    def test_file_is_old(self, temp_test_dir):
        """Test that an old file is correctly identified."""
        old_file = temp_test_dir / "old_file.txt"
        old_file.write_text("Old content")
        
        # Touch the file to set a specific old timestamp
        old_timestamp = time.time() - 100  # 100 seconds ago
        os.utime(old_file, (old_timestamp, old_timestamp))
        
        # Check with 10 second threshold - should be old
        is_old = check_file_age(old_file, age_threshold_seconds=10.0)
        assert is_old is True

    def test_nonexistent_file_raises(self, temp_test_dir):
        """Test that checking a non-existent file raises FileNotFoundError."""
        missing_file = temp_test_dir / "missing.txt"
        
        with pytest.raises(FileNotFoundError):
            check_file_age(missing_file, age_threshold_seconds=10.0)

    def test_path_types(self, sample_file):
        """Test that both string and Path objects are accepted."""
        # Test with string path
        is_old_str = check_file_age(str(sample_file), age_threshold_seconds=10.0)
        
        # Test with Path object
        is_old_path = check_file_age(sample_file, age_threshold_seconds=10.0)
        
        assert is_old_str == is_old_path


class TestRecordMetadata:
    """Tests for record_metadata function."""

    def test_creates_new_manifest(self, temp_test_dir, sample_file):
        """Test that a new manifest is created if it doesn't exist."""
        manifest_path = temp_test_dir / "new_manifest.json"
        
        record_metadata(
            file_path=sample_file,
            metadata={"key": "value"},
            output_manifest=manifest_path
        )
        
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        assert "entries" in data
        assert len(data["entries"]) == 1
        assert data["entries"][0]["file_name"] == sample_file.name

    def test_appends_to_existing_manifest(self, temp_test_dir, sample_file):
        """Test that metadata is appended to an existing manifest."""
        manifest_path = temp_test_dir / "existing_manifest.json"
        
        # Create initial manifest
        initial_data = {"entries": [{"file_name": "previous.txt"}]}
        with open(manifest_path, 'w') as f:
            json.dump(initial_data, f)
        
        # Add new entry
        record_metadata(
            file_path=sample_file,
            metadata={"key": "value"},
            output_manifest=manifest_path
        )
        
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        assert len(data["entries"]) == 2
        assert data["entries"][1]["file_name"] == sample_file.name

    def test_records_correct_metadata(self, temp_test_dir, sample_file):
        """Test that all expected metadata fields are recorded."""
        manifest_path = temp_test_dir / "metadata_test.json"
        
        record_metadata(
            file_path=sample_file,
            metadata={"custom_field": "custom_value"},
            output_manifest=manifest_path
        )
        
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        entry = data["entries"][0]
        
        # Check standard fields
        assert entry["file_path"] == str(sample_file)
        assert entry["file_name"] == sample_file.name
        assert "file_size_bytes" in entry
        assert "created_timestamp" in entry
        assert "modified_timestamp" in entry
        assert "recorded_at" in entry
        
        # Check custom metadata
        assert entry["custom_field"] == "custom_value"

    def test_nonexistent_file_raises(self, temp_test_dir):
        """Test that recording metadata for a non-existent file raises."""
        missing_file = temp_test_dir / "missing.txt"
        manifest_path = temp_test_dir / "manifest.json"
        
        with pytest.raises(FileNotFoundError):
            record_metadata(
                file_path=missing_file,
                metadata={},
                output_manifest=manifest_path
            )


class TestGetFileMetadata:
    """Tests for get_file_metadata function."""

    def test_returns_all_metadata_fields(self, sample_file):
        """Test that all metadata fields are returned."""
        metadata = get_file_metadata(sample_file)
        
        assert "file_path" in metadata
        assert "file_name" in metadata
        assert "file_size_bytes" in metadata
        assert "created_timestamp" in metadata
        assert "modified_timestamp" in metadata
        assert "accessed_timestamp" in metadata
        assert "age_seconds" in metadata

    def test_file_size_is_correct(self, sample_file):
        """Test that the recorded file size matches the actual size."""
        metadata = get_file_metadata(sample_file)
        actual_size = sample_file.stat().st_size
        
        assert metadata["file_size_bytes"] == actual_size

    def test_nonexistent_file_raises(self, temp_test_dir):
        """Test that getting metadata for a non-existent file raises."""
        missing_file = temp_test_dir / "missing.txt"
        
        with pytest.raises(FileNotFoundError):
            get_file_metadata(missing_file)


class TestListFilesByAge:
    """Tests for list_files_by_age function."""

    def test_returns_all_files(self, temp_test_dir):
        """Test that all files are returned when no filters are applied."""
        # Create test files
        for i in range(3):
            (temp_test_dir / f"file_{i}.txt").write_text(f"Content {i}")
        
        files = list_files_by_age(temp_test_dir)
        assert len(files) == 3

    def test_filters_by_extension(self, temp_test_dir):
        """Test that files are filtered by extension."""
        (temp_test_dir / "file1.txt").write_text("Text")
        (temp_test_dir / "file2.log").write_text("Log")
        (temp_test_dir / "file3.txt").write_text("Text")
        
        txt_files = list_files_by_age(temp_test_dir, extensions=['.txt'])
        assert len(txt_files) == 2
        assert all(f.suffix == '.txt' for f in txt_files)

    def test_filters_by_max_age(self, temp_test_dir):
        """Test that files are filtered by maximum age."""
        # Create a fresh file
        fresh_file = temp_test_dir / "fresh.txt"
        fresh_file.write_text("Fresh")
        
        # Create an old file
        old_file = temp_test_dir / "old.txt"
        old_file.write_text("Old")
        old_timestamp = time.time() - 100
        os.utime(old_file, (old_timestamp, old_timestamp))
        
        # Get files younger than 10 seconds
        fresh_files = list_files_by_age(temp_test_dir, max_age_seconds=10.0)
        
        assert len(fresh_files) == 1
        assert fresh_files[0].name == "fresh.txt"

    def test_filters_by_min_age(self, temp_test_dir):
        """Test that files are filtered by minimum age."""
        # Create a fresh file
        fresh_file = temp_test_dir / "fresh.txt"
        fresh_file.write_text("Fresh")
        
        # Create an old file
        old_file = temp_test_dir / "old.txt"
        old_file.write_text("Old")
        old_timestamp = time.time() - 100
        os.utime(old_file, (old_timestamp, old_timestamp))
        
        # Get files older than 10 seconds
        old_files = list_files_by_age(temp_test_dir, min_age_seconds=10.0)
        
        assert len(old_files) == 1
        assert old_files[0].name == "old.txt"

    def test_recursive_search(self, temp_test_dir):
        """Test that files are found recursively in subdirectories."""
        subdir = temp_test_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("Nested")
        
        files = list_files_by_age(temp_test_dir, extensions=['.txt'])
        assert len(files) == 1
        assert files[0].name == "nested.txt"

    def test_nonexistent_directory_raises(self, temp_test_dir):
        """Test that a non-existent directory raises an error."""
        missing_dir = temp_test_dir / "missing"
        
        with pytest.raises(FileNotFoundError):
            list_files_by_age(missing_dir)

    def test_file_path_raises(self, temp_test_dir):
        """Test that passing a file instead of directory raises an error."""
        test_file = temp_test_dir / "test.txt"
        test_file.write_text("Test")
        
        with pytest.raises(NotADirectoryError):
            list_files_by_age(test_file)