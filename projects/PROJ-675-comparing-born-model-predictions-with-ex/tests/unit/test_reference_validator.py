"""
Unit tests for the Reference Validator Agent.
Verifies Constitution Principle II compliance.
"""
import pytest
from code.validators.reference_validator import (
    _normalize_tokens,
    _calculate_token_overlap,
    validate_citation,
    TOKEN_OVERLAP_THRESHOLD
)

class TestNormalizeTokens:
    def test_basic_normalization(self):
        text = "The Quick Brown Fox"
        tokens = _normalize_tokens(text)
        # Stop words like 'the' should be removed
        assert 'the' not in tokens
        assert 'quick' in tokens
        assert 'brown' in tokens
        assert 'fox' in tokens
        # Should be sorted and unique
        assert tokens == sorted(list(set(tokens)))

    def test_empty_string(self):
        assert _normalize_tokens("") == []
        assert _normalize_tokens(None) == []

    def test_punctuation_removal(self):
        text = "Hello, world! This is a test."
        tokens = _normalize_tokens(text)
        assert ',' not in tokens
        assert '!' not in tokens
        assert '.' not in tokens
        assert 'hello' in tokens
        assert 'world' in tokens

    def test_stop_word_removal(self):
        text = "A study on the effects of water"
        tokens = _normalize_tokens(text)
        assert 'a' not in tokens
        assert 'on' not in tokens
        assert 'the' not in tokens
        assert 'of' not in tokens
        assert 'study' in tokens
        assert 'effects' in tokens
        assert 'water' in tokens

class TestCalculateTokenOverlap:
    def test_identical_sets(self):
        set1 = ['a', 'b', 'c']
        set2 = ['a', 'b', 'c']
        assert _calculate_token_overlap(set1, set2) == 1.0

    def test_no_overlap(self):
        set1 = ['a', 'b']
        set2 = ['c', 'd']
        assert _calculate_token_overlap(set1, set2) == 0.0

    def test_partial_overlap(self):
        set1 = ['a', 'b', 'c']
        set2 = ['b', 'c', 'd']
        # Intersection: {b, c} (2)
        # Union: {a, b, c, d} (4)
        assert _calculate_token_overlap(set1, set2) == 0.5

    def test_empty_sets(self):
        assert _calculate_token_overlap([], []) == 0.0
        assert _calculate_token_overlap(['a'], []) == 0.0
        assert _calculate_token_overlap([], ['a']) == 0.0

class TestValidateCitation:
    def test_high_overlap(self):
        claimed = "Experimental Solvation Energies"
        actual = {
            "title": "Experimental Solvation Energies of Small Ions"
        }
        is_valid, score, reason = validate_citation(claimed, actual)
        assert is_valid is True
        assert score >= TOKEN_OVERLAP_THRESHOLD
        assert "PASSED" in reason

    def test_low_overlap(self):
        claimed = "Quantum Mechanics Introduction"
        actual = {
            "title": "Classical Thermodynamics of Gases"
        }
        is_valid, score, reason = validate_citation(claimed, actual)
        assert is_valid is False
        assert score < TOKEN_OVERLAP_THRESHOLD
        assert "FAILED" in reason

    def test_missing_title(self):
        claimed = "Some Title"
        actual = {"source": "NIST"} # No title key
        is_valid, score, reason = validate_citation(claimed, actual)
        assert is_valid is False
        assert score == 0.0
        assert "missing" in reason.lower()

    def test_case_insensitivity(self):
        claimed = "THE BORN MODEL"
        actual = {
            "title": "the born model for solvation"
        }
        is_valid, score, reason = validate_citation(claimed, actual)
        assert is_valid is True
        assert score == 1.0 # All meaningful tokens match

    def test_threshold_boundary(self):
        # Construct a case where overlap is exactly 0.7 (if possible) or close
        # This tests the >= condition
        claimed = "a b c d e f g h"
        actual = {
            "title": "a b c d e f g h i j"
        }
        # Tokens: {a,b,c,d,e,f,g,h} vs {a,b,c,d,e,f,g,h,i,j}
        # Intersection: 8, Union: 10 -> 0.8
        is_valid, score, reason = validate_citation(claimed, actual)
        assert is_valid is True
        assert score >= 0.7