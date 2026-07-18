"""
Unit tests for T013b: sampling module.
"""
import json
import os
import tempfile
import pytest
from collections import defaultdict

from sampling import (
    load_comparison_logs,
    filter_wasted_calls,
    stratify_by_query,
    select_stratified_sample,
    run_sampling_pipeline
)
from metrics import calculate_dynamic_sample_size

# Fixtures
@pytest.fixture
def sample_logs(tmp_path):
    """Create a temporary log file with sample comparison data."""
    logs = [
        {"query_id": "q1", "doc_id": "d1", "similarity": 0.98, "label": "relevant"},
        {"query_id": "q1", "doc_id": "d2", "similarity": 0.85, "label": "relevant"},
        {"query_id": "q2", "doc_id": "d3", "similarity": 0.99, "label": "irrelevant"},
        {"query_id": "q2", "doc_id": "d4", "similarity": 0.96, "label": "irrelevant"},
        {"query_id": "q3", "doc_id": "d5", "similarity": 0.92, "label": "relevant"},
        {"query_id": "q3", "doc_id": "d6", "similarity": 0.97, "label": "relevant"},
        {"query_id": "q3", "doc_id": "d7", "similarity": 0.98, "label": "relevant"},
    ]
    log_file = tmp_path / "comparisons.jsonl"
    with open(log_file, 'w') as f:
        for record in logs:
            f.write(json.dumps(record) + "\n")
    return str(log_file), logs

@pytest.fixture
def empty_logs(tmp_path):
    """Create an empty log file."""
    log_file = tmp_path / "empty.jsonl"
    log_file.write_text("")
    return str(log_file)

# Tests
def test_load_comparison_logs(sample_logs):
    path, expected = sample_logs
    result = load_comparison_logs(path)
    assert len(result) == len(expected)
    assert result[0]["query_id"] == "q1"
    assert result[0]["similarity"] == 0.98

def test_filter_wasted_calls(sample_logs):
    path, logs = sample_logs
    comparisons = load_comparison_logs(path)
    wasted = filter_wasted_calls(comparisons, threshold=0.95)
    # Expected: 0.98, 0.99, 0.96, 0.97, 0.98 -> 5 items
    assert len(wasted) == 5
    for w in wasted:
        assert w["similarity"] > 0.95

def test_filter_wasted_calls_no_wasted(sample_logs):
    path, logs = sample_logs
    comparisons = load_comparison_logs(path)
    # Threshold higher than any similarity
    wasted = filter_wasted_calls(comparisons, threshold=0.999)
    assert len(wasted) == 0

def test_stratify_by_query(sample_logs):
    path, logs = sample_logs
    comparisons = load_comparison_logs(path)
    wasted = filter_wasted_calls(comparisons, threshold=0.95)
    stratified = stratify_by_query(wasted)

    assert "q1" in stratified
    assert "q2" in stratified
    assert "q3" in stratified
    assert len(stratified["q1"]) == 1  # 0.98
    assert len(stratified["q2"]) == 2  # 0.99, 0.96
    assert len(stratified["q3"]) == 2  # 0.97, 0.98

def test_select_stratified_sample_small_pool(sample_logs):
    path, logs = sample_logs
    comparisons = load_comparison_logs(path)
    wasted = filter_wasted_calls(comparisons, threshold=0.95)
    # Request more than available
    sample = select_stratified_sample(wasted, target_sample_size=100, random_seed=42)
    assert len(sample) == len(wasted)
    # Check that all queries are represented
    qids = set(s["query_id"] for s in sample)
    assert qids == {"q1", "q2", "q3"}

def test_select_stratified_sample_proportional(sample_logs):
    path, logs = sample_logs
    comparisons = load_comparison_logs(path)
    wasted = filter_wasted_calls(comparisons, threshold=0.95)
    # Request exactly 3 samples.
    # q1: 1, q2: 2, q3: 2 -> Total 5.
    # Proportional:
    # q1: 1/5 * 3 = 0.6 -> 1
    # q2: 2/5 * 3 = 1.2 -> 1
    # q3: 2/5 * 3 = 1.2 -> 1
    # Total 3.
    sample = select_stratified_sample(wasted, target_sample_size=3, random_seed=42)
    assert len(sample) == 3
    qids = [s["query_id"] for s in sample]
    # Should have at least one from each group if possible, but with 3 slots and 3 groups, yes.
    assert len(set(qids)) == 3

def test_run_sampling_pipeline(sample_logs, tmp_path):
    log_path, _ = sample_logs
    output_path = tmp_path / "sample.json"
    
    result = run_sampling_pipeline(
        log_path=log_path,
        similarity_threshold=0.95,
        output_path=str(output_path),
        upper_bound=10,
        random_seed=42
    )

    assert result["wasted_calls"] == 5
    assert result["sample_size"] <= 10
    assert os.path.exists(output_path)
    
    with open(output_path) as f:
        saved_data = json.load(f)
    assert isinstance(saved_data, list)
    assert len(saved_data) == result["sample_size"]

def test_calculate_dynamic_sample_size():
    # Test min logic
    assert calculate_dynamic_sample_size(50, 100) == 50
    assert calculate_dynamic_sample_size(200, 100) == 100
    assert calculate_dynamic_sample_size(0, 100) == 0