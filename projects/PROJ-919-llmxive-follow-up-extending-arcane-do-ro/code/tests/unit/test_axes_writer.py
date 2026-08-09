import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.services.axes_writer import (
    ensure_derived_directory,
    compute_file_checksum,
    write_axes_to_jsonl,
    read_axes_from_jsonl,
    verify_axes_checksum,
    get_axes_summary,
)

@pytest.fixture
def temp_axes_file():
    """Create a temporary JSONL file with sample axis data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        sample_data = [
            {
                "timestamp": "2023-01-01T00:00:00",
                "character": "Char1",
                "coarse": {"name": "Coarse1"},
                "fine": {"name": "Fine1"},
                "validation_passed": True,
            },
            {
                "timestamp": "2023-01-02T00:00:00",
                "character": "Char2",
                "coarse": {"name": "Coarse2"},
                "fine": {"name": "Fine2"},
                "validation_passed": True,
            },
        ]
        for item in sample_data:
            f.write(json.dumps(item) + "\n")
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def sample_axes():
    """Return sample axis data for testing."""
    return [
        {
            "character": "TestChar",
            "coarse": {"axis_name": "Moral", "description": "Test"},
            "fine": {"axis_name": "Social", "description": "Test"},
            "validation_passed": True,
        }
    ]

class TestWriteAxesToJsonl:
    def test_writes_correct_format(self, sample_axes, tmp_path):
        """Test that write_axes_to_jsonl creates a valid JSONL file."""
        output_file = tmp_path / "test_axes.jsonl"
        # Mock ensure_derived_directory to return tmp_path
        with patch("src.services.axes_writer.ensure_derived_directory", return_value=tmp_path):
            result_path = write_axes_to_jsonl(sample_axes, output_file.name)

        assert result_path.exists()
        assert result_path.suffix == ".jsonl"

        with open(result_path, "r") as f:
            lines = f.readlines()

        assert len(lines) == len(sample_axes)
        parsed = json.loads(lines[0])
        assert "timestamp" in parsed
        assert "character" in parsed
        assert "coarse" in parsed
        assert "fine" in parsed

    def test_creates_directory_if_missing(self, sample_axes, tmp_path):
        """Test that the derived directory is created if it doesn't exist."""
        new_dir = tmp_path / "nonexistent" / "derived"
        with patch("src.services.axes_writer.ensure_derived_directory", return_value=new_dir):
            write_axes_to_jsonl(sample_axes, "test.jsonl")

        assert new_dir.exists()

class TestReadAxesFromJsonl:
    def test_reads_all_entries(self, temp_axes_file):
        """Test that read_axes_from_jsonl reads all valid entries."""
        data = read_axes_from_jsonl(temp_axes_file)
        assert len(data) == 2
        assert data[0]["character"] == "Char1"
        assert data[1]["character"] == "Char2"

    def test_handles_empty_lines(self, tmp_path):
        """Test that empty lines in the file are skipped."""
        file_path = tmp_path / "empty_lines.jsonl"
        with open(file_path, "w") as f:
            f.write('{"character": "A"}\n')
            f.write('\n')
            f.write('{"character": "B"}\n')

        data = read_axes_from_jsonl(file_path)
        assert len(data) == 2

    def test_raises_on_missing_file(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            read_axes_from_jsonl(Path("/nonexistent/file.jsonl"))

class TestVerifyChecksum:
    def test_verifies_correct_checksum(self, temp_axes_file):
        """Test verification with correct checksum."""
        checksum = compute_file_checksum(temp_axes_file)
        assert verify_axes_checksum(temp_axes_file, checksum) is True

    def test_fails_on_incorrect_checksum(self, temp_axes_file):
        """Test verification with incorrect checksum."""
        assert verify_axes_checksum(temp_axes_file, "wrong_checksum") is False

    def test_fails_on_missing_file(self):
        """Test verification fails gracefully for missing files."""
        assert verify_axes_checksum(Path("/missing.jsonl"), "any_checksum") is False

class TestComputeChecksum:
    def test_deterministic_checksum(self, temp_axes_file):
        """Test that checksum is deterministic."""
        checksum1 = compute_file_checksum(temp_axes_file)
        checksum2 = compute_file_checksum(temp_axes_file)
        assert checksum1 == checksum2

    def test_different_files_different_checksums(self, tmp_path):
        """Test that different files produce different checksums."""
        file1 = tmp_path / "file1.jsonl"
        file2 = tmp_path / "file2.jsonl"

        file1.write_text('{"a": 1}\n')
        file2.write_text('{"a": 2}\n')

        assert compute_file_checksum(file1) != compute_file_checksum(file2)

class TestAxesSummary:
    def test_generates_correct_summary(self, temp_axes_file):
        """Test that get_axes_summary returns correct statistics."""
        summary = get_axes_summary(temp_axes_file)

        assert summary["total_entries"] == 2
        assert "Char1" in summary["unique_characters"]
        assert "Char2" in summary["unique_characters"]
        assert summary["character_count"] == 2
        assert summary["checksum"] is not None

    def test_empty_file_summary(self, tmp_path):
        """Test summary for an empty file."""
        empty_file = tmp_path / "empty.jsonl"
        empty_file.touch()

        summary = get_axes_summary(empty_file)
        assert summary["total_entries"] == 0
        assert summary["unique_characters"] == []

class TestEnsureDerivedDirectory:
    def test_creates_directory(self, tmp_path):
        """Test that ensure_derived_directory creates the directory."""
        # Mock get_config to return tmp_path
        with patch("src.services.axes_writer.get_config") as mock_config:
            mock_config.return_value.data_dir = str(tmp_path)
            result = ensure_derived_directory()

        assert result.exists()
        assert result.name == "derived"