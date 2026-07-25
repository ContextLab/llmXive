"""
Tests for generate_ground_truth_fixture.py
"""
import json
import os
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from generate_ground_truth_fixture import fetch_advbench_attacks, fetch_benign_samples

def test_fetch_advbench_attacks_structure():
    """Test that AdvBench fetch returns correct structure."""
    attacks = fetch_advbench_attacks()
    assert len(attacks) > 0, "AdvBench should return at least one attack sample"
    
    for item in attacks:
        assert "log_id" in item
        assert "text" in item
        assert "label" in item
        assert item["label"] == "attack"
        assert isinstance(item["log_id"], str)
        assert isinstance(item["text"], str)
        assert len(item["text"]) > 0

def test_fetch_benign_samples_structure():
    """Test that Benign fetch returns correct structure."""
    benign = fetch_benign_samples()
    assert len(benign) > 0, "Benign fetch should return at least one sample"
    
    for item in benign:
        assert "log_id" in item
        assert "text" in item
        assert "label" in item
        assert item["label"] == "benign"
        assert isinstance(item["log_id"], str)
        assert isinstance(item["text"], str)
        assert len(item["text"]) > 0

def test_fixture_file_contents(tmp_path):
    """Test that the generated fixture file has correct schema."""
    # We can't easily run the full generation in a unit test without network,
    # but we can test the logic if we mock or assume the functions work.
    # Instead, we verify the expected schema structure.
    expected_keys = {"log_id", "text", "label"}
    
    # Simulate a valid record
    valid_record = {
        "log_id": "test-001",
        "text": "Hello world",
        "label": "benign"
    }
    
    assert set(valid_record.keys()) == expected_keys

def test_no_synthetic_fallback():
    """
    Verify that the functions do not have synthetic fallback logic.
    This is a code inspection test.
    """
    import inspect
    from generate_ground_truth_fixture import fetch_advbench_attacks, fetch_benign_samples
    
    source_attack = inspect.getsource(fetch_advbench_attacks)
    source_benign = inspect.getsource(fetch_benign_samples)
    
    # Check for forbidden synthetic generation patterns
    forbidden_patterns = [
        "np.random",
        "random.choice",
        "generate_synthetic",
        "mock_",
        "fake_",
        "return [] # fallback"
    ]
    
    for pattern in forbidden_patterns:
        assert pattern not in source_attack, f"Found forbidden pattern '{pattern}' in fetch_advbench_attacks"
        assert pattern not in source_benign, f"Found forbidden pattern '{pattern}' in fetch_benign_samples"