"""
Unit tests for T017: save_labeled_dataset.py

Tests verify that the script correctly loads classified PRs and saves them
to the expected CSV format with all required columns.
"""
import os
import csv
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from data.save_labeled_dataset import (
    load_classified_prs,
    save_labeled_dataset,
    run_save_labeled_dataset
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        raw_dir = Path(tmp_dir) / "raw"
        processed_dir = Path(tmp_dir) / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        yield raw_dir, processed_dir

@pytest.fixture
def sample_pr_data():
    """Create sample PR data for testing."""
    return [
        {
            "pr_id": "psf/requests_123",
            "source_type": "llm",
            "confidence_score": 0.95,
            "flagged": False,
            "detector_score": 0.88,
            "repo": "psf/requests",
            "pr_number": 123,
            "author": "copilot-bot",
            "merged_at": "2023-10-01T12:00:00Z",
            "created_at": "2023-09-30T10:00:00Z"
        },
        {
            "pr_id": "microsoft/vscode_456",
            "source_type": "human",
            "confidence_score": 0.45,
            "flagged": True,
            "detector_score": 0.30,
            "repo": "microsoft/vscode",
            "pr_number": 456,
            "author": "human-user",
            "merged_at": "2023-10-02T14:30:00Z",
            "created_at": "2023-10-01T09:15:00Z"
        }
    ]

def test_save_labeled_dataset_creates_file(temp_dirs, sample_pr_data):
    """Test that save_labeled_dataset creates the output CSV file."""
    raw_dir, processed_dir = temp_dirs
    output_path = processed_dir / "prs_labeled.csv"
    
    save_labeled_dataset(sample_pr_data, output_path)
    
    assert output_path.exists(), "Output CSV file was not created"
    assert output_path.stat().st_size > 0, "Output CSV file is empty"

def test_save_labeled_dataset_has_correct_columns(temp_dirs, sample_pr_data):
    """Test that the output CSV has all required columns."""
    raw_dir, processed_dir = temp_dirs
    output_path = processed_dir / "prs_labeled.csv"
    
    save_labeled_dataset(sample_pr_data, output_path)
    
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
    
    required_columns = [
        "pr_id", "source_type", "confidence_score", "flagged", "detector_score",
        "repo", "pr_number", "author", "merged_at", "created_at"
    ]
    
    for col in required_columns:
        assert col in fieldnames, f"Missing required column: {col}"

def test_save_labeled_dataset_content(temp_dirs, sample_pr_data):
    """Test that the output CSV contains the correct data."""
    raw_dir, processed_dir = temp_dirs
    output_path = processed_dir / "prs_labeled.csv"
    
    save_labeled_dataset(sample_pr_data, output_path)
    
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == len(sample_pr_data), "Row count mismatch"
    
    # Check first row (LLM)
    assert rows[0]["source_type"] == "llm"
    assert rows[0]["confidence_score"] == "0.95"
    assert rows[0]["flagged"] == "false"
    assert rows[0]["detector_score"] == "0.88"
    
    # Check second row (Human, flagged)
    assert rows[1]["source_type"] == "human"
    assert rows[1]["confidence_score"] == "0.45"
    assert rows[1]["flagged"] == "true"
    assert rows[1]["detector_score"] == "0.30"

def test_save_labeled_dataset_empty_list(temp_dirs):
    """Test handling of empty PR list."""
    raw_dir, processed_dir = temp_dirs
    output_path = processed_dir / "prs_labeled.csv"
    
    save_labeled_dataset([], output_path)
    
    assert output_path.exists()
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 0, "Empty list should result in header-only CSV"

def test_run_save_labeled_dataset_integration(temp_dirs, sample_pr_data):
    """Test the full run_save_labeled_dataset function with mocked data."""
    raw_dir, processed_dir = temp_dirs
    
    # Create a mock raw JSON file
    mock_file = raw_dir / "prs_repo1.json"
    with open(mock_file, 'w') as f:
        json.dump(sample_pr_data, f)
    
    # Mock load_prs_from_raw to return our sample data
    with patch('data.save_labeled_dataset.load_prs_from_raw') as mock_load:
        mock_load.return_value = sample_pr_data
        
        success = run_save_labeled_dataset(raw_dir, processed_dir)
        
        assert success is True
        assert (processed_dir / "prs_labeled.csv").exists()

def test_flagged_conversion_to_string(temp_dirs, sample_pr_data):
    """Test that boolean flagged values are converted to lowercase strings."""
    raw_dir, processed_dir = temp_dirs
    output_path = processed_dir / "prs_labeled.csv"
    
    save_labeled_dataset(sample_pr_data, output_path)
    
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Check that flagged is a string "true" or "false"
    assert rows[0]["flagged"] in ["true", "false"]
    assert rows[1]["flagged"] in ["true", "false"]