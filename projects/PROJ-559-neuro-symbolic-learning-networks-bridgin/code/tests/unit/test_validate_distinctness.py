import pytest
import json
import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
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

class TestNormalizeText:
    def test_lowercase_conversion(self):
        assert normalize_text("Hello World") == "hello world"
    
    def test_punctuation_removal(self):
        assert normalize_text("Hello, World!") == "hello world"
    
    def test_whitespace_collapsing(self):
        assert normalize_text("Hello   World") == "hello world"
    
    def test_empty_string(self):
        assert normalize_text("") == ""
    
    def test_none_input(self):
        assert normalize_text(None) == ""

class TestJaccardSimilarity:
    def test_identical_sets(self):
        set1 = {"a", "b", "c"}
        set2 = {"a", "b", "c"}
        assert calculate_jaccard_similarity(set1, set2) == 1.0
    
    def test_disjoint_sets(self):
        set1 = {"a", "b"}
        set2 = {"c", "d"}
        assert calculate_jaccard_similarity(set1, set2) == 0.0
    
    def test_partial_overlap(self):
        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}
        # intersection: {b, c} = 2, union: {a, b, c, d} = 4
        assert calculate_jaccard_similarity(set1, set2) == 0.5
    
    def test_empty_sets(self):
        assert calculate_jaccard_similarity(set(), set()) == 0.0
    
    def test_one_empty_set(self):
        assert calculate_jaccard_similarity({"a", "b"}, set()) == 0.0

class TestExtractSymbolicTrace:
    def test_direct_trace(self):
        data = {"symbolic_trace": "rule1 rule2 rule3"}
        assert extract_symbolic_trace(data) == "rule1 rule2 rule3"
    
    def test_trace_as_list(self):
        data = {"symbolic_trace": ["rule1", "rule2", "rule3"]}
        assert extract_symbolic_trace(data) == "rule1 rule2 rule3"
    
    def test_rule_applications_fallback(self):
        data = {"rule_applications": ["commutativity", "associativity"]}
        assert extract_symbolic_trace(data) == "commutativity associativity"
    
    def test_empty_data(self):
        assert extract_symbolic_trace({}) == ""
    
    def test_none_input(self):
        assert extract_symbolic_trace(None) == ""

class TestExtractNeuralNarrative:
    def test_direct_narrative(self):
        data = {"neural_narrative": "This is the explanation"}
        assert extract_neural_narrative(data) == "This is the explanation"
    
    def test_narrative_as_list(self):
        data = {"neural_narrative": ["This", "is", "the", "explanation"]}
        assert extract_neural_narrative(data) == "This is the explanation"
    
    def test_text_fallback(self):
        data = {"text": "Alternative explanation text"}
        assert extract_neural_narrative(data) == "Alternative explanation text"
    
    def test_empty_data(self):
        assert extract_neural_narrative({}) == ""
    
    def test_none_input(self):
        assert extract_neural_narrative(None) == ""

class TestValidateSymbolicTraceStructure:
    def test_valid_structure(self):
        data = {
            "problem_id": "test_001",
            "rule_applications": [
                {"rule_name": "Commutativity", "description": "a + b = b + a"},
                {"rule_name": "Associativity", "description": "(a + b) + c = a + (b + c)"}
            ]
        }
        is_valid, error = validate_symbolic_trace_structure(data)
        assert is_valid
        assert error == "Valid symbolic trace structure"
    
    def test_missing_problem_id(self):
        data = {
            "rule_applications": [
                {"rule_name": "Commutativity", "description": "a + b = b + a"}
            ]
        }
        is_valid, error = validate_symbolic_trace_structure(data)
        assert not is_valid
        assert "Missing required field: problem_id" in error
    
    def test_empty_rule_applications(self):
        data = {
            "problem_id": "test_001",
            "rule_applications": []
        }
        is_valid, error = validate_symbolic_trace_structure(data)
        assert not is_valid
        assert "rule_applications cannot be empty" in error
    
    def test_missing_rule_name(self):
        data = {
            "problem_id": "test_001",
            "rule_applications": [
                {"description": "a + b = b + a"}
            ]
        }
        is_valid, error = validate_symbolic_trace_structure(data)
        assert not is_valid
        assert "missing 'rule_name'" in error

class TestValidateDistinctness:
    def test_high_similarity_fails(self):
        symbolic = "a + b = b + a commutativity rule"
        neural = "a + b = b + a commutativity rule"
        is_distinct, similarity, details = validate_distinctness(symbolic, neural, threshold=0.3)
        assert not is_distinct
        assert similarity == 1.0
        assert details["is_distinct"] == False
    
    def test_low_similarity_passes(self):
        symbolic = "commutativity associativity distributive"
        neural = "the numbers can be rearranged and grouped differently"
        is_distinct, similarity, details = validate_distinctness(symbolic, neural, threshold=0.3)
        assert is_distinct
        assert details["is_distinct"] == True
    
    def test_empty_inputs(self):
        is_distinct, similarity, details = validate_distinctness("", "test", threshold=0.3)
        assert not is_distinct
        assert "error" in details

class TestValidateExplanationPair:
    def test_valid_pair(self):
        symbolic = {
            "problem_id": "test_001",
            "rule_applications": [
                {"rule_name": "Commutativity", "description": "a + b = b + a"}
            ]
        }
        neuro_symbolic = {
            "problem_id": "test_001",
            "neural_narrative": "The numbers can be rearranged in any order."
        }
        is_valid, report = validate_explanation_pair(symbolic, neuro_symbolic)
        assert is_valid
        assert report["problem_id"] == "test_001"
        assert all(check["passed"] for check in report["checks"])
    
    def test_invalid_symbolic_structure(self):
        symbolic = {
            "problem_id": "test_001"
            # Missing rule_applications
        }
        neuro_symbolic = {
            "problem_id": "test_001",
            "neural_narrative": "Some explanation"
        }
        is_valid, report = validate_explanation_pair(symbolic, neuro_symbolic)
        assert not is_valid
        assert any(check["passed"] == False for check in report["checks"])
    
    def test_high_similarity_fails(self):
        symbolic = {
            "problem_id": "test_001",
            "rule_applications": [
                {"rule_name": "Test", "description": "a + b = b + a"}
            ]
        }
        neuro_symbolic = {
            "problem_id": "test_001",
            "neural_narrative": "a + b = b + a Test"
        }
        is_valid, report = validate_explanation_pair(symbolic, neuro_symbolic)
        assert not is_valid
        assert any(check["check"] == "symbolic_neural_distinctness" and not check["passed"] for check in report["checks"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])