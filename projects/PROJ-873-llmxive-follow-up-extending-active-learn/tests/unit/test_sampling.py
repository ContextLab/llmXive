import json
import os
import random
import tempfile
import random
import pytest
from pathlib import Path

# Adjust path if running from tests/unit
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))

from sampling import (
    load_comparison_logs,
    filter_wasted_calls,
    load_sample_config,
    select_simple_random_sample,
    run_sampling_pipeline
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_log_data():
    return [
        {"pair_id": "p1", "doc1_id": "d1", "doc2_id": "d2", "cosine_sim": 0.96, "is_wasted": True, "timestamp": "2023-01-01T00:00:00"},
        {"pair_id": "p2", "doc1_id": "d3", "doc2_id": "d4", "cosine_sim": 0.94, "is_wasted": False, "timestamp": "2023-01-01T00:00:01"},
        {"pair_id": "p3", "doc1_id": "d5", "doc2_id": "d6", "cosine_sim": 0.99, "is_wasted": True, "timestamp": "2023-01-01T00:00:02"},
        {"pair_id": "p4", "doc1_id": "d7", "doc2_id": "d8", "cosine_sim": 0.80, "is_wasted": False, "timestamp": "2023-01-01T00:00:03"},
        {"pair_id": "p5", "doc1_id": "d9", "doc2_id": "d10", "cosine_sim": 0.97, "is_wasted": True, "timestamp": "2023-01-01T00:00:04"},
    ]

@pytest.fixture
def sample_config():
    return {
        "sample_size": 2,
        "minimum_threshold": 10,
        "percentage": 0.05,
        "skip_validation": False
    }
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(config, f)
        return f.name

def test_load_comparison_logs(temp_dir, sample_log_data):
    log_path = os.path.join(temp_dir, "test_log.json")
    with open(log_path, "w") as f:
        for record in sample_log_data:
            f.write(json.dumps(record) + "\n")
    
    loaded = load_comparison_logs(log_path)
    assert len(loaded) == 5
    assert loaded[0]["pair_id"] == "p1"

def test_filter_wasted_calls(sample_log_data):
    filtered = filter_wasted_calls(sample_log_data, threshold=0.95)
    assert len(filtered) == 3
    assert all(r["cosine_sim"] > 0.95 for r in filtered)
    pair_ids = {r["pair_id"] for r in filtered}
    assert pair_ids == {"p1", "p3", "p5"}

def test_load_sample_config(temp_dir, sample_config):
    config_path = os.path.join(temp_dir, "config.json")
    with open(config_path, "w") as f:
        json.dump(sample_config, f)
    
    loaded = load_sample_config(config_path)
    assert loaded["sample_size"] == 2

def test_select_simple_random_sample():
    candidates = [{"id": i} for i in range(10)]
    seed = 42
    random.seed(seed)
    indices = select_simple_random_sample(candidates, 3, seed)
    assert len(indices) == 3
    assert all(0 <= i < 10 for i in indices)
    assert len(set(indices)) == 3  # No duplicates

def test_run_sampling_pipeline(temp_dir, sample_log_data, sample_config):
    log_path = os.path.join(temp_dir, "log.json")
    config_path = os.path.join(temp_dir, "config.json")
    output_path = os.path.join(temp_dir, "sample.json")
    
    with open(log_path, "w") as f:
        for r in sample_log_data:
            f.write(json.dumps(r) + "\n")
    
    with open(config_path, "w") as f:
        json.dump(sample_config, f)
    
    result = run_sampling_pipeline(
        log_path=log_path,
        config_path=config_path,
        output_path=output_path,
        threshold=0.95
    )
    
    assert os.path.exists(output_path)
    with open(output_path, "r") as f:
        sample_indices = json.load(f)
    
    assert len(sample_indices) == 2
    assert isinstance(sample_indices, list)
    assert all(isinstance(i, int) for i in sample_indices)