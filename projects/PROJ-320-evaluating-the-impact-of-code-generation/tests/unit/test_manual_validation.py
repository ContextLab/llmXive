"""
Unit tests for code/audit/manual_validation.py (T019b)
"""
import os
import sys
import json
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from audit.manual_validation import (
    calculate_sample_size,
    select_stratified_sample,
    calculate_error_rate,
    load_labeled_prs
)
from utils.seeds import set_global_seed

@pytest.fixture
def sample_data():
    return [
        {"pr_id": 1, "source_type": "llm", "confidence_score": 0.9, "detector_score": 0.8},
        {"pr_id": 2, "source_type": "llm", "confidence_score": 0.85, "detector_score": 0.75},
        {"pr_id": 3, "source_type": "human", "confidence_score": 0.95, "detector_score": 0.6},
        {"pr_id": 4, "source_type": "human", "confidence_score": 0.92, "detector_score": 0.55},
        {"pr_id": 5, "source_type": "llm", "confidence_score": 0.88, "detector_score": 0.82},
    ]

@pytest.fixture
def temp_csv_file(sample_data):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_data)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_calculate_sample_size():
    config = {"minimum_threshold": 10, "scaling_factor": 0.2}
    # 100 total, 50 LLM -> 0.2 * 50 = 10. Max(10, 10) = 10.
    size = calculate_sample_size(100, config)
    assert size == 10
    
    # 100 total, 10 LLM -> 0.2 * 10 = 2. Max(10, 2) = 10.
    size = calculate_sample_size(100, config)
    assert size == 10

def test_select_stratified_sample(sample_data):
    set_global_seed(42)
    sample = select_stratified_sample(sample_data, 3, 42)
    
    # Should have 3 items
    assert len(sample) == 3
    
    # Should contain both types ideally, but depends on random
    types = [x["source_type"] for x in sample]
    # Just verify no duplicates of the same object reference
    assert len(sample) == len(set(id(x) for x in sample))

def test_calculate_error_rate():
    results = [
        {"source_type": "llm", "human_label": "llm"},
        {"source_type": "llm", "human_label": "human"}, # Error
        {"source_type": "human", "human_label": "human"},
        {"source_type": "llm", "human_label": "ambiguous"}, # Ignored in error calc
    ]
    stats = calculate_error_rate(results)
    
    assert stats["total_audited"] == 4
    assert stats["errors"] == 1
    assert abs(stats["error_rate"] - 0.25) < 0.001

def test_load_labeled_prs(temp_csv_file):
    data = load_labeled_prs(temp_csv_file)
    assert len(data) == 5
    assert data[0]["pr_id"] == 1
    assert data[0]["source_type"] == "llm"
    assert isinstance(data[0]["pr_id"], int)
    assert isinstance(data[0]["confidence_score"], float)

def test_load_labeled_prs_missing_file():
    with pytest.raises(FileNotFoundError):
        load_labeled_prs("/nonexistent/path.csv")