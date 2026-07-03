import pytest
import json
import os
import sys
from typing import Dict, Any

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from generate.validate_distinctness import (
    normalize_text,
    calculate_jaccard_similarity,
    extract_symbolic_trace,
    extract_neural_narrative,
    validate_symbolic_trace_structure,
    validate_distinctness,
    validate_explanation_pair
)

class TestDistinctnessValidation:
    """Unit tests for distinctness validation functions."""

    def test_normalize_text(self):
        """Test text normalization function."""
        assert normalize_text("Hello  World") == "hello world"
        assert normalize_text("  TEST  ") == "test"
        assert normalize_text("") == ""
        assert normalize_text(None) == ""

    def test_calculate_jaccard_similarity(self):
        """Test Jaccard similarity calculation."""
        # Identical texts
        assert calculate_jaccard_similarity("hello world", "hello world") == 1.0

        # Completely different texts
        sim = calculate_jaccard_similarity("hello world", "foo bar baz")
        assert sim == 0.0

        # Partial overlap
        sim = calculate_jaccard_similarity("hello world", "hello there")
        assert 0.3 < sim < 0.6  # Should have some overlap

        # Empty inputs
        assert calculate_jaccard_similarity("", "test") == 0.0
        assert calculate_jaccard_similarity("test", "") == 0.0

    def test_extract_symbolic_trace(self):
        """Test symbolic trace extraction."""
        # Test with explicit symbolic_trace key
        exp = {
            "symbolic_trace": ["Step 1: Apply rule", "Step 2: Apply rule"]
        }
        trace = extract_symbolic_trace(exp)
        assert "Step 1" in trace
        assert "Step 2" in trace

        # Test with steps key
        exp = {
            "steps": ["Rule A", "Rule B"]
        }
        trace = extract_symbolic_trace(exp)
        assert "Rule A" in trace

        # Test with no trace
        exp = {}
        assert extract_symbolic_trace(exp) == ""

    def test_extract_neural_narrative(self):
        """Test neural narrative extraction."""
        # Test with explicit neural_narrative key
        exp = {
            "neural_narrative": "This is a fluent explanation."
        }
        narrative = extract_neural_narrative(exp)
        assert "fluent" in narrative

        # Test with explanation_text key
        exp = {
            "explanation_text": "Another explanation."
        }
        narrative = extract_neural_narrative(exp)
        assert "explanation" in narrative

    def test_validate_symbolic_trace_structure_valid(self):
        """Test validation of a properly structured symbolic trace."""
        trace = "Step 1: Apply commutativity rule. Step 2: Apply associativity rule."
        is_valid, message = validate_symbolic_trace_structure(trace)
        assert is_valid
        assert "valid" in message.lower()

    def test_validate_symbolic_trace_structure_empty(self):
        """Test validation of an empty symbolic trace."""
        is_valid, message = validate_symbolic_trace_structure("")
        assert not is_valid
        assert "empty" in message.lower()

    def test_validate_symbolic_trace_structure_no_rules(self):
        """Test validation of a trace without rule keywords."""
        trace = "This is just some text without any rules."
        is_valid, message = validate_symbolic_trace_structure(trace)
        assert not is_valid
        assert "rule" in message.lower()

    def test_validate_distinctness_valid_pair(self):
        """Test validation of a valid distinct pair."""
        symbolic = "Step 1: Apply commutativity rule: a + b = b + a. Step 2: Apply associativity."
        neural = "To solve this, we can rearrange the terms and group them differently."

        is_valid, details = validate_distinctness(symbolic, neural)

        assert is_valid
        assert details['jaccard_similarity'] < 0.4
        assert len(details['issues']) == 0

    def test_validate_distinctness_too_similar(self):
        """Test validation when outputs are too similar."""
        symbolic = "Apply commutativity rule: a + b = b + a"
        neural = "Apply commutativity rule: a + b = b + a"

        is_valid, details = validate_distinctness(symbolic, neural)

        assert not is_valid
        assert any("Jaccard similarity" in issue for issue in details['issues'])

    def test_validate_explanation_pair_full(self):
        """Test full explanation pair validation."""
        symbolic_exp = {
            "problem_id": "123",
            "symbolic_trace": [
                "Step 1: Apply commutativity rule",
                "Step 2: Apply associativity rule"
            ]
        }

        neuro_symbolic_exp = {
            "problem_id": "123",
            "neural_narrative": "We can rearrange and group terms to simplify.",
            "symbolic_trace": [
                "Step 1: Apply commutativity rule",
                "Step 2: Apply associativity rule"
            ]
        }

        is_valid, details = validate_explanation_pair(symbolic_exp, neuro_symbolic_exp)

        assert details['symbolic_trace_valid']
        assert 'details' in details

    def test_validate_explanation_pair_invalid_structure(self):
        """Test validation when symbolic trace structure is invalid."""
        symbolic_exp = {"problem_id": "123"}
        neuro_symbolic_exp = {
            "problem_id": "123",
            "neural_narrative": "Some explanation.",
            "symbolic_trace": []  # Empty trace
        }

        is_valid, details = validate_explanation_pair(symbolic_exp, neuro_symbolic_exp)

        assert not is_valid
        assert not details['symbolic_trace_valid']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])