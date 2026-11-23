"""
Unit tests for code/labeling/separate_null_samples.py (Task T024).
"""
import os
import sys
import csv
import json
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from labeling.separate_null_samples import (
    load_raw_labels,
    process_labels_and_exclusions,
    save_null_labels,
    save_final_labels,
    save_excluded_log,
    main
)

# Fixture for temporary directory
@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

# Mock the global paths for testing
@pytest.fixture(autouse=True)
def patch_paths(temp_dir, monkeypatch):
    # We need to patch the module-level constants in the target module
    # Since we can't easily patch module-level constants in the imported module,
    # we will test the functions directly with mocked file operations or
    # by creating temporary files in the temp_dir and passing them as arguments.
    # However, the functions use global paths. To test properly, we will
    # create a wrapper or test the logic by creating the expected files in temp_dir
    # and then mocking the path constants if possible, or re-implementing the logic.
    
    # Alternative: Test the logic by creating temporary files and using the functions
    # but we need to override the global paths.
    # Since the functions use global paths defined at module level, we will
    # create a test that creates the necessary files in the temp_dir and then
    # monkeypatches the module's global variables.
    
    import labeling.separate_null_samples as module_to_patch
    original_raw_path = module_to_patch.RAW_LABELS_PATH
    original_null_path = module_to_patch.NULL_SAMPLES_PATH
    original_final_path = module_to_patch.FINAL_LABELS_PATH
    original_excluded_path = module_to_patch.EXCLUDED_LOG_PATH

    module_to_patch.RAW_LABELS_PATH = temp_dir / "raw_labels.csv"
    module_to_patch.NULL_SAMPLES_PATH = temp_dir / "null_samples.csv"
    module_to_patch.FINAL_LABELS_PATH = temp_dir / "labels.csv"
    module_to_patch.EXCLUDED_LOG_PATH = temp_dir / "excluded_samples.log"

    yield temp_dir

    # Restore original paths
    module_to_patch.RAW_LABELS_PATH = original_raw_path
    module_to_patch.NULL_SAMPLES_PATH = original_null_path
    module_to_patch.FINAL_LABELS_PATH = original_final_path
    module_to_patch.EXCLUDED_LOG_PATH = original_excluded_path

def test_load_raw_labels_file_not_found(patch_paths):
    """Test that FileNotFoundError is raised when raw_labels.csv is missing."""
    with pytest.raises(FileNotFoundError):
        load_raw_labels()

def test_load_raw_labels_missing_columns(patch_paths, temp_dir):
    """Test that ValueError is raised when required columns are missing."""
    raw_file = temp_dir / "raw_labels.csv"
    with open(raw_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['clip_id', 'label'])
        writer.writeheader()
        writer.writerow({'clip_id': '1', 'label': 'valid'})
    
    with pytest.raises(ValueError):
        load_raw_labels()

def test_process_labels_and_exclusions(patch_paths, temp_dir):
    """Test the separation logic."""
    raw_file = temp_dir / "raw_labels.csv"
    with open(raw_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['clip_id', 'label', 'confidence_score', 'reason'])
        writer.writeheader()
        writer.writerow({'clip_id': '1', 'label': 'valid', 'confidence_score': '0.95', 'reason': 'ok'})
        writer.writerow({'clip_id': '2', 'label': 'null', 'confidence_score': '0.4', 'reason': 'low_conf'})
        writer.writerow({'clip_id': '3', 'label': 'invalid', 'confidence_score': '0.9', 'reason': 'phys_fail'})
        writer.writerow({'clip_id': '4', 'label': 'NULL', 'confidence_score': '0.3', 'reason': 'low_conf'})  # Test case insensitivity

    rows = load_raw_labels()
    valid, nulls = process_labels_and_exclusions(rows)

    assert len(valid) == 2
    assert len(nulls) == 2
    
    # Check valid
    assert valid[0]['clip_id'] == '1'
    assert valid[1]['clip_id'] == '3'
    
    # Check nulls
    null_ids = [n['clip_id'] for n in nulls]
    assert '2' in null_ids
    assert '4' in null_ids

def test_save_null_labels(patch_paths, temp_dir):
    """Test saving null samples."""
    null_samples = [
        {'clip_id': '1', 'reason': 'low_conf', 'confidence_score': '0.4'},
        {'clip_id': '2', 'reason': 'fail', 'confidence_score': '0.1'}
    ]
    save_null_labels(null_samples)
    
    assert (temp_dir / "null_samples.csv").exists()
    with open(temp_dir / "null_samples.csv", 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['clip_id'] == '1'
        assert rows[1]['clip_id'] == '2'

def test_save_null_labels_empty(patch_paths, temp_dir):
    """Test saving empty null samples list."""
    save_null_labels([])
    assert (temp_dir / "null_samples.csv").exists()
    with open(temp_dir / "null_samples.csv", 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 0

def test_save_final_labels(patch_paths, temp_dir):
    """Test saving valid labels."""
    valid_labels = [
        {'clip_id': '1', 'label': 'valid', 'confidence_score': '0.9', 'reason': 'ok'},
        {'clip_id': '2', 'label': 'invalid', 'confidence_score': '0.9', 'reason': 'fail'}
    ]
    save_final_labels(valid_labels)
    
    assert (temp_dir / "labels.csv").exists()
    with open(temp_dir / "labels.csv", 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2

def test_save_excluded_log(patch_paths, temp_dir):
    """Test saving excluded log."""
    null_samples = [
        {'clip_id': '1', 'reason': 'low_conf', 'confidence_score': '0.4'}
    ]
    save_excluded_log(null_samples)
    
    assert (temp_dir / "excluded_samples.log").exists()
    with open(temp_dir / "excluded_samples.log", 'r') as f:
        content = f.read()
        assert "1|low_conf|0.4" in content

def test_save_excluded_log_empty(patch_paths, temp_dir):
    """Test saving empty excluded log."""
    save_excluded_log([])
    assert (temp_dir / "excluded_samples.log").exists()
    with open(temp_dir / "excluded_samples.log", 'r') as f:
        content = f.read()
        assert content == ""