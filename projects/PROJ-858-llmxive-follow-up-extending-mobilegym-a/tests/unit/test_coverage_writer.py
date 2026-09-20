"""
Unit tests for coverage_writer module (T028)
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from code.scheduler.coverage_writer import (
    write_coverage_vectors,
    calculate_file_checksum,
    update_checksum_file,
    load_aggregated_vectors
)
from code.utils.constants import get_semantic_proxies, get_coverage_vector_dimensions


class TestCoverageWriter:
    """Tests for the coverage writer functionality."""

    def test_write_coverage_vectors_creates_file(self, tmp_path):
        """Test that write_coverage_vectors creates the output file."""
        output_path = str(tmp_path / "coverage_vectors.json")
        test_vectors = [
            {
                "task_id": "task_001",
                "vector": [1, 0, 1, 0, 1],
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        
        result_path = write_coverage_vectors(test_vectors, output_path)
        
        assert os.path.exists(result_path)
        assert result_path == output_path
        
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "vectors" in data
        assert len(data["vectors"]) == 1

    def test_write_coverage_vectors_includes_metadata(self, tmp_path):
        """Test that metadata is correctly included in output."""
        output_path = str(tmp_path / "coverage_vectors.json")
        test_vectors = []
        
        write_coverage_vectors(test_vectors, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "generated_at" in data["metadata"]
        assert "vector_dimensions" in data["metadata"]
        assert "semantic_proxies" in data["metadata"]
        assert data["metadata"]["vector_dimensions"] == get_coverage_vector_dimensions()
        assert data["metadata"]["semantic_proxies"] == get_semantic_proxies()

    def test_calculate_file_checksum(self, tmp_path):
        """Test SHA-256 checksum calculation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_file_checksum(str(test_file))
        
        # Verify it's a valid SHA-256 hex string (64 chars)
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_update_checksum_file(self, tmp_path):
        """Test updating the checksums file."""
        # Create a test data file
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps({"test": "data"}))
        
        checksum_file = tmp_path / ".checksums.txt"
        
        update_checksum_file(str(data_file), str(checksum_file))
        
        assert checksum_file.exists()
        content = checksum_file.read_text()
        
        # Should contain the checksum and filename
        assert len(content.split()[0]) == 64  # Checksum length
        assert "data.json" in content

    def test_load_aggregated_vectors_from_file(self, tmp_path):
        """Test loading vectors from a JSON file."""
        input_file = tmp_path / "aggregated.json"
        test_data = [
            {"task_id": "t1", "vector": [1, 0]},
            {"task_id": "t2", "vector": [0, 1]}
        ]
        input_file.write_text(json.dumps(test_data))
        
        result = load_aggregated_vectors(str(input_file))
        
        assert len(result) == 2
        assert result[0]["task_id"] == "t1"

    def test_load_aggregated_vectors_empty_when_missing(self, tmp_path):
        """Test that missing file returns empty list."""
        result = load_aggregated_vectors(str(tmp_path / "nonexistent.json"))
        assert result == []

    def test_write_coverage_vectors_multiple_vectors(self, tmp_path):
        """Test writing multiple vectors."""
        output_path = str(tmp_path / "coverage_vectors.json")
        test_vectors = [
            {"task_id": f"task_{i}", "vector": [i % 2] * 5}
            for i in range(10)
        ]
        
        write_coverage_vectors(test_vectors, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data["vectors"]) == 10