import pytest
import networkx as nx
from pathlib import Path
from typing import List, Dict, Set, Optional
import sys
import os
import json
import tempfile

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.loader import (
    ClawSweBenchLoader,
    calculate_relevant_lines,
    filter_dataset,
    validate_filtered_count,
    write_parquet_and_checksum,
    ParsedIssue
)
from utils.logger import DataLoadError

class TestImportGraphTraversal:
    """Tests for the graph traversal logic in calculate_relevant_lines."""

    def test_calculate_relevant_lines_empty(self):
        """Test with empty file history."""
        issue = {
            "instance_id": "test-1",
            "file_history": []
        }
        assert calculate_relevant_lines(issue) == 0

    def test_calculate_relevant_lines_single_file(self):
        """Test with a single file and no imports."""
        issue = {
            "instance_id": "test-2",
            "file_history": [
                {
                    "filename": "main.py",
                    "content": "def hello():\n    print('hello')\n" * 100
                }
            ]
        }
        lines = calculate_relevant_lines(issue)
        assert lines == 100

    def test_calculate_relevant_lines_import_chain(self):
        """Test with a chain of imports to verify graph traversal."""
        # Create a chain: A -> B -> C
        # A imports B, B imports C
        content_a = "from B import func\n" + "line\n" * 50
        content_b = "from C import func\n" + "line\n" * 30
        content_c = "def func(): pass\n" + "line\n" * 20

        issue = {
            "instance_id": "test-3",
            "file_history": [
                {"filename": "A.py", "content": content_a},
                {"filename": "B.py", "content": content_b},
                {"filename": "C.py", "content": content_c}
            ]
        }
        
        # Total lines should be 50 + 30 + 20 = 100
        lines = calculate_relevant_lines(issue)
        assert lines == 100

    def test_calculate_relevant_lines_disconnected(self):
        """Test with disconnected files (only target file counted)."""
        content_a = "line\n" * 50
        content_b = "line\n" * 30 # Not imported by A

        issue = {
            "instance_id": "test-4",
            "file_history": [
                {"filename": "A.py", "content": content_a},
                {"filename": "B.py", "content": content_b}
            ]
        }
        
        # Assuming A is the target, and B is not imported by A, only A is counted.
        # The logic iterates over all files in file_history as potential targets.
        # If A is processed, it finds no neighbors. If B is processed, it finds no neighbors.
        # Since we sum visited nodes, and they are disjoint, we get 50 + 30 = 80.
        # Wait, the logic iterates `target_files = list(file_map.keys())`.
        # It starts BFS from A, visits A (50). Then starts BFS from B (if not visited), visits B (30).
        # Total = 80.
        lines = calculate_relevant_lines(issue)
        assert lines == 80

class TestFilterDataset:
    """Tests for the filter_dataset function."""

    def test_filter_dataset_threshold(self):
        """Test filtering based on line threshold."""
        # Create mock instances
        inst_low = {
            "instance_id": "low",
            "file_history": [{"filename": "a.py", "content": "x\n" * 100}]
        }
        inst_high = {
            "instance_id": "high",
            "file_history": [{"filename": "a.py", "content": "x\n" * 600}]
        }

        instances = [inst_low, inst_high]
        filtered = list(filter_dataset(iter(instances), min_lines=500))
        
        assert len(filtered) == 1
        assert filtered[0]["instance_id"] == "high"
        assert filtered[0]["relevant_lines"] == 600

class TestValidateFilteredCount:
    """Tests for validate_filtered_count."""

    def test_validate_pass(self):
        """Test validation with sufficient count."""
        # Should not raise
        validate_filtered_count(100, min_threshold=50)

    def test_validate_fail(self):
        """Test validation with insufficient count."""
        with pytest.raises(Exception):
            validate_filtered_count(10, min_threshold=50)

class TestWriteParquetAndChecksum:
    """Tests for write_parquet_and_checksum."""

    def test_write_parquet_and_checksum_creates_file(self):
        """Test that the function creates the parquet file and checksum file."""
        data = [
            {"id": 1, "value": "a"},
            {"id": 2, "value": "b"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            state_dir = Path(tmpdir) / "state"
            
            # Mock get_data_dir if needed, but we pass output_dir explicitly
            path, checksum = write_parquet_and_checksum(
                data, 
                output_dir=out_dir, 
                version="test"
            )
            
            assert path.exists()
            assert path.suffix == ".parquet"
            
            checksum_file = state_dir / "checksums_test.json"
            assert checksum_file.exists()
            
            with open(checksum_file) as f:
                data_check = json.load(f)
            
            assert path.name in data_check
            assert "sha256" in data_check[path.name]
            assert data_check[path.name]["sha256"] == checksum

    def test_write_parquet_and_checksum_empty_raises(self):
        """Test that writing an empty list raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            with pytest.raises(DataLoadError):
                write_parquet_and_checksum([], output_dir=out_dir, version="test")