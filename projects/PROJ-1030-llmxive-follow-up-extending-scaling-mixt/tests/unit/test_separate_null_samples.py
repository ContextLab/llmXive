import os
import csv
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from labeling.separate_null_samples import (
    load_raw_labels,
    process_labels_and_exclusions,
    save_null_labels,
    save_final_labels,
    save_excluded_log,
    main
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_raw_csv(temp_dir):
    """Create a sample raw_labels.csv file."""
    filepath = temp_dir / "raw_labels.csv"
    data = [
        {"clip_id": "clip_001", "label": "valid", "confidence_score": "0.95", "reason": ""},
        {"clip_id": "clip_002", "label": "invalid", "confidence_score": "0.85", "reason": ""},
        {"clip_id": "clip_003", "label": "valid", "confidence_score": "0.45", "reason": ""},
        {"clip_id": "clip_004", "label": "valid", "confidence_score": "0.92", "reason": "Simulation failure"},
        {"clip_id": "clip_005", "label": "invalid", "confidence_score": "0.98", "reason": ""},
    ]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["clip_id", "label", "confidence_score", "reason"])
        writer.writeheader()
        writer.writerows(data)
    
    return filepath

def test_load_raw_labels(temp_dir, sample_raw_csv):
    """Test loading raw labels from CSV."""
    records = load_raw_labels(sample_raw_csv)
    
    assert len(records) == 5
    assert records[0]['clip_id'] == 'clip_001'
    assert records[0]['label'] == 'valid'
    assert isinstance(records[0]['confidence_score'], float)
    assert abs(records[0]['confidence_score'] - 0.95) < 1e-5

def test_process_labels_and_exclusions(sample_raw_csv):
    """Test separation of valid and null samples."""
    records = load_raw_labels(sample_raw_csv)
    valid, nulls = process_labels_and_exclusions(records, threshold=0.9)
    
    # clip_001 (0.95), clip_005 (0.98) should be valid
    # clip_002 (0.85), clip_003 (0.45), clip_004 (simulation failure) should be null
    assert len(valid) == 2
    assert len(nulls) == 3
    
    valid_ids = [r['clip_id'] for r in valid]
    assert 'clip_001' in valid_ids
    assert 'clip_005' in valid_ids
    
    null_ids = [r['clip_id'] for r in nulls]
    assert 'clip_002' in null_ids
    assert 'clip_003' in null_ids
    assert 'clip_004' in null_ids

def test_save_null_labels(temp_dir, sample_raw_csv):
    """Test saving null labels to CSV."""
    records = load_raw_labels(sample_raw_csv)
    _, nulls = process_labels_and_exclusions(records)
    
    output_path = temp_dir / "null_labels.csv"
    save_null_labels(nulls, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert 'clip_id' in rows[0]
    assert 'reason' in rows[0]
    assert 'confidence_score' in rows[0]

def test_save_final_labels(temp_dir, sample_raw_csv):
    """Test saving final labels to CSV."""
    records = load_raw_labels(sample_raw_csv)
    valid, _ = process_labels_and_exclusions(records)
    
    output_path = temp_dir / "labels.csv"
    save_final_labels(valid, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert 'clip_id' in rows[0]
    assert 'label' in rows[0]
    assert 'confidence_score' in rows[0]

def test_save_excluded_log_empty(temp_dir):
    """Test creating empty excluded log when no samples are excluded."""
    output_path = temp_dir / "excluded_samples.log"
    save_excluded_log([], output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size == 0

def test_save_excluded_log_with_data(temp_dir, sample_raw_csv):
    """Test creating excluded log with data."""
    records = load_raw_labels(sample_raw_csv)
    _, nulls = process_labels_and_exclusions(records)
    
    output_path = temp_dir / "excluded_samples.log"
    save_excluded_log(nulls, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 3

def test_missing_raw_file(temp_dir):
    """Test error handling when raw labels file is missing."""
    missing_path = temp_dir / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        load_raw_labels(missing_path)