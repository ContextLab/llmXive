"""
Test for sampling log schema (T046 related, but good to have in test suite).
"""
import pytest
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sampling_log_path = project_root / "data" / "processed" / "sampling_log.json"

def test_sampling_log_schema():
    """Verify sampling_log.json schema."""
    if not sampling_log_path.exists():
        pytest.skip("sampling_log.json not found.")
    
    with open(sampling_log_path, 'r') as f:
        data = json.load(f)
    
    required_keys = ["sample_size", "seed", "method", "total_rows_scanned"]
    for key in required_keys:
        assert key in data, f"Missing key '{key}' in sampling_log.json"
    
    assert isinstance(data["sample_size"], int)
    assert data["seed"] == 42
    assert data["method"] == "streaming_islice"
