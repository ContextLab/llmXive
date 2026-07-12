import json
import pytest
from pathlib import Path
import tempfile
import os

from code.sampling.failure_sampler import (
    load_results_file,
    identify_failures,
    stratified_sample,
    run_sampling_pipeline
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_results_file_list(temp_dir):
    data = [{"id": 1, "value": 10}, {"id": 2, "value": 20}]
    file_path = temp_dir / "test.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    result = load_results_file(file_path, "Test")
    assert result == data


def test_load_results_file_dict(temp_dir):
    data = {"results": [{"id": 1, "value": 10}]}
    file_path = temp_dir / "test.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    result = load_results_file(file_path, "Test")
    assert result == data["results"]


def test_load_results_file_missing(temp_dir):
    file_path = temp_dir / "nonexistent.json"
    result = load_results_file(file_path, "Test")
    assert result == []


def test_identify_failures_leak(temp_dir):
    # Simulate Access Control failures (unauthorized exposure > 0)
    records = [
        {"id": 1, "domain": "medical", "unauthorized_exposure_rate": 0.5},
        {"id": 2, "domain": "office", "unauthorized_exposure_rate": 0.0},
        {"id": 3, "domain": "medical", "unauthorized_exposure_rate": 0.1}
    ]
    failures = identify_failures(records, metric_key='unauthorized_exposure_rate', threshold=0.0)
    assert len(failures) == 2
    assert all(f['unauthorized_exposure_rate'] > 0 for f in failures)


def test_identify_failures_utility(temp_dir):
    # Simulate Utility failures (low success rate)
    records = [
        {"id": 1, "domain": "medical", "utility_score": 0.8},
        {"id": 2, "domain": "office", "utility_score": 1.0},
        {"id": 3, "domain": "education", "utility_score": 0.5}
    ]
    failures = identify_failures(records, metric_key='utility_score', threshold=1.0)
    assert len(failures) == 2
    assert all(f['utility_score'] < 1.0 for f in failures)


def test_stratified_sample_balanced(temp_dir):
    # Create a balanced set of failures across domains
    records = [
        {"id": i, "domain": "medical"} for i in range(10)
    ] + [
        {"id": i, "domain": "office"} for i in range(10, 20)
    ] + [
        {"id": i, "domain": "education"} for i in range(20, 30)
    ]
    
    sampled = stratified_sample(records, target_size=9, seed=42)
    
    # Should get 3 from each domain (proportional)
    domains = [r['domain'] for r in sampled]
    assert domains.count('medical') == 3
    assert domains.count('office') == 3
    assert domains.count('education') == 3
    assert len(sampled) == 9


def test_stratified_sample_unbalanced(temp_dir):
    # Create an unbalanced set
    records = [
        {"id": i, "domain": "medical"} for i in range(50)
    ] + [
        {"id": i, "domain": "office"} for i in range(50, 55)
    ]
    
    sampled = stratified_sample(records, target_size=10, seed=42)
    
    # Should be roughly proportional: 50/55 and 5/55 -> ~9 and ~1
    domains = [r['domain'] for r in sampled]
    assert len(sampled) == 10
    # Check that both domains are represented if possible
    assert 'medical' in domains
    assert 'office' in domains


def test_run_sampling_pipeline(temp_dir):
    # Create mock AC and Utility results
    ac_data = [
        {"id": 1, "domain": "medical", "unauthorized_exposure_rate": 0.5},
        {"id": 2, "domain": "office", "unauthorized_exposure_rate": 0.0},
        {"id": 3, "domain": "education", "unauthorized_exposure_rate": 0.2}
    ]
    util_data = [
        {"id": 4, "domain": "medical", "utility_score": 0.8},
        {"id": 5, "domain": "office", "utility_score": 1.0},
        {"id": 6, "domain": "household", "utility_score": 0.9}
    ]
    
    ac_path = temp_dir / "ac_results.json"
    util_path = temp_dir / "util_results.json"
    out_path = temp_dir / "output.json"
    
    with open(ac_path, 'w') as f:
        json.dump(ac_data, f)
    with open(util_path, 'w') as f:
        json.dump(util_data, f)
    
    run_sampling_pipeline(ac_path, util_path, out_path, target_size=2, seed=42)
    
    assert out_path.exists()
    with open(out_path, 'r') as f:
        output = json.load(f)
    
    assert "samples" in output
    assert len(output["samples"]) <= 2 # Should be at most 2
    assert len(output["samples"]) > 0 # Should have at least one failure