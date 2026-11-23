import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path
import shutil

# Mock config to avoid side effects during tests
from unittest.mock import patch, MagicMock

from validate_data import (
    calculate_file_checksum,
    validate_data_file,
    count_processed_meta_analyses,
    aggregate_success_rate,
    write_success_rate_report,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_OUTPUT_DIR,
    TARGET_COUNT
)

@pytest.fixture
def temp_dirs():
    """Create temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        raw_dir = tmp_path / "data" / "raw"
        proc_dir = tmp_path / "data" / "processed"
        out_dir = tmp_path / "data" / "output"
        
        raw_dir.mkdir(parents=True)
        proc_dir.mkdir(parents=True)
        out_dir.mkdir(parents=True)
        
        # Patch the global constants
        with patch('validate_data.DATA_RAW_DIR', raw_dir), \
             patch('validate_data.DATA_PROCESSED_DIR', proc_dir), \
             patch('validate_data.DATA_OUTPUT_DIR', out_dir):
            yield {
                'raw': raw_dir,
                'processed': proc_dir,
                'output': out_dir,
                'root': tmp_path
            }

def test_calculate_file_checksum(temp_dirs):
    """Test checksum calculation."""
    file_path = temp_dirs['raw'] / "test.txt"
    file_path.write_text("Hello World")
    
    checksum = calculate_file_checksum(file_path)
    assert len(checksum) == 64  # SHA256 hex length
    assert checksum == "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"

def test_validate_data_file_valid_json(temp_dirs):
    """Test validation of a valid JSON file."""
    file_path = temp_dirs['raw'] / "valid.json"
    file_path.write_text(json.dumps({"key": "value"}))
    
    result = validate_data_file(file_path)
    assert result["status"] == "valid"
    assert "checksum" in result

def test_validate_data_file_missing(temp_dirs):
    """Test validation of a missing file."""
    file_path = temp_dirs['raw'] / "missing.json"
    
    result = validate_data_file(file_path)
    assert result["status"] == "missing"

def test_validate_data_file_empty(temp_dirs):
    """Test validation of an empty file."""
    file_path = temp_dirs['raw'] / "empty.json"
    file_path.touch()
    
    result = validate_data_file(file_path)
    assert result["status"] == "empty"

def test_validate_data_file_csv(temp_dirs):
    """Test validation of a valid CSV file."""
    file_path = temp_dirs['raw'] / "data.csv"
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df.to_csv(file_path, index=False)
    
    result = validate_data_file(file_path)
    assert result["status"] == "valid"
    assert result["rows"] == 2

def test_count_processed_meta_analyses_parquet(temp_dirs):
    """Test counting from parquet file."""
    # Create a fake parquet file
    file_path = temp_dirs['processed'] / "subsample_data.parquet"
    df = pd.DataFrame({
        "meta_id": [1, 1, 2, 3, 3, 3], # 3 unique IDs
        "k": [3, 4, 3, 3, 4, 5]
    })
    df.to_parquet(file_path)
    
    count = count_processed_meta_analyses()
    assert count == 3

def test_count_processed_meta_analyses_fallback_json(temp_dirs):
    """Test counting fallback to raw JSON files."""
    # Remove parquet if exists (simulate missing)
    (temp_dirs['processed'] / "subsample_data.parquet").unlink(missing_ok=True)
    
    # Create raw files
    (temp_dirs['raw'] / "meta_1.json").write_text("{}")
    (temp_dirs['raw'] / "meta_2.json").write_text("{}")
    (temp_dirs['raw'] / "meta_3.json").write_text("{}")
    # Exclude config files
    (temp_dirs['raw'] / "simulation_params.json").write_text("{}")
    
    count = count_processed_meta_analyses()
    assert count == 3

def test_aggregate_success_rate_meets_target(temp_dirs, caplog):
    """Test aggregation when target is met."""
    # Create enough files to meet target (50)
    for i in range(TARGET_COUNT):
        (temp_dirs['raw'] / f"meta_{i}.json").write_text("{}")
    
    with patch('validate_data.is_real_mode', return_value=True):
        report = aggregate_success_rate()
    
    assert report["actual_processed"] == TARGET_COUNT
    assert report["success_rate"] == 1.0
    assert report["meets_requirement"] is True
    assert report["mode"] == "real"

def test_aggregate_success_rate_below_target(temp_dirs):
    """Test aggregation when target is NOT met."""
    # Create fewer files than target
    for i in range(10):
        (temp_dirs['raw'] / f"meta_{i}.json").write_text("{}")
    
    with patch('validate_data.is_real_mode', return_value=False):
        report = aggregate_success_rate()
    
    assert report["actual_processed"] == 10
    assert report["success_rate"] == 0.2
    assert report["meets_requirement"] is False
    assert report["mode"] == "simulation"

def test_write_success_rate_report(temp_dirs):
    """Test writing the report file."""
    report = {
        "total_target": 50,
        "actual_processed": 25,
        "success_rate": 0.5,
        "mode": "simulation",
        "meets_requirement": False
    }
    
    path = write_success_rate_report(report)
    
    assert path.exists()
    with open(path) as f:
        loaded = json.load(f)
    
    assert loaded["actual_processed"] == 25
    assert loaded["mode"] == "simulation"