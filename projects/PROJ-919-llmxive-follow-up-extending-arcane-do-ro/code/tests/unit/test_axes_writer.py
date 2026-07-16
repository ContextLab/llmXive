"""
Unit tests for the axes writer module (T013).

Tests the functionality of writing validated axis definitions to JSONL format,
computing checksums, and verifying data integrity.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.services.axes_writer import (
    write_axes_to_jsonl,
    read_axes_from_jsonl,
    verify_axes_checksum,
    compute_file_checksum,
    get_axes_summary,
    ensure_derived_directory
)


@pytest.fixture
def temp_axes_file(tmp_path):
    """Create a temporary directory and file for testing."""
    test_file = tmp_path / "test_axes.jsonl"
    sample_data = [
        {
            "character": "TestChar",
            "coarse": {"type": "TestType", "description": "Test desc"},
            "fine": {"type": "TestFine", "description": "Fine desc"},
            "validation": {"passed": True}
        }
    ]
    with open(test_file, "w", encoding="utf-8") as f:
        for entry in sample_data:
            f.write(json.dumps(entry) + "\n")
    return test_file


@pytest.fixture
def sample_axes():
    """Provide sample axis data for testing."""
    return [
        {
            "character": "CharacterA",
            "coarse": {"type": "CoarseType1", "description": "Desc1"},
            "fine": {"type": "FineType1", "description": "FineDesc1"},
            "validation": {"passed": True}
        },
        {
            "character": "CharacterB",
            "coarse": {"type": "CoarseType2", "description": "Desc2"},
            "fine": {"type": "FineType2", "description": "FineDesc2"},
            "validation": {"passed": False}
        }
    ]


class TestWriteAxesToJsonl:
    def test_write_axes_creates_file(self, tmp_path, sample_axes):
        """Test that write_axes_to_jsonl creates the output file."""
        output_path = tmp_path / "output.jsonl"
        result_path = write_axes_to_jsonl(sample_axes, output_path=output_path)
        
        assert result_path.exists()
        assert result_path == output_path

    def test_write_axes_content_format(self, tmp_path, sample_axes):
        """Test that the output file contains valid JSON lines."""
        output_path = tmp_path / "output.jsonl"
        write_axes_to_jsonl(sample_axes, output_path=output_path)
        
        with open(output_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        assert len(lines) == len(sample_axes)
        for line in lines:
            parsed = json.loads(line.strip())
            assert "character" in parsed
            assert "coarse" in parsed
            assert "fine" in parsed

    def test_write_axes_adds_metadata(self, tmp_path, sample_axes):
        """Test that write_axes_to_jsonl adds timestamp and version if missing."""
        output_path = tmp_path / "output.jsonl"
        # Remove timestamp/version from sample to test auto-addition
        for entry in sample_axes:
            entry.pop("timestamp", None)
            entry.pop("version", None)
        
        write_axes_to_jsonl(sample_axes, output_path=output_path)
        
        with open(output_path, "r", encoding="utf-8") as f:
            line = f.readline()
            parsed = json.loads(line)
        
        assert "timestamp" in parsed
        assert "version" in parsed

    def test_write_empty_axes_raises_error(self, tmp_path):
        """Test that writing an empty list raises ValueError."""
        output_path = tmp_path / "empty.jsonl"
        with pytest.raises(ValueError, match="Cannot write empty axes list"):
            write_axes_to_jsonl([], output_path=output_path)

    def test_write_invalid_entry_raises_error(self, tmp_path):
        """Test that writing non-dict entries raises ValueError."""
        output_path = tmp_path / "invalid.jsonl"
        invalid_axes = [{"valid": True}, "invalid_string"]
        with pytest.raises(ValueError, match="is not a dictionary"):
            write_axes_to_jsonl(invalid_axes, output_path=output_path)

    def test_write_creates_checksum_file(self, tmp_path, sample_axes):
        """Test that a checksum file is created alongside the output."""
        output_path = tmp_path / "output.jsonl"
        write_axes_to_jsonl(sample_axes, output_path=output_path)
        
        checksum_path = tmp_path / "output.sha256"
        assert checksum_path.exists()


class TestReadAxesFromJsonl:
    def test_read_axes_returns_list(self, temp_axes_file):
        """Test that read_axes_from_jsonl returns a list of dicts."""
        axes = read_axes_from_jsonl(temp_axes_file)
        
        assert isinstance(axes, list)
        assert len(axes) == 1
        assert isinstance(axes[0], dict)

    def test_read_axes_preserves_content(self, temp_axes_file):
        """Test that read_axes_from_jsonl preserves original content."""
        axes = read_axes_from_jsonl(temp_axes_file)
        
        assert axes[0]["character"] == "TestChar"
        assert axes[0]["coarse"]["type"] == "TestType"

    def test_read_nonexistent_file_raises_error(self, tmp_path):
        """Test that reading a nonexistent file raises FileNotFoundError."""
        fake_path = tmp_path / "nonexistent.jsonl"
        with pytest.raises(FileNotFoundError):
            read_axes_from_jsonl(fake_path)

    def test_read_invalid_json_raises_error(self, tmp_path):
        """Test that reading invalid JSON raises JSONDecodeError."""
        invalid_file = tmp_path / "invalid.jsonl"
        with open(invalid_file, "w") as f:
            f.write("not valid json\n")
        
        with pytest.raises(json.JSONDecodeError):
            read_axes_from_jsonl(invalid_file)


class TestVerifyChecksum:
    def test_verify_valid_checksum(self, tmp_path, sample_axes):
        """Test that verify_axes_checksum returns True for valid file."""
        output_path = tmp_path / "valid.jsonl"
        write_axes_to_jsonl(sample_axes, output_path=output_path)
        
        assert verify_axes_checksum(output_path) is True

    def test_verify_mismatched_checksum(self, tmp_path, sample_axes):
        """Test that verify_axes_checksum returns False when file is modified."""
        output_path = tmp_path / "modified.jsonl"
        write_axes_to_jsonl(sample_axes, output_path=output_path)
        
        # Modify the file
        with open(output_path, "a") as f:
            f.write('{"modified": true}\n')
        
        assert verify_axes_checksum(output_path) is False

    def test_verify_missing_checksum_file(self, tmp_path):
        """Test that verify_axes_checksum raises error if checksum file missing."""
        jsonl_path = tmp_path / "no_checksum.jsonl"
        jsonl_path.write_text('{"test": true}\n')
        
        with pytest.raises(FileNotFoundError):
            verify_axes_checksum(jsonl_path)


class TestComputeChecksum:
    def test_compute_checksum_deterministic(self, tmp_path):
        """Test that checksum computation is deterministic."""
        test_file = tmp_path / "checksum_test.txt"
        test_file.write_text("test content")
        
        checksum1 = compute_file_checksum(test_file)
        checksum2 = compute_file_checksum(test_file)
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length

    def test_compute_checksum_content_sensitive(self, tmp_path):
        """Test that checksum changes with content."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("content A")
        file2.write_text("content B")
        
        assert compute_file_checksum(file1) != compute_file_checksum(file2)


