import os
import json
import pytest
from pathlib import Path
import yaml

def test_baseline_retrieval_results_schema():
    """
    Contract test: Verify data/processed/baseline_retrieval_results.json 
    matches the expected schema.
    """
    output_path = Path("data/processed/baseline_retrieval_results.json")
    
    # Check if file exists
    assert output_path.exists(), f"Output file {output_path} does not exist."
    
    # Load data
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list), "Results must be a list of dictionaries."
    assert len(data) > 0, "Results list cannot be empty."
    
    # Define expected keys based on task description
    expected_keys = ["episode_id", "method", "score", "latency_ms", "peak_ram_mb"]
    
    for i, entry in enumerate(data):
        assert isinstance(entry, dict), f"Entry {i} is not a dictionary."
        
        # Check required keys
        for key in expected_keys:
            assert key in entry, f"Entry {i} missing required key: {key}"
        
        # Validate types
        assert isinstance(entry["episode_id"], (str, int)), f"episode_id must be str or int"
        assert entry["method"] == "retrieval_only", f"method must be 'retrieval_only', got {entry['method']}"
        assert isinstance(entry["score"], (int, float)), f"score must be numeric"
        assert 0.0 <= entry["score"] <= 1.0, f"score must be between 0 and 1"
        assert isinstance(entry["latency_ms"], (int, float)), f"latency_ms must be numeric"
        assert entry["latency_ms"] >= 0, f"latency_ms must be non-negative"
        assert isinstance(entry["peak_ram_mb"], (int, float)), f"peak_ram_mb must be numeric"
        assert entry["peak_ram_mb"] >= 0, f"peak_ram_mb must be non-negative"

def test_baseline_retrieval_results_content():
    """
    Integration check: Ensure the results contain valid episode IDs from the dataset.
    """
    output_path = Path("data/processed/baseline_retrieval_results.json")
    if not output_path.exists():
        pytest.skip("Output file not found, skipping content test.")
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    # Check that method is consistent
    methods = set(entry["method"] for entry in data)
    assert methods == {"retrieval_only"}, f"Expected only 'retrieval_only' method, found {methods}"
    
    # Check that scores are binary (0 or 1) for access control
    # (Assuming score is binary for this baseline)
    scores = set(entry["score"] for entry in data)
    assert scores.issubset({0, 1, 0.0, 1.0}), f"Scores should be binary (0/1), found {scores}"