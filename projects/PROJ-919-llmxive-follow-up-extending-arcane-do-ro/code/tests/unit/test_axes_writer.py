import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Add code to path if not already present
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.axes_writer import (
    ensure_derived_directory,
    compute_file_checksum,
    write_axes_to_jsonl,
    read_axes_from_jsonl,
    verify_axes_checksum,
    get_axes_summary
)

@pytest.fixture
def temp_axes_file():
    """Create a temporary JSONL file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = Path(f.name)
        # Write sample data
        sample_data = [
            {
                "timestamp": "2023-01-01T00:00:00",
                "data": {
                    "character": "TestChar",
                    "type": "coarse",
                    "axis_name": "Test Axis",
                    "description": "Test Description"
                }
            }
        ]
        for item in sample_data:
            f.write(json.dumps(item) + "\n")
    yield temp_path
    temp_path.unlink()

@pytest.fixture
def sample_axes():
    """Provide sample axis data."""
    return [
        {
            "character": "Scrooge",
            "type": "coarse",
            "axis_name": "Greed vs Generosity",
            "description": "The spectrum from selfish accumulation to selfless giving"
        },
        {
            "character": "Scrooge",
            "type": "fine",
            "axis_name": "Isolation vs Connection",
            "description": "The tendency to withdraw from social bonds versus seek them",
            "source_observation": "Observed in his rejection of Fred's invitation"
        }
    ]

class TestWriteAxesToJsonl:
    def test_write_creates_file(self, sample_axes, tmp_path):
        """Test that write_axes_to_jsonl creates the output file."""
        output_path = tmp_path / "test_axes.jsonl"
        result_path = write_axes_to_jsonl(sample_axes, output_path)
        
        assert result_path.exists()
        assert result_path == output_path

    def test_write_correct_format(self, sample_axes, tmp_path):
        """Test that the written file contains valid JSONL with correct structure."""
        output_path = tmp_path / "test_axes.jsonl"
        write_axes_to_jsonl(sample_axes, output_path)
        
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == len(sample_axes)
        
        for line, expected in zip(lines, sample_axes):
            record = json.loads(line)
            assert "timestamp" in record
            assert "data" in record
            assert record["data"]["character"] == expected["character"]

    def test_write_empty_list(self, tmp_path):
        """Test writing an empty list of axes."""
        output_path = tmp_path / "empty_axes.jsonl"
        result_path = write_axes_to_jsonl([], output_path)
        
        assert result_path.exists()
        assert result_path.stat().st_size == 0

    def test_write_invalid_format_raises(self, tmp_path):
        """Test that writing invalid format raises ValueError."""
        output_path = tmp_path / "invalid_axes.jsonl"
        with pytest.raises(ValueError):
            write_axes_to_jsonl(["invalid"], output_path)

class TestReadAxesFromJsonl:
    def test_read_valid_file(self, temp_axes_file):
        """Test reading from a valid JSONL file."""
        axes = read_axes_from_jsonl(temp_axes_file)
        assert len(axes) == 1
        assert axes[0]["character"] == "TestChar"

    def test_read_nonexistent_file(self, tmp_path):
        """Test that reading a nonexistent file raises FileNotFoundError."""
        non_existent = tmp_path / "does_not_exist.jsonl"
        with pytest.raises(FileNotFoundError):
            read_axes_from_jsonl(non_existent)

    def test_read_invalid_json(self, tmp_path):
        """Test that reading invalid JSON raises JSONDecodeError."""
        invalid_path = tmp_path / "invalid.jsonl"
        with open(invalid_path, 'w') as f:
            f.write("not valid json\n")
        
        with pytest.raises(json.JSONDecodeError):
            read_axes_from_jsonl(invalid_path)

class TestVerifyChecksum:
    def test_verify_correct_checksum(self, temp_axes_file):
        """Test verification with correct checksum."""
        checksum = compute_file_checksum(temp_axes_file)
        assert verify_axes_checksum(temp_axes_file, checksum) is True

    def test_verify_incorrect_checksum(self, temp_axes_file):
        """Test verification with incorrect checksum."""
        assert verify_axes_checksum(temp_axes_file, "wrong_checksum") is False

    def test_verify_nonexistent_file(self, tmp_path):
        """Test verification of nonexistent file raises error."""
        non_existent = tmp_path / "nonexistent.jsonl"
        with pytest.raises(FileNotFoundError):
            verify_axes_checksum(non_existent, "some_checksum")

class TestComputeChecksum:
    def test_checksum_deterministic(self, temp_axes_file):
        """Test that checksum is deterministic."""
        checksum1 = compute_file_checksum(temp_axes_file)
        checksum2 = compute_file_checksum(temp_axes_file)
        assert checksum1 == checksum2

    def test_checksum_changes_with_content(self, tmp_path):
        """Test that checksum changes when content changes."""
        file_path = tmp_path / "test.txt"
        with open(file_path, 'w') as f:
            f.write("content1")
        checksum1 = compute_file_checksum(file_path)
        
        with open(file_path, 'w') as f:
            f.write("content2")
        checksum2 = compute_file_checksum(file_path)
        
        assert checksum1 != checksum2

class TestAxesSummary:
    def test_summary_structure(self, temp_axes_file):
        """Test that summary has correct structure."""
        summary = get_axes_summary(temp_axes_file)
        
        assert "total_axes" in summary
        assert "coarse_count" in summary
        assert "fine_count" in summary
        assert "unique_characters" in summary
        assert "file_path" in summary
        assert "checksum" in summary

    def test_summary_counts(self, tmp_path):
        """Test summary counts are correct."""
        test_file = tmp_path / "summary_test.jsonl"
        axes = [
            {"timestamp": "t1", "data": {"character": "A", "type": "coarse"}},
            {"timestamp": "t2", "data": {"character": "A", "type": "fine"}},
            {"timestamp": "t3", "data": {"character": "B", "type": "coarse"}}
        ]
        
        with open(test_file, 'w') as f:
            for ax in axes:
                f.write(json.dumps(ax) + "\n")
        
        summary = get_axes_summary(test_file)
        
        assert summary["total_axes"] == 3
        assert summary["coarse_count"] == 2
        assert summary["fine_count"] == 1
        assert set(summary["unique_characters"]) == {"A", "B"}

class TestEnsureDerivedDirectory:
    @patch('src.services.axes_writer.get_config')
    def test_creates_directory(self, mock_config, tmp_path):
        """Test that ensure_derived_directory creates the directory."""
        mock_config.return_value = {
            "data": {
                "derived": str(tmp_path / "derived")
            }
        }
        
        result = ensure_derived_directory()
        
        assert result.exists()
        assert result.is_dir()

    @patch('src.services.axes_writer.get_config')
    def test_uses_existing_directory(self, mock_config, tmp_path):
        """Test that ensure_derived_directory uses existing directory."""
        derived_dir = tmp_path / "existing"
        derived_dir.mkdir()
        
        mock_config.return_value = {
            "data": {
                "derived": str(derived_dir)
            }
        }
        
        result = ensure_derived_directory()
        
        assert result == derived_dir
        assert result.exists()