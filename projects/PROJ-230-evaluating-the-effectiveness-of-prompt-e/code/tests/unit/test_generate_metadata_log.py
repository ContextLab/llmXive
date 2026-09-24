"""
Unit tests for generate_metadata_log.py
"""
import os
import sys
import json
import tempfile
import csv
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.generate_metadata_log import (
    scan_translation_dirs,
    extract_metadata,
    aggregate_metadata,
    save_metadata_log
)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory structure mimicking translation outputs."""
    temp_dir = tempfile.mkdtemp()
    base_path = Path(temp_dir)
    
    # Create condition directories
    condition1 = base_path / "zero_shot_basic"
    condition2 = base_path / "few_shot_style"
    condition1.mkdir()
    condition2.mkdir()
    
    # Create valid JSON files
    file1_data = {
        "input_id": "test-001",
        "seed": 42,
        "timestamp": "2024-01-01T12:00:00",
        "raw_output": "function test() { return true; }"
    }
    file2_data = {
        "input_id": "test-002",
        "seed": 123,
        "timestamp": "2024-01-01T12:05:00",
        "raw_output": "function test2() { return false; }"
    }
    
    with open(condition1 / "test-001.json", 'w') as f:
        json.dump(file1_data, f)
    
    with open(condition2 / "test-002.json", 'w') as f:
        json.dump(file2_data, f)
    
    # Create an invalid JSON file
    with open(condition1 / "invalid.json", 'w') as f:
        f.write("{ invalid json }")
    
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

def test_scan_translation_dirs(temp_output_dir):
    """Test that scan_translation_dirs finds all JSON files in condition directories."""
    base_path = Path(temp_output_dir)
    results = scan_translation_dirs(base_path)
    
    # Should find 2 valid JSON files (invalid.json is skipped by glob but might be included, 
    # but we filter later in extract_metadata)
    # Actually glob includes all .json files, so we expect 3 entries
    assert len(results) == 3
    
    # Check that we have files from both conditions
    conditions = [item[0] for item in results]
    assert "zero_shot_basic" in conditions
    assert "few_shot_style" in conditions

def test_extract_metadata_valid(temp_output_dir):
    """Test metadata extraction from a valid JSON file."""
    base_path = Path(temp_output_dir)
    valid_file = base_path / "zero_shot_basic" / "test-001.json"
    
    metadata = extract_metadata(valid_file)
    
    assert metadata is not None
    assert metadata['input_id'] == "test-001"
    assert metadata['seed'] == "42"
    assert metadata['timestamp'] == "2024-01-01T12:00:00"
    assert 'file_path' in metadata

def test_extract_metadata_invalid_json(temp_output_dir):
    """Test that invalid JSON files return None."""
    base_path = Path(temp_output_dir)
    invalid_file = base_path / "zero_shot_basic" / "invalid.json"
    
    metadata = extract_metadata(invalid_file)
    
    assert metadata is None

def test_extract_metadata_missing_input_id(temp_output_dir):
    """Test that files without input_id return None."""
    base_path = Path(temp_output_dir)
    condition1 = base_path / "zero_shot_basic"
    bad_file = condition1 / "bad.json"
    
    bad_data = {
        "seed": 42,
        "timestamp": "2024-01-01T12:00:00"
    }
    
    with open(bad_file, 'w') as f:
        json.dump(bad_data, f)
    
    metadata = extract_metadata(bad_file)
    
    assert metadata is None

def test_aggregate_metadata(temp_output_dir):
    """Test that aggregate_metadata correctly combines data from multiple files."""
    base_path = Path(temp_output_dir)
    files = scan_translation_dirs(base_path)
    
    aggregated = aggregate_metadata(files)
    
    # Should have 2 valid entries (invalid.json is skipped)
    assert len(aggregated) == 2
    
    # Check that all entries have required fields
    for entry in aggregated:
        assert 'prompt_condition' in entry
        assert 'input_id' in entry
        assert 'seed' in entry
        assert 'timestamp' in entry

def test_save_metadata_log_creates_csv(temp_output_dir):
    """Test that save_metadata_log creates a valid CSV file."""
    base_path = Path(temp_output_dir)
    files = scan_translation_dirs(base_path)
    aggregated = aggregate_metadata(files)
    
    output_file = Path(temp_output_dir) / "metadata_log.csv"
    save_metadata_log(aggregated, output_file)
    
    assert output_file.exists()
    
    # Read and verify CSV structure
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        # Check headers
        assert reader.fieldnames == ['prompt_condition', 'seed', 'timestamp', 'input_id']
        
        # Check row count
        assert len(rows) == 2
        
        # Verify no raw_output column exists (security check)
        for row in rows:
            assert 'raw_output' not in row
            assert 'file_path' not in row

def test_save_metadata_log_empty(temp_output_dir):
    """Test that save_metadata_log creates an empty CSV with headers when no data."""
    output_file = Path(temp_output_dir) / "empty_metadata.csv"
    save_metadata_log([], output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 0
        assert reader.fieldnames == ['prompt_condition', 'seed', 'timestamp', 'input_id']

def test_metadata_log_no_raw_outputs(temp_output_dir):
    """Critical test: Ensure the metadata log NEVER contains raw outputs."""
    base_path = Path(temp_output_dir)
    files = scan_translation_dirs(base_path)
    aggregated = aggregate_metadata(files)
    
    output_file = Path(temp_output_dir) / "security_check.csv"
    save_metadata_log(aggregated, output_file)
    
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # The raw code from the JSON files should NOT appear in the metadata log
        assert "function test() { return true; }" not in content
        assert "function test2() { return false; }" not in content