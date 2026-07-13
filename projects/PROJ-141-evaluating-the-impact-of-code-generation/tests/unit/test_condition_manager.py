"""
Unit tests for the Condition Manager.

These tests verify the condition switching logic, LLM assistant state management,
and logging behavior of the ConditionManager class.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from experiment.condition_manager import ConditionManager, ConditionError


class TestConditionManager(unittest.TestCase):
    """Test cases for ConditionManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.participant_id = "test_participant_001"
        self.session_id = "test_session_001"
        self.manager = ConditionManager(self.participant_id, self.session_id)

    def test_initialization(self):
        """Test that ConditionManager initializes correctly."""
        self.assertIsNone(self.manager.current_condition)
        self.assertEqual(self.manager.participant_id, self.participant_id)
        self.assertEqual(self.manager.session_id, self.session_id)
        self.assertEqual(len(self.manager.get_switch_history()), 0)

    def test_initialize_condition_llm_assisted(self):
        """Test initializing with LLM-assisted condition."""
        result = self.manager.initialize_condition("llm_assisted")
        
        self.assertEqual(result, "llm_assisted")
        self.assertEqual(self.manager.current_condition, "llm_assisted")
        self.assertTrue(self.manager.is_llm_assistant_enabled())

    def test_initialize_condition_baseline(self):
        """Test initializing with baseline condition."""
        result = self.manager.initialize_condition("baseline")
        
        self.assertEqual(result, "baseline")
        self.assertEqual(self.manager.current_condition, "baseline")
        self.assertFalse(self.manager.is_llm_assistant_enabled())

    def test_initialize_invalid_condition(self):
        """Test that invalid condition raises ConditionError."""
        with self.assertRaises(ConditionError) as context:
            self.manager.initialize_condition("invalid_condition")
        
        self.assertIn("Invalid condition", str(context.exception))

    def test_switch_condition_from_llm_to_baseline(self):
        """Test switching from LLM-assisted to baseline."""
        self.manager.initialize_condition("llm_assisted")
        
        new_condition, metadata = self.manager.switch_condition("baseline")
        
        self.assertEqual(new_condition, "baseline")
        self.assertEqual(self.manager.current_condition, "baseline")
        self.assertFalse(self.manager.is_llm_assistant_enabled())
        self.assertEqual(metadata["previous_condition"], "llm_assisted")
        self.assertEqual(metadata["new_condition"], "baseline")
        self.assertIn("llm_state_change", metadata)
        self.assertEqual(metadata["llm_state_change"]["status"], "disabled")

    def test_switch_condition_from_baseline_to_llm(self):
        """Test switching from baseline to LLM-assisted."""
        self.manager.initialize_condition("baseline")
        
        new_condition, metadata = self.manager.switch_condition("llm_assisted")
        
        self.assertEqual(new_condition, "llm_assisted")
        self.assertEqual(self.manager.current_condition, "llm_assisted")
        self.assertTrue(self.manager.is_llm_assistant_enabled())
        self.assertEqual(metadata["previous_condition"], "baseline")
        self.assertEqual(metadata["new_condition"], "llm_assisted")
        self.assertIn("llm_state_change", metadata)
        self.assertEqual(metadata["llm_state_change"]["status"], "enabled")

    def test_switch_to_same_condition_raises_error(self):
        """Test that switching to the same condition raises ConditionError."""
        self.manager.initialize_condition("llm_assisted")
        
        with self.assertRaises(ConditionError) as context:
            self.manager.switch_condition("llm_assisted")
        
        self.assertIn("Cannot switch to the same condition", str(context.exception))

    def test_switch_invalid_condition_raises_error(self):
        """Test that switching to an invalid condition raises ConditionError."""
        self.manager.initialize_condition("llm_assisted")
        
        with self.assertRaises(ConditionError) as context:
            self.manager.switch_condition("invalid")
        
        self.assertIn("Invalid condition", str(context.exception))

    def test_switch_history_tracking(self):
        """Test that switch history is properly tracked."""
        self.manager.initialize_condition("llm_assisted")
        
        self.assertEqual(len(self.manager.get_switch_history()), 0)
        
        self.manager.switch_condition("baseline")
        self.assertEqual(len(self.manager.get_switch_history()), 1)
        
        self.manager.switch_condition("llm_assisted")
        self.assertEqual(len(self.manager.get_switch_history()), 2)
        
        history = self.manager.get_switch_history()
        self.assertEqual(history[0]["from"], "llm_assisted")
        self.assertEqual(history[0]["to"], "baseline")
        self.assertEqual(history[1]["from"], "baseline")
        self.assertEqual(history[1]["to"], "llm_assisted")

    def test_validate_condition(self):
        """Test the validate_condition method."""
        self.assertTrue(self.manager.validate_condition("llm_assisted"))
        self.assertTrue(self.manager.validate_condition("baseline"))
        self.assertFalse(self.manager.validate_condition("invalid"))
        self.assertFalse(self.manager.validate_condition(""))

    def test_get_current_condition(self):
        """Test getting the current condition."""
        self.assertIsNone(self.manager.get_current_condition())
        
        self.manager.initialize_condition("llm_assisted")
        self.assertEqual(self.manager.get_current_condition(), "llm_assisted")
        
        self.manager.switch_condition("baseline")
        self.assertEqual(self.manager.get_current_condition(), "baseline")


if __name__ == "__main__":
    unittest.main()