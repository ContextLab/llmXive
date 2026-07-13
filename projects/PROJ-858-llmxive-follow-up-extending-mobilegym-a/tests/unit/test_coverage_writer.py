"""
Unit tests for T028: coverage_writer.py
Tests the logic of writing vectors and calculating checksums.
"""
import json
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.scheduler.coverage_writer import (
    write_coverage_vectors,
    calculate_file_checksum,
    update_checksum_file
)
from utils.constants import get_coverage_vector_dimensions

def test_write_coverage_vectors_creates_file():
    """Test that write_coverage_vectors creates a valid JSON file."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_vectors.json")
        
        # Mock the output path temporarily
        with patch('code.scheduler.coverage_writer.OUTPUT_DIR', tmpdir):
            with patch('code.scheduler.coverage_writer.OUTPUT_FILE', test_file):
                vectors = [
                    {
                        "batch_id": "batch_001",
                        "vector": [1, 0, 1],
                        "dimensions": 3,
                        "active_count": 2,
                        "timestamp": "2023-10-27T10:00:00.000000+00:00"
                    }
                ]
                
                result_path = write_coverage_vectors(vectors)
                
                assert os.path.exists(result_path), "Output file was not created"
                
                with open(result_path, 'r') as f:
                    data = json.load(f)
                
                assert "metadata" in data
                assert "vectors" in data
                assert len(data["vectors"]) == 1
                assert data["vectors"][0]["batch_id"] == "batch_001"

def test_calculate_file_checksum():
    """Test that checksum calculation is deterministic and correct."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "checksum_test.txt")
        
        content = "Hello, World!"
        with open(test_file, 'w') as f:
            f.write(content)
        
        checksum1 = calculate_file_checksum(test_file)
        checksum2 = calculate_file_checksum(test_file)
        
        assert checksum1 == checksum2, "Checksums should be deterministic"
        assert len(checksum1) == 64, "SHA256 checksum should be 64 hex characters"

def test_update_checksum_file():
    """Test updating the checksum file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checksum_file = os.path.join(tmpdir, ".checksums.txt")
        test_path = "/fake/path/test.json"
        test_checksum = "abc123def456"
        
        # First write
        update_checksum_file(test_path, test_checksum)
        
        assert os.path.exists(checksum_file), "Checksum file not created"
        
        with open(checksum_file, 'r') as f:
            content = f.read()
        
        assert test_path in content
        assert test_checksum in content

if __name__ == "__main__":
    test_write_coverage_vectors_creates_file()
    test_calculate_file_checksum()
    test_update_checksum_file()
    print("All tests passed.")
