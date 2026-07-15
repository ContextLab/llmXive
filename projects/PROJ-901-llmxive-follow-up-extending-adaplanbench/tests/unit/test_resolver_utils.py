"""
Unit tests for resolver_utils.py functions.
Tests parse_intent and match_constraint in isolation.
"""
import pytest
from agent.resolver_utils import parse_intent, match_constraint
from agent.constraint_store import Constraint


class TestParseIntent:
    """Tests for the parse_intent function."""

    def test_parse_simple_action_object(self):
        """Test parsing a simple action-object sentence."""
        intent = "place the red block"
        result = parse_intent(intent)
        
        assert result is not None
        assert result["action"] == "place"
        assert result["object"] == "block"
        assert "red" in result["modifiers"]

    def test_parse_with_location(self):
        """Test parsing a sentence with a location."""
        intent = "put the cup on the table"
        result = parse_intent(intent)
        
        assert result is not None
        assert result["action"] == "put"
        assert result["object"] == "cup"
        assert result["location"] == "the table"

    def test_parse_negation(self):
        """Test parsing a negated intent."""
        intent = "do not touch the red button"
        result = parse_intent(intent)
        
        assert result is not None
        assert result["is_negation"] is True
        assert result["action"] == "do"  # First word

    def test_parse_empty_string(self):
        """Test parsing an empty string returns None."""
        result = parse_intent("")
        assert result is None

    def test_parse_none_input(self):
        """Test parsing None returns None."""
        result = parse_intent(None)
        assert result is None

    def test_parse_short_string(self):
        """Test parsing a single word returns None."""
        result = parse_intent("place")
        assert result is None


class TestMatchConstraint:
    """Tests for the match_constraint function."""

    def test_exact_match_violation(self):
        """Test exact match resulting in a violation."""
        parsed = parse_intent("do not place red objects on blue surfaces")
        constraint = Constraint(
            id="c1",
            text="do not place red objects on blue surfaces",
            is_active=True
        )
        
        result = match_constraint(parsed, constraint)
        
        assert result["matched"] is True
        assert result["match_type"] == "exact"
        assert result["is_violation"] is False  # Both have negation

    def test_exact_match_violation_positive(self):
        """Test exact match where intent violates constraint."""
        parsed = parse_intent("place red objects on blue surfaces")
        constraint = Constraint(
            id="c2",
            text="do not place red objects on blue surfaces",
            is_active=True
        )
        
        result = match_constraint(parsed, constraint)
        
        assert result["matched"] is True
        assert result["match_type"] == "negation"
        assert result["is_violation"] is True

    def test_substring_match(self):
        """Test substring matching."""
        parsed = parse_intent("I want to place the red block on the blue table")
        constraint = Constraint(
            id="c3",
            text="place the red block on the blue table",
            is_active=True
        )
        
        result = match_constraint(parsed, constraint)
        
        assert result["matched"] is True
        assert result["match_type"] == "substring"
        assert result["is_violation"] is True

    def test_no_match(self):
        """Test when there is no match."""
        parsed = parse_intent("pick up the green apple")
        constraint = Constraint(
            id="c4",
            text="do not use red objects",
            is_active=True
        )
        
        result = match_constraint(parsed, constraint)
        
        assert result["matched"] is False
        assert result["match_type"] == "miss"
        assert result["is_violation"] is False

    def test_match_with_none_intent(self):
        """Test matching with None parsed intent."""
        constraint = Constraint(id="c5", text="test", is_active=True)
        result = match_constraint(None, constraint)
        
        assert result["matched"] is False
        assert result["is_violation"] is False

    def test_match_with_none_constraint(self):
        """Test matching with None constraint."""
        parsed = parse_intent("test")
        result = match_constraint(parsed, None)
        
        assert result["matched"] is False
        assert result["is_violation"] is False

    def test_negation_pattern_match(self):
        """Test negation pattern detection."""
        parsed = parse_intent("avoid using red items")
        constraint = Constraint(
            id="c6",
            text="do not use red items",
            is_active=True
        )
        
        result = match_constraint(parsed, constraint)
        
        # Should match via negation pattern
        assert result["matched"] is True
        assert result["match_type"] == "negation"
        assert result["is_violation"] is False  # Both are negations

    def test_negation_violation(self):
        """Test violation when intent contradicts negation constraint."""
        parsed = parse_intent("use red items")
        constraint = Constraint(
            id="c7",
            text="do not use red items",
            is_active=True
        )
        
        result = match_constraint(parsed, constraint)
        
        assert result["matched"] is True
        assert result["match_type"] == "negation"
        assert result["is_violation"] is True
