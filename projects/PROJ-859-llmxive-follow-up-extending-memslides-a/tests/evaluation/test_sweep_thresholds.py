"""
Tests for the sweep_thresholds module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from evaluation.sweep_thresholds import (
    SweepThresholdsError,
    load_global_rules,
    prune_rules_by_min_support,
    prune_rules_by_max_depth,
    prune_rules_by_count,
    apply_pruning,
    calculate_compression_ratio,
    run_sweep
)

# Mock config for testing
MOCK_CONFIG = {
    "paths": {
        "global_rules": "data/processed/rules/global_rules.json",
        "sweep_rules": "data/processed/rules/sweeps",
        "sweep_config": "data/processed/sweep_config.json"
    }
}

@pytest.fixture
def sample_rules():
    """Provide a sample list of rules for testing."""
    return [
        {"id": 1, "support": 0.9, "depth": 3, "rule": "A -> B"},
        {"id": 2, "support": 0.5, "depth": 5, "rule": "C -> D"},
        {"id": 3, "support": 0.2, "depth": 2, "rule": "E -> F"},
        {"id": 4, "support": 0.1, "depth": 8, "rule": "G -> H"},
    ]

@pytest.fixture
def temp_global_rules_file(sample_rules, tmp_path):
    """Create a temporary global rules file."""
    file_path = tmp_path / "global_rules.json"
    with open(file_path, 'w') as f:
        json.dump(sample_rules, f)
    return file_path

def test_prune_by_min_support(sample_rules):
    """Test pruning rules by minimum support."""
    pruned = prune_rules_by_min_support(sample_rules, 0.3)
    assert len(pruned) == 2
    assert all(r["support"] >= 0.3 for r in pruned)

def test_prune_by_max_depth(sample_rules):
    """Test pruning rules by maximum depth."""
    pruned = prune_rules_by_max_depth(sample_rules, 4)
    assert len(pruned) == 2
    assert all(r["depth"] <= 4 for r in pruned)

def test_prune_by_count(sample_rules):
    """Test pruning rules by maximum count."""
    pruned = prune_rules_by_count(sample_rules, 2)
    assert len(pruned) == 2
    # Should be sorted by support descending
    assert pruned[0]["id"] == 1
    assert pruned[1]["id"] == 2

def test_apply_pruning_valid(sample_rules):
    """Test apply_pruning with valid methods."""
    result = apply_pruning(sample_rules, "min_support", 0.5)
    assert len(result) == 2

    result = apply_pruning(sample_rules, "max_depth", 3)
    assert len(result) == 2

    result = apply_pruning(sample_rules, "max_count", 3)
    assert len(result) == 3

def test_apply_pruning_invalid_method(sample_rules):
    """Test apply_pruning with invalid method raises error."""
    with pytest.raises(SweepThresholdsError):
        apply_pruning(sample_rules, "invalid_method", 10)

def test_calculate_compression_ratio():
    """Test compression ratio calculation."""
    assert calculate_compression_ratio(100, 50) == 0.5
    assert calculate_compression_ratio(100, 0) == 0.0
    assert calculate_compression_ratio(0, 0) == 0.0

def test_load_global_rules_missing_file(tmp_path):
    """Test loading from a missing file raises error."""
    config = {"paths": {"global_rules": str(tmp_path / "missing.json")}}
    with pytest.raises(SweepThresholdsError):
        load_global_rules(config)

def test_load_global_rules_invalid_json(tmp_path):
    """Test loading invalid JSON raises error."""
    file_path = tmp_path / "invalid.json"
    file_path.write_text("not valid json")
    config = {"paths": {"global_rules": str(file_path)}}
    with pytest.raises(SweepThresholdsError):
        load_global_rules(config)

def test_run_sweep(sample_rules, tmp_path):
    """Test the full sweep execution."""
    output_dir = tmp_path / "sweeps"
    sweep_config = {
        "sweep_methods": [
            {
                "method": "min_support",
                "param": "min_support",
                "values": [0.0, 0.5]
            }
        ]
    }

    metadata = run_sweep(sample_rules, output_dir, sweep_config)

    assert metadata["total_sweeps"] == 2
    assert metadata["original_rule_count"] == 4
    assert len(metadata["results"]) == 2

    # Check that files were created
    files = list(output_dir.glob("*.json"))
    assert len(files) == 2
    
    # Verify content of one file
    with open(files[0], 'r') as f:
        loaded_rules = json.load(f)
        assert isinstance(loaded_rules, list)
