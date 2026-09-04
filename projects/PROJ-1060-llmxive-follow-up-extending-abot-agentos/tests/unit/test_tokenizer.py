"""
Unit tests for the SymbolicTokenizer module.
Tests token mapping accuracy and edge cases.
"""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from code.tokenizer import SymbolicTokenizer, discretize_trace, COARSE_TAXONOMY, FINE_TAXONOMY
from code.config import GRANULARITY, MODEL_ID


class TestSymbolicTokenizer:
    """Tests for the SymbolicTokenizer class."""

    def test_init_coarse_granularity(self):
        """Test initialization with coarse granularity."""
        tokenizer = SymbolicTokenizer(granularity="coarse")
        assert tokenizer.granularity == "coarse"
        assert tokenizer.taxonomy == COARSE_TAXONOMY
        assert tokenizer.model_id == MODEL_ID

    def test_init_fine_granularity(self):
        """Test initialization with fine granularity."""
        tokenizer = SymbolicTokenizer(granularity="fine")
        assert tokenizer.granularity == "fine"
        assert tokenizer.taxonomy == FINE_TAXONOMY
        assert tokenizer.model_id == MODEL_ID

    def test_classify_action_known(self):
        """Test action classification with known action."""
        tokenizer = SymbolicTokenizer()
        result = tokenizer._classify_action("go_to counter")
        assert result in ["go_to", "unknown_action"]

    def test_classify_action_unknown(self):
        """Test action classification with unknown action."""
        tokenizer = SymbolicTokenizer()
        result = tokenizer._classify_action("invalid_action_xyz")
        assert result == "unknown_action"

    def test_classify_state_known(self):
        """Test state classification with known state."""
        tokenizer = SymbolicTokenizer()
        result = tokenizer._classify_state("microwave is open")
        assert result in ["open", "unknown_state"]

    def test_classify_state_unknown(self):
        """Test state classification with unknown state."""
        tokenizer = SymbolicTokenizer()
        result = tokenizer._classify_state("microwave is floating")
        assert result == "unknown_state"

    def test_classify_relation_known(self):
        """Test relation classification with known relation."""
        tokenizer = SymbolicTokenizer()
        result = tokenizer._classify_relation("apple is on_top_of counter")
        assert result in ["on_top_of", "unknown_relation"]

    def test_classify_relation_unknown(self):
        """Test relation classification with unknown relation."""
        tokenizer = SymbolicTokenizer()
        result = tokenizer._classify_relation("apple is floating_above counter")
        assert result == "unknown_relation"

    def test_discretize_trace_empty(self):
        """Test discretization of empty trace."""
        tokenizer = SymbolicTokenizer()
        trace = {}
        tokens = tokenizer.discretize_trace(trace)
        assert tokens == []

    def test_discretize_trace_with_actions(self):
        """Test discretization of trace with actions."""
        tokenizer = SymbolicTokenizer()
        trace = {
            "actions": ["go_to counter", "take apple", "put apple in bowl"]
        }
        tokens = tokenizer.discretize_trace(trace)
        assert len(tokens) == 3
        assert "go_to" in tokens
        assert "take" in tokens
        assert "put" in tokens

    def test_discretize_trace_with_states(self):
        """Test discretization of trace with states."""
        tokenizer = SymbolicTokenizer()
        trace = {
            "states": ["microwave is open", "apple is taken", "microwave is closed"]
        }
        tokens = tokenizer.discretize_trace(trace)
        assert len(tokens) == 3
        assert "open" in tokens
        assert "closed" in tokens

    def test_discretize_trace_with_relations(self):
        """Test discretization of trace with relations."""
        tokenizer = SymbolicTokenizer()
        trace = {
            "relations": ["apple is on_top_of counter", "bowl is near apple"]
        }
        tokens = tokenizer.discretize_trace(trace)
        assert len(tokens) == 2
        assert "on_top_of" in tokens
        assert "near" in tokens

    def test_discretize_trace_mixed(self):
        """Test discretization of trace with mixed content."""
        tokenizer = SymbolicTokenizer()
        trace = {
            "actions": ["go_to counter"],
            "states": ["microwave is open"],
            "relations": ["apple is on_top_of counter"]
        }
        tokens = tokenizer.discretize_trace(trace)
        assert len(tokens) == 3
        assert "go_to" in tokens
        assert "open" in tokens
        assert "on_top_of" in tokens


class TestDiscretizeTraceFunction:
    """Tests for the standalone discretize_trace function."""

    def test_discretize_trace_convenience(self):
        """Test the convenience function discretize_trace."""
        trace = {
            "actions": ["go_to counter"],
            "states": ["microwave is open"]
        }
        tokens = discretize_trace(trace)
        assert len(tokens) == 2
        assert "go_to" in tokens
        assert "open" in tokens

    def test_discretize_trace_with_none_values(self):
        """Test discretization with None values in trace."""
        trace = {
            "actions": None,
            "states": ["microwave is open"],
            "relations": None
        }
        # Should not crash, should handle None gracefully
        tokens = discretize_trace(trace)
        assert len(tokens) == 1
        assert "open" in tokens


class TestTaxonomyConsistency:
    """Tests for taxonomy consistency."""

    def test_coarse_taxonomy_keys(self):
        """Test that coarse taxonomy has all required keys."""
        required_keys = ["object", "location", "action", "state", "relation", "unknown"]
        for key in required_keys:
            assert key in COARSE_TAXONOMY

    def test_fine_taxonomy_keys(self):
        """Test that fine taxonomy has all required keys."""
        required_keys = ["object", "location", "action", "state", "relation", "unknown"]
        for key in required_keys:
            assert key in FINE_TAXONOMY

    def test_coarse_taxonomy_tokens(self):
        """Test that coarse taxonomy tokens are valid."""
        for category, tokens in COARSE_TAXONOMY.items():
            assert isinstance(tokens, list)
            assert len(tokens) > 0
            for token in tokens:
                assert isinstance(token, str)
                assert len(token) > 0

    def test_fine_taxonomy_tokens(self):
        """Test that fine taxonomy tokens are valid."""
        for category, tokens in FINE_TAXONOMY.items():
            assert isinstance(tokens, list)
            assert len(tokens) > 0
            for token in tokens:
                assert isinstance(token, str)
                assert len(token) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
