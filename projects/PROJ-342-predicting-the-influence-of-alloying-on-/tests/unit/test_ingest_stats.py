import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code to path if needed, though typically run from root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingest import write_ingestion_stats

def test_write_ingestion_stats():
    """
    Test that write_ingestion_stats correctly calculates and writes the JSON file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_stats.json")
        
        original = 100
        kept = 85
        
        stats = write_ingestion_stats(original, kept, output_path)
        
        # Verify return value
        assert stats["original_count"] == original
        assert stats["kept_count"] == kept
        assert stats["dropped_count"] == 15
        assert abs(stats["retention_rate"] - 0.85) < 1e-6
        
        # Verify file content
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data == stats

def test_write_ingestion_stats_zero_original():
    """
    Test behavior when original count is 0 (division by zero protection).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_stats_zero.json")
        
        original = 0
        kept = 0
        
        stats = write_ingestion_stats(original, kept, output_path)
        
        assert stats["original_count"] == 0
        assert stats["kept_count"] == 0
        assert stats["dropped_count"] == 0
        assert stats["retention_rate"] == 0.0
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data == stats
