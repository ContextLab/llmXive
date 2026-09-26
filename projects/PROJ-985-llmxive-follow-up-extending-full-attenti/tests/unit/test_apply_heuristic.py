"""
Unit tests for the apply_heuristic module.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.apply_heuristic import (
    load_rules,
    evaluate_rule,
    apply_heuristic_to_token,
    process_document_heuristic
)


class TestLoadRules:
    def test_load_rules_valid_file(self):
        """Test loading rules from a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"rules": [{"condition": "entropy > 1.0", "pos": ["NOUN"]}]}, f)
            temp_path = f.name
        
        try:
            rules = load_rules(temp_path)
            assert len(rules) == 1
            assert rules[0]["condition"] == "entropy > 1.0"
            assert rules[0]["pos"] == ["NOUN"]
        finally:
            os.unlink(temp_path)

    def test_load_rules_missing_file(self):
        """Test that loading from a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_rules("nonexistent_file.json")

    def test_load_rules_invalid_format(self):
        """Test that loading from a file without 'rules' key raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"other_key": []}, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_rules(temp_path)
        finally:
            os.unlink(temp_path)


class TestEvaluateRule:
    def test_rule_matches_entropy(self):
        """Test a rule that matches based on entropy condition."""
        token_data = {"entropy": 2.5, "pos_tag": "NOUN"}
        rule = {"condition": "entropy > 2.0", "pos": ["NOUN"]}
        
        assert evaluate_rule(token_data, rule) is True

    def test_rule_does_not_match_entropy(self):
        """Test a rule that does not match based on entropy condition."""
        token_data = {"entropy": 1.5, "pos_tag": "NOUN"}
        rule = {"condition": "entropy > 2.0", "pos": ["NOUN"]}
        
        assert evaluate_rule(token_data, rule) is False

    def test_rule_matches_pos(self):
        """Test a rule that matches based on POS tag."""
        token_data = {"entropy": 1.0, "pos_tag": "VERB"}
        rule = {"pos": ["VERB", "NOUN"]}
        
        assert evaluate_rule(token_data, rule) is True

    def test_rule_does_not_match_pos(self):
        """Test a rule that does not match based on POS tag."""
        token_data = {"entropy": 1.0, "pos_tag": "ADJ"}
        rule = {"pos": ["VERB", "NOUN"]}
        
        assert evaluate_rule(token_data, rule) is False

    def test_rule_missing_feature(self):
        """Test a rule when the feature is missing."""
        token_data = {"pos_tag": "NOUN"}  # entropy missing
        rule = {"condition": "entropy > 2.0", "pos": ["NOUN"]}
        
        assert evaluate_rule(token_data, rule) is False

    def test_rule_invalid_condition_format(self):
        """Test a rule with an invalid condition format."""
        token_data = {"entropy": 2.5, "pos_tag": "NOUN"}
        rule = {"condition": "invalid condition", "pos": ["NOUN"]}
        
        assert evaluate_rule(token_data, rule) is False

    def test_rule_unknown_operator(self):
        """Test a rule with an unknown operator."""
        token_data = {"entropy": 2.5, "pos_tag": "NOUN"}
        rule = {"condition": "entropy ? 2.0", "pos": ["NOUN"]}
        
        assert evaluate_rule(token_data, rule) is False


class TestApplyHeuristicToToken:
    def test_token_matches_first_rule(self):
        """Test that a token matching the first rule is selected."""
        token_data = {"entropy": 3.0, "pos_tag": "NOUN"}
        rules = [
            {"condition": "entropy > 2.0", "pos": ["NOUN"]},
            {"condition": "entropy > 5.0", "pos": ["VERB"]}
        ]
        
        assert apply_heuristic_to_token(token_data, rules) is True

    def test_token_matches_second_rule(self):
        """Test that a token matching the second rule is selected."""
        token_data = {"entropy": 6.0, "pos_tag": "VERB"}
        rules = [
            {"condition": "entropy > 2.0", "pos": ["NOUN"]},
            {"condition": "entropy > 5.0", "pos": ["VERB"]}
        ]
        
        assert apply_heuristic_to_token(token_data, rules) is True

    def test_token_matches_no_rule(self):
        """Test that a token matching no rule is not selected."""
        token_data = {"entropy": 1.0, "pos_tag": "ADJ"}
        rules = [
            {"condition": "entropy > 2.0", "pos": ["NOUN"]},
            {"condition": "entropy > 5.0", "pos": ["VERB"]}
        ]
        
        assert apply_heuristic_to_token(token_data, rules) is False

    def test_empty_rules(self):
        """Test that a token with no rules is not selected."""
        token_data = {"entropy": 3.0, "pos_tag": "NOUN"}
        rules = []
        
        assert apply_heuristic_to_token(token_data, rules) is False


class TestProcessDocumentHeuristic:
    def test_process_document_basic(self):
        """Test processing a document with basic token data."""
        doc_tokens = [
            {"text": "The", "entropy": 1.0, "pos_tag": "DET"},
            {"text": "cat", "entropy": 3.0, "pos_tag": "NOUN"},
            {"text": "sat", "entropy": 2.5, "pos_tag": "VERB"}
        ]
        rules = [{"condition": "entropy > 2.0", "pos": ["NOUN", "VERB"]}]
        
        # Mock components (not used in this simple case)
        results = process_document_heuristic(doc_tokens, rules, None, None, None)
        
        assert len(results) == 3
        assert results[0]["heuristic_label"] is False  # entropy 1.0 <= 2.0
        assert results[1]["heuristic_label"] is True   # entropy 3.0 > 2.0 and NOUN
        assert results[2]["heuristic_label"] is True   # entropy 2.5 > 2.0 and VERB

    def test_process_document_no_matches(self):
        """Test processing a document where no tokens match rules."""
        doc_tokens = [
            {"text": "The", "entropy": 1.0, "pos_tag": "DET"},
            {"text": "a", "entropy": 0.5, "pos_tag": "DET"}
        ]
        rules = [{"condition": "entropy > 5.0", "pos": ["NOUN"]}]
        
        results = process_document_heuristic(doc_tokens, rules, None, None, None)
        
        assert all(r["heuristic_label"] is False for r in results)