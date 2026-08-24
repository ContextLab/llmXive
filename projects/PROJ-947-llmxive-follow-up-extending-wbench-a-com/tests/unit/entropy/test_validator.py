"""
Unit tests for the Task Validity Validator (Action Chain Check).
"""

import pytest
import json
from entropy.validator import validate_action_chain, DataValidationError


class TestActionChainValidation:
    """Tests for the validate_action_chain function."""

    def test_valid_simple_chain(self):
        """Test a valid simple action chain: pick then place."""
        chain = [
            {"type": "pick", "object": "cube"},
            {"type": "move", "position": [10, 10]},
            {"type": "place", "object": "cube"}
        ]
        assert validate_action_chain(json.dumps(chain)) is True

    def test_invalid_empty_chain(self):
        """Test that an empty chain returns False."""
        assert validate_action_chain("[]") is False

    def test_invalid_null_chain(self):
        """Test that a null/None chain returns False."""
        assert validate_action_chain(None) is False

    def test_invalid_json_string(self):
        """Test that a malformed JSON string returns False."""
        assert validate_action_chain("{ invalid json }") is False

    def test_invalid_action_type(self):
        """Test that an invalid action type returns False."""
        chain = [
            {"type": "invalid_action", "object": "cube"}
        ]
        assert validate_action_chain(json.dumps(chain)) is False

    def test_invalid_sequence_place_before_pick(self):
        """Test that placing before picking returns False."""
        chain = [
            {"type": "place", "object": "cube"}
        ]
        assert validate_action_chain(json.dumps(chain)) is False

    def test_invalid_sequence_pick_twice(self):
        """Test that picking twice in a row (without intermediate place/drop) returns False."""
        chain = [
            {"type": "pick", "object": "cube1"},
            {"type": "pick", "object": "cube2"}
        ]
        assert validate_action_chain(json.dumps(chain)) is False

    def test_invalid_coordinates(self):
        """Test that coordinates out of bounds return False."""
        chain = [
            {"type": "move", "position": [2000, 2000]}
        ]
        assert validate_action_chain(json.dumps(chain)) is False

    def test_valid_coordinates(self):
        """Test that valid coordinates return True."""
        chain = [
            {"type": "move", "position": [500, 500]}
        ]
        assert validate_action_chain(json.dumps(chain)) is True

    def test_complex_valid_chain(self):
        """Test a complex but valid chain."""
        chain = [
            {"type": "pick", "object": "A"},
            {"type": "move", "position": [10, 10]},
            {"type": "place", "object": "A"},
            {"type": "pick", "object": "B"},
            {"type": "push", "object": "B", "direction": "forward"},
            {"type": "drop", "object": "B"}
        ]
        assert validate_action_chain(json.dumps(chain)) is True

    def test_missing_action_type(self):
        """Test chain with missing 'type' field."""
        chain = [
            {"object": "cube"}
        ]
        assert validate_action_chain(json.dumps(chain)) is False

    def test_non_dict_action(self):
        """Test chain containing a non-dict action."""
        chain = [
            {"type": "pick"},
            "invalid_action_string"
        ]
        assert validate_action_chain(json.dumps(chain)) is False