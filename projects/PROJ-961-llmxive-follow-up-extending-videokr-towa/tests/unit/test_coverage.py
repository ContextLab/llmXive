"""
Unit tests for calculate_annotation_coverage.py
"""
import json
import tempfile
from pathlib import Path
import csv
import pytest

# Add code root to path if not already present
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingest.calculate_annotation_coverage import calculate_coverage, load_annotated_data


def test_coverage_all_resolved():
    """Test when all records have valid chain_length."""
    records = [
        {"id": "1", "question": "Q1", "chain_length": "1"},
        {"id": "2", "question": "Q2", "chain_length": "2"},
        {"id": "3", "question": "Q3", "chain_length": "3+"}
    ]
    result = calculate_coverage(records)
    assert result["total_input_records"] == 3
    assert result["unresolvable_count"] == 0
    assert result["resolved_count"] == 3
    assert result["proportion"] == 1.0


def test_coverage_all_unresolvable():
    """Test when all records are unresolvable."""
    records = [
        {"id": "1", "question": "Q1", "chain_length": None},
        {"id": "2", "question": "Q2", "chain_length": "unresolvable"},
        {"id": "3", "question": "Q3", "chain_length": ""}
    ]
    result = calculate_coverage(records)
    assert result["total_input_records"] == 3
    assert result["unresolvable_count"] == 3
    assert result["resolved_count"] == 0
    assert result["proportion"] == 0.0


def test_coverage_mixed():
    """Test with a mix of resolved and unresolvable records."""
    records = [
        {"id": "1", "question": "Q1", "chain_length": "1"},
        {"id": "2", "question": "Q2", "chain_length": "unresolvable"},
        {"id": "3", "question": "Q3", "chain_length": "2"},
        {"id": "4", "question": "Q4", "chain_length": None},
        {"id": "5", "question": "Q5", "chain_length": "4"}
    ]
    result = calculate_coverage(records)
    assert result["total_input_records"] == 5
    assert result["unresolvable_count"] == 2
    assert result["resolved_count"] == 3
    assert result["proportion"] == 0.6


def test_coverage_invalid_string():
    """Test that invalid string values in chain_length are counted as unresolvable."""
    records = [
        {"id": "1", "question": "Q1", "chain_length": "invalid"},
        {"id": "2", "question": "Q2", "chain_length": "1"}
    ]
    result = calculate_coverage(records)
    assert result["unresolvable_count"] == 1
    assert result["proportion"] == 0.5


def test_empty_records_raises():
    """Test that empty list raises ValueError."""
    with pytest.raises(ValueError):
        calculate_coverage([])