"""
Contract test for metrics_longitudinal.csv schema.
Task: T025
"""
import csv
import json
import os
import pytest
from pathlib import Path

# Schema definition matching code/02_metric_extraction.py
EXPECTED_SCHEMA = {
    "pair_id": str,
    "repo_id": str,
    "block_id": str,
    "label": str,
    "churn_lines_added": int,
    "churn_lines_deleted": int,
    "churn_total_changes": int,
    "latency_days_to_fix": (int, type(None)),  # Optional[int]
    "num_commits": int,
    "window_start": str,
    "window_end": str,
    "extraction_timestamp": str
}

REQUIRED_FIELDS = list(EXPECTED_SCHEMA.keys())

def test_metrics_longitudinal_schema_exists():
    """Test that the output file exists."""
    output_path = Path("data/processed/metrics_longitudinal.csv")
    assert output_path.exists(), f"Output file {output_path} does not exist."

def test_metrics_longitudinal_has_correct_headers():
    """Test that the CSV has the correct headers."""
    output_path = Path("data/processed/metrics_longitudinal.csv")
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        assert set(headers) == set(REQUIRED_FIELDS), \
            f"Headers mismatch. Expected: {REQUIRED_FIELDS}, Got: {headers}"

def test_metrics_longitudinal_data_types():
    """Test that data types in the CSV match the schema."""
    output_path = Path("data/processed/metrics_longitudinal.csv")
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            for field, expected_type in EXPECTED_SCHEMA.items():
                value = row[field]
                
                if expected_type == (int, type(None)):
                    # Optional int
                    if value != '':
                        try:
                            int(value)
                        except ValueError:
                            pytest.fail(f"Row {i}, Field {field}: Expected int or None, got '{value}'")
                    # Empty string is treated as None
                else:
                    if expected_type == str:
                        assert isinstance(value, str), f"Row {i}, Field {field}: Expected str, got {type(value)}"
                    elif expected_type == int:
                        try:
                            int(value)
                        except ValueError:
                            pytest.fail(f"Row {i}, Field {field}: Expected int, got '{value}'")

def test_metrics_longitudinal_no_duplicates():
    """Test that pair_ids are unique."""
    output_path = Path("data/processed/metrics_longitudinal.csv")
    pair_ids = []
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row['pair_id']
            assert pid not in pair_ids, f"Duplicate pair_id found: {pid}"
            pair_ids.append(pid)

def test_metrics_longitudinal_valid_labels():
    """Test that labels are either 'LLM' or 'Human'."""
    output_path = Path("data/processed/metrics_longitudinal.csv")
    valid_labels = {'LLM', 'Human'}
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            assert row['label'] in valid_labels, \
                f"Row {i}: Invalid label '{row['label']}'. Expected 'LLM' or 'Human'."
