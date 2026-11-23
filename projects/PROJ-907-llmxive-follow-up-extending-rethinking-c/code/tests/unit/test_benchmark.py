import pytest
import time
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.benchmark import validate_disjoint_sets, save_to_csv, save_to_json

class TestLatencyMeasurementLogic:
    """
    Unit tests for the benchmark script's latency measurement and validation logic.
    """

    def test_validate_disjoint_sets_valid(self):
        """Test that valid disjoint sets pass validation."""
        # Trace: 0-99, Benchmark: 100-149
        validate_disjoint_sets(trace_size=100, benchmark_start=100, benchmark_size=50)

    def test_validate_disjoint_sets_overlap_start(self):
        """Test that overlap at the start raises an error."""
        # Trace: 0-99, Benchmark: 90-139 (Overlap 90-99)
        with pytest.raises(ValueError, match="Benchmark set overlaps"):
            validate_disjoint_sets(trace_size=100, benchmark_start=90, benchmark_size=50)

    def test_validate_disjoint_sets_complete_overlap(self):
        """Test that complete overlap raises an error."""
        # Trace: 0-99, Benchmark: 0-49
        with pytest.raises(ValueError, match="Benchmark set overlaps"):
            validate_disjoint_sets(trace_size=100, benchmark_start=0, benchmark_size=50)

    def test_save_to_csv_creates_file(self):
        """Test that save_to_csv creates a file with headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.csv"
            data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
            save_to_csv(data, filepath)
            
            assert filepath.exists()
            with open(filepath, 'r') as f:
                content = f.read()
                assert "a,b" in content
                assert "1,2" in content

    def test_save_to_json_creates_file(self):
        """Test that save_to_json creates a file with JSON content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.json"
            data = [{"a": 1, "b": 2}]
            save_to_json(data, filepath)
            
            assert filepath.exists()
            with open(filepath, 'r') as f:
                content = json.load(f)
                assert len(content) == 1
                assert content[0]["a"] == 1

    def test_save_to_json_appends(self):
        """Test that save_to_json appends to existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.json"
            initial_data = [{"a": 1}]
            save_to_json(initial_data, filepath)
            
            new_data = [{"a": 2}]
            save_to_json(new_data, filepath)
            
            with open(filepath, 'r') as f:
                content = json.load(f)
                assert len(content) == 2
                assert content[0]["a"] == 1
                assert content[1]["a"] == 2