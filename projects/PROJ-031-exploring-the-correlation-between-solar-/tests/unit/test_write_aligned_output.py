"""
Unit tests for T017: write_aligned_output.py
"""
import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.write_aligned_output import write_aligned_events, compute_sha256

def test_write_aligned_events():
    """Test writing aligned events to CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_aligned.csv"
        data = [
            {"event_id": "1", "timestamp": "2023-01-01", "dst_min": "-50", "flare_flux": "1e-4"},
            {"event_id": "2", "timestamp": "2023-01-02", "dst_min": "-100", "flare_flux": "1e-3"}
        ]
        
        write_aligned_events(data, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]["event_id"] == "1"
        assert rows[1]["dst_min"] == "-100"

def test_compute_sha256():
    """Test SHA256 computation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        content = "Hello, World!"
        file_path.write_text(content)
        
        checksum = compute_sha256(str(file_path))
        expected = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        assert checksum == expected

def test_empty_data():
    """Test handling of empty data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "empty.csv"
        write_aligned_events([], output_path)
        # Should not crash, might create empty file or skip
        # Based on implementation, it returns early.
        assert not output_path.exists() # Or exists with 0 bytes depending on impl

if __name__ == "__main__":
    test_write_aligned_events()
    test_compute_sha256()
    test_empty_data()
    print("All tests passed.")
