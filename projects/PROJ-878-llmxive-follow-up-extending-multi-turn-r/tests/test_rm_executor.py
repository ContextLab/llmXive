"""
Unit tests for code/rm_executor.py focusing on hard turn limit enforcement
and censored data flagging.
"""
import unittest
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.graph_utils import graph_from_dict
from rm_executor import ReflectiveMaskingExecutor, RunResult

class TestTurnLimitEnforcement(unittest.TestCase):
    """Tests for hard turn limit (50 turns) enforcement."""

    def setUp(self):
        """Set up test fixtures."""
        self.max_turns = 50
        self.executor = ReflectiveMaskingExecutor(
            model_path="dummy_model",
            device="cpu",
            max_turns=self.max_turns
        )
        # Mock the model to avoid actual loading
        self.executor.model = MagicMock()
        self.executor.tokenizer = MagicMock()

        # Create a dummy graph for testing
        self.test_graph = graph_from_dict({
            "nodes": ["A", "B", "C", "D"],
            "edges": [("A", "B"), ("B", "C"), ("C", "D")]
        })

    @patch.object(ReflectiveMaskingExecutor, '_run_single_turn')
    def test_enforces_hard_turn_limit(self, mock_turn):
        """Test that execution stops exactly at max_turns if not converged."""
        # Mock turn to always return "continue" status
        mock_turn.return_value = ({"path": ["A", "B", "C", "D"]}, "continue", 0.0)

        result = self.executor.run(self.test_graph, ground_truth_path=["A", "B", "C", "D"])

        # Verify execution stopped at the limit
        self.assertEqual(mock_turn.call_count, self.max_turns)
        self.assertEqual(result.turns_to_converge, self.max_turns)
        self.assertEqual(result.convergence_status, "failure")
        self.assertTrue(result.is_censored)

    @patch.object(ReflectiveMaskingExecutor, '_run_single_turn')
    def test_converges_before_limit(self, mock_turn):
        """Test that execution stops early if convergence is achieved."""
        # Mock first 10 turns to continue, 11th to converge
        def turn_side_effect(*args, **kwargs):
            if turn_side_effect.call_count < 10:
                turn_side_effect.call_count += 1
                return ({"path": ["A", "B"]}, "continue", 0.0)
            else:
                return ({"path": ["A", "B", "C", "D"]}, "converged", 1.0)
        turn_side_effect.call_count = 0

        mock_turn.side_effect = turn_side_effect

        result = self.executor.run(self.test_graph, ground_truth_path=["A", "B", "C", "D"])

        # Verify early stop
        self.assertEqual(mock_turn.call_count, 10)
        self.assertEqual(result.turns_to_converge, 10)
        self.assertEqual(result.convergence_status, "converged")
        self.assertFalse(result.is_censored)

    @patch.object(ReflectiveMaskingExecutor, '_run_single_turn')
    def test_censored_flag_set_on_limit(self, mock_turn):
        """Test that is_censored flag is set when limit is hit."""
        mock_turn.return_value = ({"path": ["A"]}, "continue", 0.0)

        result = self.executor.run(self.test_graph, ground_truth_path=["A", "B"])

        self.assertTrue(result.is_censored)
        self.assertEqual(result.convergence_status, "failure")

    @patch.object(ReflectiveMaskingExecutor, '_run_single_turn')
    def test_censored_flag_false_on_convergence(self, mock_turn):
        """Test that is_censored flag is not set when converged early."""
        mock_turn.return_value = ({"path": ["A", "B"]}, "converged", 1.0)

        result = self.executor.run(self.test_graph, ground_truth_path=["A", "B"])

        self.assertFalse(result.is_censored)
        self.assertEqual(result.convergence_status, "converged")

    def test_default_max_turns_is_50(self):
        """Test that default max_turns is 50 if not specified."""
        executor = ReflectiveMaskingExecutor(
            model_path="dummy_model",
            device="cpu"
        )
        self.assertEqual(executor.max_turns, 50)

    @patch.object(ReflectiveMaskingExecutor, '_run_single_turn')
    def test_custom_max_turns_respected(self, mock_turn):
        """Test that custom max_turns parameter is respected."""
        custom_limit = 25
        executor = ReflectiveMaskingExecutor(
            model_path="dummy_model",
            device="cpu",
            max_turns=custom_limit
        )
        executor.model = MagicMock()
        executor.tokenizer = MagicMock()

        mock_turn.return_value = ({"path": ["A"]}, "continue", 0.0)

        result = executor.run(self.test_graph, ground_truth_path=["A", "B"])

        self.assertEqual(mock_turn.call_count, custom_limit)
        self.assertEqual(result.turns_to_converge, custom_limit)

