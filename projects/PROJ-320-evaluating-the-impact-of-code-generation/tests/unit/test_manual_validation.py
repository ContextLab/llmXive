import pytest
import os
import json
import tempfile
import csv
from pathlib import Path

from audit.manual_validation import (
    calculate_sample_size,
    select_stratified_sample,
    execute_human_judgment_checklist,
    calculate_error_rate,
    load_labeled_prs,
    run_manual_validation
)

@pytest.fixture
def sample_prs():
    """Create a sample list of PRs for testing."""
    return [
        {"pr_id": 1, "source_type": "llm", "confidence_score": 0.9, "detector_score": 0.8, "flagged": False},
        {"pr_id": 2, "source_type": "llm", "confidence_score": 0.85, "detector_score": 0.75, "flagged": False},
        {"pr_id": 3, "source_type": "human", "confidence_score": 0.95, "detector_score": 0.1, "flagged": False},
        {"pr_id": 4, "source_type": "llm", "confidence_score": 0.7, "detector_score": 0.6, "flagged": False},
        {"pr_id": 5, "source_type": "human", "confidence_score": 0.8, "detector_score": 0.2, "flagged": False},
        {"pr_id": 6, "source_type": "llm", "confidence_score": 0.55, "detector_score": 0.4, "flagged": True},
    ]

def test_calculate_sample_size_min_threshold():
    """Test that sample size is at least the minimum threshold."""
    # With 5 LLMs, 10% would be 0.5 -> ceil(0.5) = 1, but min is 10
    n_llm = 5
    size = calculate_sample_size(n_llm)
    assert size == 10  # MIN_THRESHOLD

def test_calculate_sample_size_proportion():
    """Test that sample size uses proportion when it exceeds minimum."""
    # With 200 LLMs, 10% would be 20, which is > 10
    n_llm = 200
    size = calculate_sample_size(n_llm)
    assert size == 20

def test_select_stratified_sample():
    """Test stratified sampling logic."""
    prs = [
        {"pr_id": 1, "source_type": "llm", "confidence_score": 0.9},
        {"pr_id": 2, "source_type": "llm", "confidence_score": 0.95},
        {"pr_id": 3, "source_type": "llm", "confidence_score": 0.65},
        {"pr_id": 4, "source_type": "llm", "confidence_score": 0.5},
    ]
    sample = select_stratified_sample(prs, n_llm=4, sample_size=2, seed=42)
    assert len(sample) == 2
    assert all(p["source_type"] == "llm" for p in sample)

def test_execute_human_judgment_checklist_writes_file():
    """Test that checklist execution writes results to JSON."""
    sample = [
        {"pr_id": 1, "source_type": "llm", "confidence_score": 0.9, "detector_score": 0.8},
    ]
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        output_path = f.name
    
    try:
        results = execute_human_judgment_checklist(sample, output_path)
        assert len(results) == 1
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 1
            assert "pr_id" in data[0]
            assert "human_verified_label" in data[0]
    finally:
        os.unlink(output_path)

def test_calculate_error_rate():
    """Test error rate calculation."""
    results = [
        {"is_correct": True},
        {"is_correct": True},
        {"is_correct": False},
    ]
    rate = calculate_error_rate(results)
    assert rate == 1/3

def test_calculate_error_rate_empty():
    """Test error rate with empty list."""
    rate = calculate_error_rate([])
    assert rate == 0.0

def test_load_labeled_prs(tmp_path):
    """Test loading labeled PRs from CSV."""
    csv_path = tmp_path / "prs_labeled.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["pr_id", "source_type", "confidence_score", "flagged", "detector_score"])
        writer.writerow([1, "llm", "0.9", "False", "0.8"])
        writer.writerow([2, "human", "0.95", "False", "0.1"])
    
    prs = load_labeled_prs(str(csv_path))
    assert len(prs) == 2
    assert prs[0]["pr_id"] == 1
    assert prs[0]["source_type"] == "llm"
    assert prs[0]["confidence_score"] == 0.9
    assert prs[0]["flagged"] == False

def test_run_manual_validation_success(tmp_path):
    """Test full pipeline with low error rate."""
    # Create input CSV
    csv_path = tmp_path / "prs_labeled.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["pr_id", "source_type", "confidence_score", "flagged", "detector_score"])
        for i in range(100):
            writer.writerow([i, "llm", "0.9", "False", "0.8"])
    
    audit_path = tmp_path / "audit_results.json"
    error_path = tmp_path / "error_rate.json"
    
    # This should pass without raising an error
    run_manual_validation(
        input_path=str(csv_path),
        audit_output_path=str(audit_path),
        error_rate_output_path=str(error_path),
        seed=42
    )
    
    assert os.path.exists(audit_path)
    assert os.path.exists(error_path)
    
    with open(error_path, 'r') as f:
        data = json.load(f)
        assert data["status"] == "pass"