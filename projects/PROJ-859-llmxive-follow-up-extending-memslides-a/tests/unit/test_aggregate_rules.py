"""
Unit tests for the rule aggregation logic (T026b).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from models.aggregate_rules import RuleAggregator
from config import get_config

@pytest.fixture
def mock_config(tmp_path):
    """Create a temporary config with valid paths for testing."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    global_rules_file = tmp_path / "global_rules.json"

    return {
        'paths': {
            'processed_rules': str(rules_dir),
            'global_rules': str(global_rules_file),
            'training': str(tmp_path / "training"),
            'held_out': str(tmp_path / "held_out"),
            'processed': str(tmp_path / "processed")
        }
    }

@pytest.fixture
def sample_per_trace_rules(mock_config):
    """Create sample per-trace rule files in the mock config directory."""
    rules_dir = Path(mock_config['paths']['processed_rules'])

    # Trace 1 rules
    trace1_rules = [
        {"condition": "tool == 'edit'", "action": "compress", "trace_id": "t1"},
        {"condition": "tool == 'delete'", "action": "skip", "trace_id": "t1"}
    ]
    with open(rules_dir / "trace_t1_rules.json", 'w') as f:
        json.dump({"rules": trace1_rules}, f)

    # Trace 2 rules (includes a duplicate of trace1 rule 1)
    trace2_rules = [
        {"condition": "tool == 'edit'", "action": "compress", "trace_id": "t2"},
        {"condition": "tool == 'format'", "action": "apply", "trace_id": "t2"}
    ]
    with open(rules_dir / "trace_t2_rules.json", 'w') as f:
        json.dump({"rules": trace2_rules}, f)

    return rules_dir

def test_load_per_trace_rules(mock_config, sample_per_trace_rules):
    """Test loading rules from multiple files."""
    aggregator = RuleAggregator(mock_config)
    rules = aggregator.load_per_trace_rules()

    assert len(rules) == 4, "Should load 4 rules total (2 from each file)"
    assert rules[0]['condition'] == "tool == 'edit'"
    assert rules[2]['condition'] == "tool == 'edit'" # Duplicate

def test_deduplicate_rules(mock_config, sample_per_trace_rules):
    """Test that duplicate rules are merged and support count incremented."""
    aggregator = RuleAggregator(mock_config)
    raw_rules = aggregator.load_per_trace_rules()
    unique_rules = aggregator.deduplicate_rules(raw_rules)

    assert len(unique_rules) == 3, "Should have 3 unique rules (2 from t1, 1 new from t2, 1 duplicate)"

    # Check support counts
    edit_rule = next(r for r in unique_rules if r['condition'] == "tool == 'edit'")
    assert edit_rule['support_count'] == 2, "The 'edit' rule should have support 2"

    delete_rule = next(r for r in unique_rules if r['condition'] == "tool == 'delete'")
    assert delete_rule['support_count'] == 1

def test_sort_rules(mock_config, sample_per_trace_rules):
    """Test that rules are sorted by support count descending."""
    aggregator = RuleAggregator(mock_config)
    raw_rules = aggregator.load_per_trace_rules()
    unique_rules = aggregator.deduplicate_rules(raw_rules)
    sorted_rules = aggregator.sort_rules(unique_rules)

    # The 'edit' rule should be first
    assert sorted_rules[0]['condition'] == "tool == 'edit'"
    assert sorted_rules[0]['support_count'] == 2

    # The next two should have support 1
    assert sorted_rules[1]['support_count'] == 1
    assert sorted_rules[2]['support_count'] == 1

def test_aggregate_full_pipeline(mock_config, sample_per_trace_rules):
    """Test the full aggregation pipeline and output file creation."""
    aggregator = RuleAggregator(mock_config)
    result = aggregator.aggregate()

    assert 'global_rules' in result
    assert 'metadata' in result
    assert result['metadata']['total_raw_rules'] == 4
    assert result['metadata']['unique_rules'] == 3

    # Verify file was written
    output_path = Path(mock_config['paths']['global_rules'])
    assert output_path.exists(), "Global rules file should be created"

    with open(output_path, 'r') as f:
        saved_data = json.load(f)

    assert 'global_rules' in saved_data
    assert len(saved_data['global_rules']) == 3

def test_aggregate_empty_directory(mock_config):
    """Test that aggregation fails gracefully if no rule files exist."""
    aggregator = RuleAggregator(mock_config)
    with pytest.raises(FileNotFoundError, match="No rule files found"):
        aggregator.load_per_trace_rules()

def test_aggregate_invalid_json(mock_config, tmp_path):
    """Test handling of invalid JSON in rule files."""
    rules_dir = Path(mock_config['paths']['processed_rules'])
    (rules_dir / "bad.json").write_text("not valid json")

    aggregator = RuleAggregator(mock_config)
    with pytest.raises(ValueError, match="Invalid JSON"):
        aggregator.load_per_trace_rules()
