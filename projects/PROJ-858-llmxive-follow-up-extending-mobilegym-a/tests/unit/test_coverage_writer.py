"""
Unit tests for coverage_writer module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from scheduler.coverage_writer import (
    load_aggregated_vectors,
    write_coverage_vectors,
    calculate_file_checksum,
    update_checksum_file
)


class TestCoverageWriter:
    """Tests for coverage writer functionality."""

    def test_calculate_file_checksum(self, tmp_path):
        """Test checksum calculation for a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_file_checksum(str(test_file))
        
        # SHA-256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_write_coverage_vectors(self, tmp_path):
        """Test writing coverage vectors to JSON file."""
        test_vectors = [
            {"id": "task_1", "vector": [1, 0, 1, 0], "metadata": {"steps": 100}},
            {"id": "task_2", "vector": [0, 1, 1, 1], "metadata": {"steps": 150}}
        ]
        
        output_path = str(tmp_path / "coverage_vectors.json")
        
        result_path = write_coverage_vectors(test_vectors, output_path)
        
        assert os.path.exists(result_path)
        
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "vectors" in data
        assert len(data["vectors"]) == 2
        assert data["vectors"][0]["id"] == "task_1"
        assert data["vectors"][0]["vector"] == [1, 0, 1, 0]

    def test_write_coverage_vectors_creates_directory(self, tmp_path):
        """Test that write_coverage_vectors creates parent directories."""
        test_vectors = [{"id": "test", "vector": [1, 0]}]
        
        output_path = str(tmp_path / "subdir" / "coverage.json")
        
        result_path = write_coverage_vectors(test_vectors, output_path)
        
        assert os.path.exists(result_path)

    def test_update_checksum_file(self, tmp_path):
        """Test updating the checksum registry file."""
        test_file = tmp_path / "test_artifact.json"
        test_file.write_text('{"test": "data"}')
        
        checksum_file = tmp_path / "checksums.txt"
        
        update_checksum_file(str(test_file), str(checksum_file))
        
        assert checksum_file.exists()
        
        with open(checksum_file, 'r') as f:
            content = f.read()
        
        assert "test_artifact.json" in content
        assert calculate_file_checksum(str(test_file))[:16] in content

    def test_load_aggregated_vectors_from_file(self, tmp_path):
        """Test loading vectors from a specified file."""
        test_data = {
            "vectors": [
                {"id": "loaded_1", "vector": [1, 1, 0]},
                {"id": "loaded_2", "vector": [0, 0, 1]}
            ]
        }
        
        source_file = tmp_path / "source.json"
        with open(source_file, 'w') as f:
            json.dump(test_data, f)
        
        vectors = load_aggregated_vectors(str(source_file))
        
        assert len(vectors) == 2
        assert vectors[0]["id"] == "loaded_1"

    def test_load_aggregated_vectors_missing_file_raises(self, tmp_path):
        """Test that missing source file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_aggregated_vectors(str(tmp_path / "nonexistent.json"))

    def test_write_coverage_vectors_includes_metadata(self, tmp_path):
        """Test that written file includes proper metadata."""
        test_vectors = [{"id": "meta_test", "vector": [1, 0, 1]}]
        output_path = str(tmp_path / "meta_test.json")
        
        write_coverage_vectors(test_vectors, output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "generated_at" in data["metadata"]
        assert "total_vectors" in data["metadata"]
        assert data["metadata"]["total_vectors"] == 1
        assert data["metadata"]["version"] == "1.0"
