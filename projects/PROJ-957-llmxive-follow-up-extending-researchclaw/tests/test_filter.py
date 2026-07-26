"""
Unit tests for src/data/filter.py
"""

import json
import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.filter import (
    filter_by_failure_mode,
    analyze_failure_modes,
    write_failure_mode_audit,
    write_subset_json,
    main
)


@pytest.fixture
def sample_dataset():
    """Create a mock dataset with various failure modes."""
    return [
        {
            "id": "task_001",
            "metadata": {"failure_mode": "experimental protocol mismatch", "other": "data1"}
        },
        {
            "id": "task_002",
            "metadata": {"failure_mode": "experimental protocol mismatch", "other": "data2"}
        },
        {
            "id": "task_003",
            "metadata": {"failure_mode": "instrument calibration error", "other": "data3"}
        },
        {
            "id": "task_004",
            "metadata": {"failure_mode": "experimental protocol mismatch", "other": "data4"}
        },
        {
            "id": "task_005",
            "metadata": {"failure_mode": "sample contamination", "other": "data5"}
        },
    ]


@pytest.fixture
def sample_dataset_missing_key():
    """Create a mock dataset with missing failure_mode key."""
    return [
        {
            "id": "task_001",
            "metadata": {"other": "data1"}  # Missing failure_mode
        },
    ]


@pytest.fixture
def sample_dataset_no_metadata():
    """Create a mock dataset without metadata key."""
    return [
        {
            "id": "task_001",
            "description": "No metadata here"
        },
    ]


def test_filter_by_failure_mode_exact_match(sample_dataset):
    """Test filtering for exact failure mode match."""
    filtered = filter_by_failure_mode(sample_dataset, "experimental protocol mismatch")
    assert len(filtered) == 3
    for task in filtered:
        assert task['metadata']['failure_mode'] == "experimental protocol mismatch"


def test_filter_by_failure_mode_no_match(sample_dataset):
    """Test filtering when no items match."""
    filtered = filter_by_failure_mode(sample_dataset, "nonexistent mode")
    assert len(filtered) == 0


def test_filter_by_failure_mode_missing_key_raises(sample_dataset_missing_key):
    """Test that missing failure_mode key raises KeyError (FR-006)."""
    with pytest.raises(KeyError, match="FR-006"):
        filter_by_failure_mode(sample_dataset_missing_key, "experimental protocol mismatch")


def test_filter_by_failure_mode_no_metadata_skips(sample_dataset_no_metadata):
    """Test that items without metadata are skipped with a warning."""
    # This should not raise, just skip the item
    filtered = filter_by_failure_mode(sample_dataset_no_metadata, "experimental protocol mismatch")
    assert len(filtered) == 0


def test_analyze_failure_modes(sample_dataset):
    """Test analysis of failure mode distribution."""
    counts = analyze_failure_modes(sample_dataset)
    assert len(counts) == 3
    assert counts["experimental protocol mismatch"] == 3
    assert counts["instrument calibration error"] == 1
    assert counts["sample contamination"] == 1


def test_analyze_failure_modes_empty():
    """Test analysis on empty dataset."""
    counts = analyze_failure_modes([])
    assert len(counts) == 0


def test_write_failure_mode_audit(tmp_path):
    """Test writing failure mode audit CSV."""
    mode_counts = {
        "experimental protocol mismatch": 10,
        "instrument calibration error": 5
    }
    output_path = tmp_path / "audit.csv"
    
    write_failure_mode_audit(mode_counts, 15, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['dominant_mode'] == "experimental protocol mismatch"
        assert rows[0]['count'] == "10"
        assert rows[0]['total_tasks'] == "15"


def test_write_subset_json(tmp_path):
    """Test writing subset to JSON and computing checksum."""
    tasks = [
        {"id": "task_001", "metadata": {"failure_mode": "test"}},
        {"id": "task_002", "metadata": {"failure_mode": "test"}}
    ]
    output_path = tmp_path / "subset.json"
    
    checksum = write_subset_json(tasks, output_path)
    
    assert output_path.exists()
    assert len(checksum) == 64  # SHA256 hex length
    
    with open(output_path, 'r', encoding='utf-8') as f:
        loaded = json.load(f)
        assert len(loaded) == 2
        assert loaded[0]['id'] == "task_001"


@patch('src.data.filter.load_researchclawbench_data')
@patch('src.data.filter.filter_by_failure_mode')
@patch('src.data.filter.write_subset_json')
@patch('src.data.filter.write_checksum')
@patch('src.data.filter.Path')
def test_main_success_flow(mock_path, mock_write_checksum, mock_write_subset, mock_filter, mock_load):
    """Test the main function success flow."""
    # Mock dataset
    mock_dataset = MagicMock()
    mock_load.return_value = mock_dataset
    
    # Mock filtered tasks
    mock_tasks = [{"id": "task_001"}]
    mock_filter.return_value = mock_tasks
    
    # Mock checksum
    mock_write_subset.return_value = "a" * 64
    
    # Mock Path to return a temp directory
    mock_temp_path = MagicMock()
    mock_temp_path.parent.mkdir = MagicMock()
    mock_path.return_value = mock_temp_path
    
    # Run main
    result = main()
    
    assert result == 0
    mock_load.assert_called_once()
    mock_filter.assert_called_once()
    mock_write_subset.assert_called_once()
