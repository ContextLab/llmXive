"""
Unit tests for code/rules/metrics.py
"""
import json
import tempfile
from pathlib import Path
import pytest

import sys
# Add project root to path for imports if running standalone
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from rules.metrics import calculate_precision, PrecisionResult, _normalize_rule_signature

def test_normalize_rule_signature():
    """Test that rule signatures are normalized correctly."""
    rule1 = {"type": "transition", "condition": "  a  ", "consequence": "  b  "}
    rule2 = {"type": "transition", "condition": "a", "consequence": "b"}
    
    sig1 = _normalize_rule_signature(rule1)
    sig2 = _normalize_rule_signature(rule2)
    
    assert sig1 == sig2
    assert "a" in sig1 and "b" in sig1

def test_calculate_precision_perfect_match():
    """Test precision calculation when all extracted rules match the oracle."""
    extracted = [
        {"type": "transition", "condition": "A", "consequence": "B"},
        {"type": "transition", "condition": "B", "consequence": "C"}
    ]
    
    oracle_graph = {
        "edges": [
            {"source": "A", "action": "move", "target": "B"},
            {"source": "B", "action": "move", "target": "C"}
        ]
    }
    
    result = calculate_precision(extracted, oracle_graph)
    
    assert isinstance(result, PrecisionResult)
    assert result.precision == 1.0
    assert result.true_positives == 2
    assert result.false_positives == 0
    assert result.total_extracted == 2

def test_calculate_precision_no_match():
    """Test precision calculation when no extracted rules match the oracle."""
    extracted = [
        {"type": "transition", "condition": "X", "consequence": "Y"}
    ]
    
    oracle_graph = {
        "edges": [
            {"source": "A", "action": "move", "target": "B"}
        ]
    }
    
    result = calculate_precision(extracted, oracle_graph)
    
    assert result.precision == 0.0
    assert result.true_positives == 0
    assert result.false_positives == 1

def test_calculate_precision_partial_match():
    """Test precision calculation with mixed results."""
    extracted = [
        {"type": "transition", "condition": "A", "consequence": "B"}, # Match
        {"type": "transition", "condition": "X", "consequence": "Y"}  # No Match
    ]
    
    oracle_graph = {
        "edges": [
            {"source": "A", "action": "move", "target": "B"}
        ]
    }
    
    result = calculate_precision(extracted, oracle_graph)
    
    assert result.precision == 0.5
    assert result.true_positives == 1
    assert result.false_positives == 1

def test_calculate_precision_empty_extracted():
    """Test precision calculation with empty extracted rules."""
    extracted = []
    oracle_graph = {"edges": [{"source": "A", "action": "m", "target": "B"}]}
    
    result = calculate_precision(extracted, oracle_graph)
    
    assert result.precision == 0.0
    assert result.total_extracted == 0

def test_calculate_precision_empty_oracle():
    """Test precision calculation when oracle has no rules."""
    extracted = [{"type": "transition", "condition": "A", "consequence": "B"}]
    oracle_graph = {}
    
    result = calculate_precision(extracted, oracle_graph)
    
    assert result.precision == 0.0
    assert result.false_positives == 1