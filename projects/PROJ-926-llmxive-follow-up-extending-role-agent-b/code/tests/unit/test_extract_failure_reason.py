"""
Unit tests for the extract_failure_reason function.
"""
import pytest
from src.sim.trajectory_generator import extract_failure_reason


class TestExtractFailureReason:
    """Tests for failure reason extraction logic."""

    def test_empty_log(self):
        """Test that empty action log returns appropriate message."""
        result = extract_failure_reason([])
        assert result == "Empty action log: no actions recorded"

    def test_not_found_pattern(self):
        """Test detection of 'not found' failure pattern."""
        action_log = [
            {"action": "pick up the apple", "observation": "nothing found", "step": 1},
            {"action": "look around", "observation": "still nothing", "step": 2}
        ]
        result = extract_failure_reason(action_log)
        assert "not found" in result.lower() or "failed" in result.lower()

    def test_nothing_to_pick_up(self):
        """Test detection of 'nothing to pick up' pattern."""
        action_log = [
            {"action": "pick up the apple", "observation": "nothing to pick up", "step": 1}
        ]
        result = extract_failure_reason(action_log)
        assert "nothing to pick up" in result.lower()

    def test_timeout_pattern(self):
        """Test detection of timeout failure."""
        action_log = [
            {"action": "move to kitchen", "observation": "timeout: max steps reached", "step": 50}
        ]
        result = extract_failure_reason(action_log)
        assert "timeout" in result.lower()

    def test_invalid_action(self):
        """Test detection of invalid action syntax."""
        action_log = [
            {"action": "invalid_command", "observation": "invalid action syntax", "step": 1}
        ]
        result = extract_failure_reason(action_log)
        assert "invalid action" in result.lower()

    def test_unknown_failure_fallback(self):
        """Test fallback for unclassified failures."""
        action_log = [
            {"action": "move to kitchen", "observation": "some random observation", "step": 1},
            {"action": "look", "observation": "nothing relevant", "step": 2}
        ]
        result = extract_failure_reason(action_log)
        assert result != "Unknown failure"  # Should have a descriptive fallback
        assert "step" in result.lower() or "failure" in result.lower()

    def test_object_extraction_in_reason(self):
        """Test that object names are extracted in failure reasons."""
        action_log = [
            {"action": "pick up the laptop", "observation": "nothing found", "step": 1}
        ]
        result = extract_failure_reason(action_log)
        # The reason should mention the object or the action
        assert "laptop" in result.lower() or "pick" in result.lower()