"""
Unit tests for reproducibility verification functionality.

Tests for code/utils/reproducibility_checker.py
"""

import os
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from utils.artifact_checksums import compute_file_hash
from utils.reproducibility_checker import (
    load_previous_checksums,
    compute_current_checksums,
    compare_checksums,
    save_reproducibility_report,
    verify_reproducibility
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_artifacts(temp_dir):
    """Create sample artifact files for testing."""
    # Create data/processed directory
    processed_dir = temp_dir / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Create sample files
    files = {}
    for i in range(3):
        file_path = processed_dir / f"sample_{i}.csv"
        content = f"id,value\n{i},{i*10}\n"
        file_path.write_text(content)
        files[str(file_path.relative_to(temp_dir))] = content
    
    # Create state directory
    state_dir = temp_dir / "state"
    state_dir.mkdir(parents=True)
    state_file = state_dir / "test_state.yaml"
    state_file.write_text("key: value\n")
    files[str(state_file.relative_to(temp_dir))] = "key: value\n"
    
    return temp_dir, files

def test_load_previous_checksums_missing_file(temp_dir):
    """Test loading checksums from a non-existent file."""
    non_existent_file = temp_dir / "non_existent.yaml"
    result = load_previous_checksums(non_existent_file)
    assert result is None

def test_load_previous_checksums_success(temp_dir):
    """Test loading checksums from an existing file."""
    state_file = temp_dir / "state.yaml"
    test_data = {
        "checksums": {
            "file1.csv": "abc123",
            "file2.csv": "def456"
        }
    }
    
    with open(state_file, 'w') as f:
        yaml.dump(test_data, f)
    
    result = load_previous_checksums(state_file)
    assert result is not None
    assert "checksums" in result
    assert result["checksums"]["file1.csv"] == "abc123"

def test_compute_current_checksums(temp_dir, sample_artifacts):
    """Test computing checksums for current artifacts."""
    _, files = sample_artifacts
    
    checksums = compute_current_checksums(["data/processed", "state"], temp_dir)
    
    assert len(checksums) == len(files)
    for rel_path, content in files.items():
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        assert rel_path in checksums
        assert checksums[rel_path] == expected_hash

def test_compute_current_checksums_empty_dir(temp_dir):
    """Test computing checksums when directory is empty."""
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()
    
    checksums = compute_current_checksums(["empty"], temp_dir)
    assert checksums == {}

def test_compare_checksums_perfect_match():
    """Test comparison when all checksums match."""
    previous = {"file1.csv": "abc", "file2.csv": "def"}
    current = {"file1.csv": "abc", "file2.csv": "def"}
    
    results = compare_checksums(previous, current)
    
    assert len(results["matched"]) == 2
    assert len(results["mismatched"]) == 0
    assert len(results["new"]) == 0
    assert len(results["missing"]) == 0
    assert results["match_rate"] == 1.0

def test_compare_checksums_mismatches():
    """Test comparison when some checksums differ."""
    previous = {"file1.csv": "abc", "file2.csv": "def"}
    current = {"file1.csv": "xyz", "file2.csv": "def"}
    
    results = compare_checksums(previous, current)
    
    assert len(results["matched"]) == 1
    assert len(results["mismatched"]) == 1
    assert results["mismatched"][0]["path"] == "file1.csv"
    assert results["match_rate"] == 0.5

def test_compare_checksums_new_files():
    """Test comparison with new files."""
    previous = {"file1.csv": "abc"}
    current = {"file1.csv": "abc", "file2.csv": "def"}
    
    results = compare_checksums(previous, current)
    
    assert len(results["new"]) == 1
    assert "file2.csv" in results["new"]
    assert results["match_rate"] == 0.5

def test_compare_checksums_missing_files():
    """Test comparison with missing files."""
    previous = {"file1.csv": "abc", "file2.csv": "def"}
    current = {"file1.csv": "abc"}
    
    results = compare_checksums(previous, current)
    
    assert len(results["missing"]) == 1
    assert "file2.csv" in results["missing"]
    assert results["match_rate"] == 0.5

def test_save_reproducibility_report(temp_dir):
    """Test saving reproducibility report to file."""
    previous = {"file1.csv": "abc"}
    current = {"file1.csv": "abc"}
    
    results = compare_checksums(previous, current)
    
    report_file = temp_dir / "reproducibility_report.yaml"
    report = save_reproducibility_report(
        results, previous, current, report_file, temp_dir
    )
    
    assert report_file.exists()
    assert report["verification_status"] == "passed"
    assert report["summary"]["match_rate"] == 1.0
    
    # Verify file contents
    with open(report_file, 'r') as f:
        saved_report = yaml.safe_load(f)
    
    assert saved_report["verification_status"] == "passed"

def test_save_reproducibility_report_failure(temp_dir):
    """Test saving reproducibility report when there are mismatches."""
    previous = {"file1.csv": "abc"}
    current = {"file1.csv": "xyz"}
    
    results = compare_checksums(previous, current)
    
    report_file = temp_dir / "reproducibility_report.yaml"
    report = save_reproducibility_report(
        results, previous, current, report_file, temp_dir
    )
    
    assert report_file.exists()
    assert report["verification_status"] == "failed"
    assert report["summary"]["match_rate"] == 0.0

@patch('utils.reproducibility_checker.re_run_pipeline_components')
@patch('utils.reproducibility_checker.load_previous_checksums')
@patch('utils.reproducibility_checker.compute_current_checksums')
def test_verify_reproducibility_success(
    mock_compute, mock_load, mock_rerun, temp_dir, sample_artifacts
):
    """Test successful reproducibility verification."""
    _, files = sample_artifacts
    
    # Mock previous checksums
    mock_load.return_value = {
        "checksums": {k: hashlib.sha256(v.encode()).hexdigest() for k, v in files.items()}
    }
    
    # Mock current checksums (same as previous)
    mock_compute.return_value = {
        k: hashlib.sha256(v.encode()).hexdigest() for k, v in files.items()
    }
    
    # Mock pipeline rerun
    mock_rerun.return_value = True
    
    # Temporarily change working directory
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        result = verify_reproducibility(temp_dir)
        
        assert result["verification_status"] == "passed"
        assert result["summary"]["match_rate"] == 1.0
    finally:
        os.chdir(original_cwd)

@patch('utils.reproducibility_checker.re_run_pipeline_components')
@patch('utils.reproducibility_checker.load_previous_checksums')
def test_verify_reproducibility_pipeline_failure(mock_load, mock_rerun, temp_dir):
    """Test reproducibility verification when pipeline rerun fails."""
    mock_load.return_value = {"checksums": {"file.csv": "abc"}}
    mock_rerun.return_value = False
    
    result = verify_reproducibility(temp_dir)
    
    assert result["status"] == "failed"
    assert "Pipeline re-execution failed" in result["reason"]

@patch('utils.reproducibility_checker.load_previous_checksums')
def test_verify_reproducibility_no_previous(mock_load, temp_dir):
    """Test reproducibility verification when no previous checksums exist."""
    mock_load.return_value = None
    
    result = verify_reproducibility(temp_dir)
    
    assert result["status"] == "failed"
    assert "No previous checksums found" in result["reason"]

def test_compute_file_hash_consistency(temp_dir):
    """Test that file hash computation is consistent."""
    file_path = temp_dir / "test.txt"
    content = "test content for hashing"
    file_path.write_text(content)
    
    hash1 = compute_file_hash(file_path)
    hash2 = compute_file_hash(file_path)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex digest

def test_compute_file_hash_content_change(temp_dir):
    """Test that file hash changes when content changes."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("content 1")
    hash1 = compute_file_hash(file_path)
    
    file_path.write_text("content 2")
    hash2 = compute_file_hash(file_path)
    
    assert hash1 != hash2
