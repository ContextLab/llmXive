import os
import csv
import json
import tempfile
import pytest
from pathlib import Path

# Mock the dependencies to avoid needing full data pipeline setup for unit test
# We will test the save_metrics_to_csv function directly with mock data
import sys
from unittest.mock import patch, MagicMock

# Add project root to path if not already
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.save_metrics import save_metrics_to_csv

def test_save_metrics_csv_structure(tmp_path):
    """Test that save_metrics_to_csv creates a file with correct headers and data."""
    output_file = tmp_path / "test_metrics.csv"
    
    mock_metrics = [
        {
            'pr_id': 1,
            'source_type': 'llm',
            'comment_count': 5,
            'time_to_merge_minutes': 120.5,
            'review_cycles': 2,
            'complexity_score': 15.0
        },
        {
            'pr_id': 2,
            'source_type': 'human',
            'comment_count': 3,
            'time_to_merge_minutes': 45.0,
            'review_cycles': 1,
            'complexity_score': 8.5
        }
    ]
    
    save_metrics_to_csv(mock_metrics, str(output_file))
    
    assert output_file.exists(), "Output CSV file was not created"
    
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
        
        # Check headers
        expected_headers = ['pr_id', 'source_type', 'comment_count', 'time_to_merge_minutes', 'review_cycles', 'complexity_score']
        assert reader.fieldnames == expected_headers, f"Headers mismatch: {reader.fieldnames}"
        
        # Check data integrity
        assert rows[0]['pr_id'] == '1'
        assert rows[0]['source_type'] == 'llm'
        assert rows[0]['comment_count'] == '5'
        assert rows[0]['time_to_merge_minutes'] == '120.5'
        assert rows[0]['review_cycles'] == '2'
        assert rows[0]['complexity_score'] == '15.0'

def test_save_metrics_empty_list(tmp_path):
    """Test that save_metrics_to_csv creates an empty file with headers if input is empty."""
    output_file = tmp_path / "empty_metrics.csv"
    
    save_metrics_to_csv([], str(output_file))
    
    assert output_file.exists(), "Output CSV file was not created"
    
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 0, "Expected 0 rows"
        
        # Check headers exist even for empty file
        expected_headers = ['pr_id', 'source_type', 'comment_count', 'time_to_merge_minutes', 'review_cycles', 'complexity_score']
        assert reader.fieldnames == expected_headers, f"Headers mismatch: {reader.fieldnames}"

def test_save_metrics_missing_keys(tmp_path):
    """Test that save_metrics_to_csv handles missing keys by filling with None."""
    output_file = tmp_path / "partial_metrics.csv"
    
    mock_metrics = [
        {
            'pr_id': 1,
            'source_type': 'llm'
            # Missing other keys
        }
    ]
    
    save_metrics_to_csv(mock_metrics, str(output_file))
    
    assert output_file.exists(), "Output CSV file was not created"
    
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['comment_count'] == '' # None becomes empty string in CSV
        assert rows[0]['complexity_score'] == ''
