import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.services.probes_writer import (
    ensure_derived_directory,
    compute_file_checksum,
    write_probes_to_jsonl,
    read_probes_from_jsonl,
    verify_probes_checksum,
    get_probes_summary
)

@pytest.fixture
def temp_probes_file():
    """Create a temporary JSONL file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        # Write sample probes
        sample_data = [
            {"character": "A", "probe_text": "Test 1", "character_status": "valid"},
            {"character": "B", "probe_text": "Test 2", "character_status": "invalid"},
            {"character": "A", "probe_text": "Test 3", "character_status": "valid"}
        ]
        for item in sample_data:
            f.write(json.dumps(item) + "\n")
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def sample_probes():
    """Return a list of sample probe dictionaries."""
    return [
        {"character": "Hero", "probe_text": "Scenario 1", "character_status": "valid"},
        {"character": "Villain", "probe_text": "Scenario 2", "character_status": "invalid"},
        {"character": "Hero", "probe_text": "Scenario 3", "character_status": "valid"}
    ]

class TestWriteProbesToJsonl:
    def test_write_creates_file(self, sample_probes, tmp_path):
        output_path = tmp_path / "test_probes.jsonl"
        result_path = write_probes_to_jsonl(sample_probes, output_path)
        
        assert result_path.exists()
        assert result_path == output_path
        
        # Verify content
        with open(result_path, 'r') as f:
            lines = f.readlines()
        assert len(lines) == len(sample_probes)
        
        # Check first line parses correctly
        first_probe = json.loads(lines[0])
        assert first_probe["character"] == "Hero"

    def test_write_adds_metadata(self, sample_probes, tmp_path):
        output_path = tmp_path / "test_probes.jsonl"
        write_probes_to_jsonl(sample_probes, output_path)
        
        with open(output_path, 'r') as f:
            first_line = json.loads(f.readline())
        
        assert "timestamp" in first_line
        assert "index" in first_line
        assert first_line["index"] == 0

    def test_write_empty_list(self, tmp_path):
        output_path = tmp_path / "empty_probes.jsonl"
        result_path = write_probes_to_jsonl([], output_path)
        
        assert result_path.exists()
        assert result_path.stat().st_size == 0

class TestReadProbesFromJsonl:
    def test_read_correct_count(self, temp_probes_file):
        probes = read_probes_from_jsonl(temp_probes_file)
        assert len(probes) == 3

    def test_read_preserves_data(self, temp_probes_file):
        probes = read_probes_from_jsonl(temp_probes_file)
        assert probes[0]["character"] == "A"
        assert probes[0]["probe_text"] == "Test 1"
        assert probes[1]["character_status"] == "invalid"

    def test_read_missing_file(self, tmp_path):
        missing_path = tmp_path / "nonexistent.jsonl"
        probes = read_probes_from_jsonl(missing_path)
        assert probes == []

class TestVerifyProbesChecksum:
    def test_verify_success(self, temp_probes_file):
        checksum = compute_file_checksum(temp_probes_file)
        assert verify_probes_checksum(temp_probes_file, checksum) is True

    def test_verify_failure(self, temp_probes_file):
        assert verify_probes_checksum(temp_probes_file, "fake_checksum") is False

    def test_verify_missing_file(self, tmp_path):
        missing_path = tmp_path / "missing.jsonl"
        assert verify_probes_checksum(missing_path, "any_checksum") is False

class TestComputeChecksum:
    def test_checksum_deterministic(self, temp_probes_file):
        checksum1 = compute_file_checksum(temp_probes_file)
        checksum2 = compute_file_checksum(temp_probes_file)
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length

    def test_checksum_changes_with_content(self, tmp_path):
        path1 = tmp_path / "file1.jsonl"
        path1.write_text('{"a": 1}\n')
        path2 = tmp_path / "file2.jsonl"
        path2.write_text('{"a": 2}\n')
        
        assert compute_file_checksum(path1) != compute_file_checksum(path2)

class TestProbesSummary:
    def test_summary_counts(self, sample_probes):
        summary = get_probes_summary(sample_probes)
        assert summary["count"] == 3
        assert summary["valid_count"] == 2
        assert summary["invalid_count"] == 1

    def test_summary_characters(self, sample_probes):
        summary = get_probes_summary(sample_probes)
        assert set(summary["characters"]) == {"Hero", "Villain"}

    def test_summary_empty(self):
        summary = get_probes_summary([])
        assert summary["count"] == 0
        assert summary["characters"] == []

class TestEnsureDerivedDirectory:
    @patch('src.services.probes_writer.get_config')
    def test_creates_directory(self, mock_get_config, tmp_path):
        mock_config = MagicMock()
        mock_config.data_dir = str(tmp_path / "data")
        mock_get_config.return_value = mock_config
        
        result = ensure_derived_directory()
        
        assert result.exists()
        assert result.name == "derived"