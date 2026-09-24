import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from ingestion import count_raw_records, save_raw_record_count, count_raw_records_from_csv

def test_count_raw_records_from_csv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,label,text\n1,AD,This is a test transcript with enough words.\n2,Control,Another test.\n")
        temp_path = f.name

    try:
        count = count_raw_records_from_csv(temp_path)
        assert count == 2
    finally:
        os.unlink(temp_path)

def test_save_raw_record_count():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "raw_record_count.json")
        count_raw_records.__globals__['ensure_dirs'] = lambda x: None  # Mock ensure_dirs for test
        save_raw_record_count(100, output_path)

        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data["raw_record_count"] == 100

def test_count_raw_records_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy files
        for i in range(5):
            Path(tmpdir, f"file_{i}.txt").touch()
        Path(tmpdir, "file_5.log").touch()  # Should not be counted

        count = count_raw_records(tmpdir)
        assert count == 5  # Only .txt files counted based on logic in function

def test_count_raw_records_invalid_path():
    with pytest.raises(ValueError):
        count_raw_records("nonexistent_file.xyz")

# Additional tests for other functions can be added as they are implemented
