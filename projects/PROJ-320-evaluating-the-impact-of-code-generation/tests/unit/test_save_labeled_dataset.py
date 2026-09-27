"""
Unit tests for T017: save_labeled_dataset.py
"""
import os
import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from data.save_labeled_dataset import (
    load_classified_prs,
    save_labeled_dataset,
    run_save_labeled_dataset,
    main
)

@pytest.fixture
def temp_data_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        processed_dir = Path(tmpdir) / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        yield raw_dir, processed_dir

@pytest.fixture
def sample_prs():
    """Sample PR data for testing."""
    return [
        {
            "pr_id": "test_repo_1",
            "source_type": "llm",
            "confidence_score": 0.95,
            "flagged": False,
            "detector_score": 0.88,
            "repo": "test_repo",
            "pr_number": 1,
            "author": "copilot-bot",
            "merged_at": "2023-01-01T00:00:00Z",
            "created_at": "2023-01-01T00:00:00Z"
        },
        {
            "pr_id": "test_repo_2",
            "source_type": "human",
            "confidence_score": 0.45,
            "flagged": True,
            "detector_score": 0.30,
            "repo": "test_repo",
            "pr_number": 2,
            "author": "human-dev",
            "merged_at": "2023-01-02T00:00:00Z",
            "created_at": "2023-01-02T00:00:00Z"
        }
    ]

def test_load_classified_prs_empty_directory(temp_data_dirs):
    """Test loading from an empty directory."""
    raw_dir, _ = temp_data_dirs
    prs = load_classified_prs(raw_dir)
    assert prs == []

def test_save_labeled_dataset_creates_file(temp_data_dirs, sample_prs):
    """Test that save_labeled_dataset creates the CSV file with correct content."""
    _, output_dir = temp_data_dirs
    output_path = output_dir / "prs_labeled.csv"
    
    save_labeled_dataset(sample_prs, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    
    # Check headers
    expected_headers = [
        "pr_id", "source_type", "confidence_score", "flagged", "detector_score",
        "repo", "pr_number", "author", "merged_at", "created_at"
    ]
    assert reader.fieldnames == expected_headers

def test_save_labeled_dataset_formats_boolean_correctly(temp_data_dirs, sample_prs):
    """Test that boolean flagged values are written as lowercase strings."""
    _, output_dir = temp_data_dirs
    output_path = output_dir / "prs_labeled.csv"
    
    save_labeled_dataset(sample_prs, output_path)
    
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # First row should be False, second True
    assert rows[0]["flagged"] == "false"
    assert rows[1]["flagged"] == "true"

def test_save_labeled_dataset_handles_missing_fields(temp_data_dirs):
    """Test that missing fields are handled with defaults."""
    _, output_dir = temp_data_dirs
    output_path = output_dir / "prs_labeled.csv"
    
    incomplete_prs = [
        {
            "repo": "test_repo",
            "pr_number": 1
            # Missing other fields
        }
    ]
    
    save_labeled_dataset(incomplete_prs, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]["pr_id"] == "test_repo_1"
    assert rows[0]["source_type"] == "unknown"
    assert float(rows[0]["confidence_score"]) == 0.0
    assert rows[0]["flagged"] == "false"
    assert float(rows[0]["detector_score"]) == 0.0

@patch('data.save_labeled_dataset.load_prs_from_raw')
@patch('data.save_labeled_dataset.get_logger')
def test_run_save_labeled_dataset_integration(mock_logger, mock_load, temp_data_dirs, sample_prs):
    """Integration test for the full run_save_labeled_dataset flow."""
    raw_dir, output_dir = temp_data_dirs
    
    # Mock the logger
    mock_logger_instance = MagicMock()
    mock_logger.return_value = mock_logger_instance
    
    # Mock the data loading
    mock_load.return_value = sample_prs
    
    success = run_save_labeled_dataset(raw_data_dir=raw_dir, output_dir=output_dir)
    
    assert success is True
    assert (output_dir / "prs_labeled.csv").exists()
    mock_load.assert_called_once_with(raw_dir)

def test_main_exits_on_failure(temp_data_dirs):
    """Test that main exits with code 1 on failure."""
    raw_dir, output_dir = temp_data_dirs
    
    # Ensure raw directory is empty so load returns []
    with patch('data.save_labeled_dataset.run_save_labeled_dataset', return_value=False):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