class TestCensoredDataHandling(unittest.TestCase):
    """Tests for censored data flagging and reporting."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = ReflectiveMaskingExecutor(
            model_path="dummy_model",
            device="cpu",
            max_turns=50
        )
        self.executor.model = MagicMock()
        self.executor.tokenizer = MagicMock()

        self.test_graph = graph_from_dict({
            "nodes": ["X", "Y", "Z"],
            "edges": [("X", "Y"), ("Y", "Z")]
        })

    @patch.object(ReflectiveMaskingExecutor, '_run_single_turn')
    def test_censored_result_includes_turn_limit(self, mock_turn):
        """Test that censored results record the turn limit as turns_to_converge."""
        mock_turn.return_value = ({"path": ["X"]}, "continue", 0.0)

        result = self.executor.run(self.test_graph, ground_truth_path=["X", "Y", "Z"])

        self.assertEqual(result.turns_to_converge, 50)
        self.assertTrue(result.is_censored)

    @patch.object(ReflectiveMaskingExecutor, '_run_single_turn')
    def test_censored_result_has_failure_status(self, mock_turn):
        """Test that censored results have 'failure' convergence status."""
        mock_turn.return_value = ({"path": ["X"]}, "continue", 0.0)

        result = self.executor.run(self.test_graph, ground_truth_path=["X", "Y", "Z"])

        self.assertEqual(result.convergence_status, "failure")

    @patch.object(ReflectiveMaskingExecutor, '_run_single_turn')
    def test_non_censored_result_has_converged_status(self, mock_turn):
        """Test that non-censored results have 'converged' status."""
        mock_turn.return_value = ({"path": ["X", "Y", "Z"]}, "converged", 1.0)

        result = self.executor.run(self.test_graph, ground_truth_path=["X", "Y", "Z"])

        self.assertEqual(result.convergence_status, "converged")
        self.assertFalse(result.is_censored)

    def test_run_result_censored_field_exists(self):
        """Test that RunResult has is_censored field."""
        result = RunResult(
            instance_id="test_001",
            turns_to_converge=10,
            convergence_status="converged",
            path_coverage=1.0,
            divergence=0.0,
            is_censored=False
        )
        self.assertFalse(result.is_censored)

        result_censored = RunResult(
            instance_id="test_002",
            turns_to_converge=50,
            convergence_status="failure",
            path_coverage=0.5,
            divergence=0.5,
            is_censored=True
        )
        self.assertTrue(result_censored.is_censored)

class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases in turn limit enforcement."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = ReflectiveMaskingExecutor(
            model_path="dummy_model",
            device="cpu",
            max_turns=50
        )
        self.executor.model = MagicMock()
        self.executor.tokenizer = MagicMock()

        self.test_graph = graph_from_dict({
            "nodes": ["A"],
            "edges": []
        })

    @patch.object(ReflectiveMaskingExecutor, '_run_single_turn')
    def test_zero_turns_convergence(self, mock_turn):
        """Test convergence at turn 0 (already solved)."""
        mock_turn.return_value = ({"path": ["A"]}, "converged", 1.0)

        result = self.executor.run(self.test_graph, ground_truth_path=["A"])

        self.assertEqual(result.turns_to_converge, 0)
        self.assertFalse(result.is_censored)
        self.assertEqual(result.convergence_status, "converged")

    @patch.object(ReflectiveMaskingExecutor, '_run_single_turn')
    def test_max_turns_equals_one(self, mock_turn):
        """Test with max_turns=1."""
        executor = ReflectiveMaskingExecutor(
            model_path="dummy_model",
            device="cpu",
            max_turns=1
        )
        executor.model = MagicMock()
        executor.tokenizer = MagicMock()

        mock_turn.return_value = ({"path": ["A"]}, "continue", 0.0)

        result = executor.run(self.test_graph, ground_truth_path=["A"])

        self.assertEqual(mock_turn.call_count, 1)
        self.assertEqual(result.turns_to_converge, 1)
        self.assertTrue(result.is_censored)
        self.assertEqual(result.convergence_status, "failure")


if __name__ == "__main__":
    unittest.main()