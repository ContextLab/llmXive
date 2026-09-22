import pytest
import json
import csv
import os
from pathlib import Path
import tempfile
import shutil

from data.finalize_dataset import (
    calculate_success_rate,
    compute_file_checksum,
    load_processed_data,
    save_dataset,
    save_success_rate_report
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    path = tempfile.mkdtemp()
    yield Path(path)
    shutil.rmtree(path)

def test_calculate_success_rate():
    """Test success rate calculation logic."""
    assert calculate_success_rate(95, 100) == 0.95
    assert calculate_success_rate(0, 100) == 0.0
    assert calculate_success_rate(100, 100) == 1.0
    assert calculate_success_rate(50, 200) == 0.25

def test_calculate_success_rate_zero_division():
    """Test success rate with zero input count."""
    assert calculate_success_rate(10, 0) == 0.0

def test_compute_file_checksum(temp_dir):
    """Test file checksum computation."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_file_checksum(test_file)
    assert len(checksum) == 64  # SHA256 hex length

def test_load_processed_data(temp_dir):
    """Test loading CSV data."""
    csv_file = temp_dir / "data.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['a', 'b'])
        writer.writeheader()
        writer.writerow({'a': '1', 'b': '2'})
        writer.writerow({'a': '3', 'b': '4'})
    
    data = load_processed_data(csv_file)
    assert len(data) == 2
    assert data[0] == {'a': '1', 'b': '2'}

def test_save_dataset(temp_dir):
    """Test saving dataset to CSV."""
    output_file = temp_dir / "output.csv"
    data = [{'a': '1', 'b': '2'}, {'a': '3', 'b': '4'}]
    
    save_dataset(data, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0] == {'a': '1', 'b': '2'}

def test_save_success_rate_report(temp_dir):
    """Test saving success rate report."""
    json_file = temp_dir / "report.json"
    
    save_success_rate_report(0.98, "PASS", None, json_file)
    
    assert json_file.exists()
    with open(json_file, 'r') as f:
        report = json.load(f)
        assert report['status'] == 'PASS'
        assert report['success_rate'] == 0.98
        assert report['reason'] is None

def test_save_success_rate_report_fail(temp_dir):
    """Test saving fail success rate report."""
    json_file = temp_dir / "report_fail.json"
    
    save_success_rate_report(0.90, "FAIL", "success_rate_below_threshold", json_file)
    
    assert json_file.exists()
    with open(json_file, 'r') as f:
        report = json.load(f)
        assert report['status'] == 'FAIL'
        assert report['reason'] == 'success_rate_below_threshold'
