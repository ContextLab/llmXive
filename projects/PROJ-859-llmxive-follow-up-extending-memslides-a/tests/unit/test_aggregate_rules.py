"""
Unit tests for rule aggregation functionality (Task T026b).
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from models.aggregate_rules import RuleAggregator


@pytest.fixture
def sample_config(tmp_path):
    """Create a temporary config for testing."""
    processed_rules_dir = tmp_path / 'processed' / 'rules'
    processed_rules_dir.mkdir(parents=True)
    
    config = {
        'paths': {
            'processed_rules': str(processed_rules_dir)
        },
        'rule_aggregation': {
            'min_support': 2
        }
    }
    return config


@pytest.fixture
def sample_per_trace_rules(tmp_path, sample_config):
    """Create sample per-trace rule files for testing."""
    input_dir = Path(sample_config['paths']['processed_rules'])
    
    # Create sample rules for trace_001
    trace_001_rules = [
        {
            'conditions': [{'field': 'tool', 'op': 'eq', 'value': 'edit'}],
            'actions': [{'type': 'compress', 'ratio': 0.5}]
        },
        {
            'conditions': [{'field': 'tool', 'op': 'eq', 'value': 'delete'}],
            'actions': [{'type': 'compress', 'ratio': 0.3}]
        }
    ]
    
    with open(input_dir / 'trace_trace_001_rules.json', 'w') as f:
        json.dump(trace_001_rules, f)
    
    # Create sample rules for trace_002 (some overlap)
    trace_002_rules = [
        {
            'conditions': [{'field': 'tool', 'op': 'eq', 'value': 'edit'}],
            'actions': [{'type': 'compress', 'ratio': 0.5}]
        },
        {
            'conditions': [{'field': 'tool', 'op': 'eq', 'value': 'move'}],
            'actions': [{'type': 'compress', 'ratio': 0.7}]
        }
    ]
    
    with open(input_dir / 'trace_trace_002_rules.json', 'w') as f:
        json.dump(trace_002_rules, f)
    
    # Create sample rules for trace_003 (unique rule)
    trace_003_rules = [
        {
            'conditions': [{'field': 'tool', 'op': 'eq', 'value': 'unique'}],
            'actions': [{'type': 'compress', 'ratio': 0.9}]
        }
    ]
    
    with open(input_dir / 'trace_trace_003_rules.json', 'w') as f:
        json.dump(trace_003_rules, f)
    
    return list(input_dir.glob('trace_*_rules.json'))


def test_canonicalize_rule(sample_config):
    """Test that rules are canonicalized correctly."""
    aggregator = RuleAggregator(sample_config)
    
    rule1 = {
        'conditions': [{'field': 'tool', 'op': 'eq', 'value': 'edit'}],
        'actions': [{'type': 'compress', 'ratio': 0.5}]
    }
    
    rule2 = {
        'conditions': [{'field': 'tool', 'op': 'eq', 'value': 'edit'}],
        'actions': [{'type': 'compress', 'ratio': 0.5}]
    }
    
    rule3 = {
        'conditions': [{'field': 'tool', 'op': 'eq', 'value': 'delete'}],
        'actions': [{'type': 'compress', 'ratio': 0.5}]
    }
    
    # Same rules should have same canonical key
    assert aggregator._canonicalize_rule(rule1) == aggregator._canonicalize_rule(rule2)
    
    # Different rules should have different canonical keys
    assert aggregator._canonicalize_rule(rule1) != aggregator._canonicalize_rule(rule3)


def test_load_per_trace_rules(sample_config, sample_per_trace_rules):
    """Test loading per-trace rules."""
    aggregator = RuleAggregator(sample_config)
    
    trace_ids = ['trace_001', 'trace_002', 'trace_003']
    per_trace_rules = aggregator._load_per_trace_rules(trace_ids)
    
    assert len(per_trace_rules) == 3
    assert 'trace_001' in per_trace_rules
    assert 'trace_002' in per_trace_rules
    assert 'trace_003' in per_trace_rules
    
    assert len(per_trace_rules['trace_001']) == 2
    assert len(per_trace_rules['trace_002']) == 2
    assert len(per_trace_rules['trace_003']) == 1


def test_aggregate_rules(sample_config, sample_per_trace_rules):
    """Test rule aggregation with min_support filtering."""
    aggregator = RuleAggregator(sample_config)
    
    # Load rules
    trace_ids = ['trace_001', 'trace_002', 'trace_003']
    per_trace_rules = aggregator._load_per_trace_rules(trace_ids)
    
    # Aggregate
    global_rules = aggregator._aggregate_rules(per_trace_rules)
    
    # With min_support=2:
    # - 'edit' rule appears in trace_001 and trace_002 (support=2) -> INCLUDED
    # - 'delete' rule appears only in trace_001 (support=1) -> EXCLUDED
    # - 'move' rule appears only in trace_002 (support=1) -> EXCLUDED
    # - 'unique' rule appears only in trace_003 (support=1) -> EXCLUDED
    
    assert len(global_rules) == 1
    assert global_rules[0]['support_count'] == 2
    assert global_rules[0]['support_traces'] == ['trace_001', 'trace_002']


def test_aggregate_with_min_support_1(sample_config, sample_per_trace_rules):
    """Test rule aggregation with min_support=1 (no filtering)."""
    config = sample_config.copy()
    config['rule_aggregation']['min_support'] = 1
    aggregator = RuleAggregator(config)
    
    trace_ids = ['trace_001', 'trace_002', 'trace_003']
    per_trace_rules = aggregator._load_per_trace_rules(trace_ids)
    
    global_rules = aggregator._aggregate_rules(per_trace_rules)
    
    # All rules should be included
    assert len(global_rules) == 4  # edit, delete, move, unique


def test_save_global_rules(sample_config, sample_per_trace_rules, tmp_path):
    """Test saving global rules to file."""
    aggregator = RuleAggregator(sample_config)
    
    trace_ids = ['trace_001', 'trace_002', 'trace_003']
    result = aggregator.aggregate(trace_ids)
    
    output_path = aggregator.save(result)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert 'global_rules' in saved_data
    assert 'metadata' in saved_data
    assert len(saved_data['global_rules']) == 1  # With min_support=2


def test_aggregate_no_files(sample_config, tmp_path):
    """Test aggregation when no rule files exist."""
    config = sample_config.copy()
    config['paths']['processed_rules'] = str(tmp_path / 'empty')
    aggregator = RuleAggregator(config)
    
    with pytest.raises(ValueError, match="No trace rule files found"):
        aggregator.aggregate()


def test_aggregate_missing_file(sample_config):
    """Test aggregation when a specific trace file is missing."""
    aggregator = RuleAggregator(sample_config)
    
    with pytest.raises(FileNotFoundError, match="Per-trace rule file not found"):
        aggregator._load_per_trace_rules(['nonexistent_trace'])