class TestAxesSummary:
    def test_summary_empty_list(self):
        """Test summary for empty axes list."""
        summary = get_axes_summary([])
        assert summary["count"] == 0

    def test_summary_counts_characters(self, sample_axes):
        """Test that summary correctly counts unique characters."""
        summary = get_axes_summary(sample_axes)
        
        assert summary["total_count"] == 2
        assert summary["unique_characters"] == 2
        assert "CharacterA" in summary["character_list"]
        assert "CharacterB" in summary["character_list"]

    def test_summary_validates_status(self, sample_axes):
        """Test that summary correctly counts valid/invalid entries."""
        summary = get_axes_summary(sample_axes)
        
        assert summary["valid_count"] == 1
        assert summary["invalid_count"] == 1

    def test_summary_collects_types(self, sample_axes):
        """Test that summary collects coarse and fine types."""
        summary = get_axes_summary(sample_axes)
        
        assert "CoarseType1" in summary["coarse_types"]
        assert "CoarseType2" in summary["coarse_types"]
        assert "FineType1" in summary["fine_types"]
        assert "FineType2" in summary["fine_types"]


class TestEnsureDerivedDirectory:
    def test_ensure_creates_directory(self, tmp_path):
        """Test that ensure_derived_directory creates the directory."""
        # Patch the global constant for testing
        with patch("src.services.axes_writer.DERIVED_DATA_DIR", tmp_path / "test_derived"):
            ensure_derived_directory()
            assert (tmp_path / "test_derived").exists()

    def test_ensure_existing_directory(self, tmp_path):
        """Test that ensure_derived_directory does nothing if dir exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        with patch("src.services.axes_writer.DERIVED_DATA_DIR", existing_dir):
            ensure_derived_directory()
            assert existing_dir.exists()
