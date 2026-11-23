"""
Integration tests for the Degraded Condition workflow.

These tests verify the end-to-end flow of generating degraded trajectories,
calculating relevance scores, and producing the expected output artifacts.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.conditions.degraded import run as run_degraded
from src.retrieval.relevance_scorer import run as run_scorer


class TestDegradedConditionIntegration:
    """Integration tests for degraded condition and relevance scoring."""

    def test_degraded_to_scorer_integration(self):
        """
        Test the integration between degraded condition generation and
        relevance scoring.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create mock degraded failures file
            degraded_path = os.path.join(tmp_dir, "degraded_failures.json")
            scored_path = os.path.join(tmp_dir, "degraded_scores.json")

            # Create mock degraded trajectory data
            mock_trajectories = [
                {
                    "id": "deg_001",
                    "task_id": "task_001",
                    "failure_signal": "failed to pick up object",
                    "trajectory": [{"action": "noop", "state": "failed"}]
                },
                {
                    "id": "deg_002",
                    "task_id": "task_002",
                    "failure_signal": "failed to open container",
                    "trajectory": [{"action": "noop", "state": "failed"}]
                }
            ]

            with open(degraded_path, 'w') as f:
                json.dump(mock_trajectories, f)

            # Mock the task bank to return valid task definitions
            with patch("src.retrieval.relevance_scorer.get_task_definition") as mock_get_task:
                mock_get_task.return_value = {
                    "description": "test task description",
                    "goal": "test goal",
                    "objects": ["object", "container"]
                }

                # Run the relevance scorer on the degraded trajectories
                stats = run_scorer(
                    input_path=degraded_path,
                    output_path=scored_path,
                    cohort_name="degraded"
                )

                # Verify output file exists
                assert os.path.exists(scored_path)

                # Verify stats are returned
                assert stats["cohort"] == "degraded"
                assert stats["num_trajectories"] == 2
                assert "mean_relevance_score" in stats

                # Verify scored data
                with open(scored_path, 'r') as f:
                    scored_data = json.load(f)

                assert len(scored_data) == 2
                for traj in scored_data:
                    assert "relevance_score" in traj
                    assert 0.0 <= traj["relevance_score"] <= 1.0

    def test_degraded_condition_with_real_task_bank_structure(self):
        """
        Test degraded condition workflow with a more realistic task bank structure.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            degraded_path = os.path.join(tmp_dir, "degraded_failures.json")
            scored_path = os.path.join(tmp_dir, "degraded_scores.json")

            # Create mock trajectories with varied failure signals
            mock_trajectories = [
                {
                    "id": "deg_001",
                    "task_id": "pick_coffee_from_kitchen",
                    "failure_signal": "failed to pick up coffee mug from counter",
                    "trajectory": [{"action": "goto counter", "state": "failed"}]
                },
                {
                    "id": "deg_002",
                    "task_id": "put_coffee_in_basket",
                    "failure_signal": "failed to place coffee in basket",
                    "trajectory": [{"action": "put coffee", "state": "failed"}]
                }
            ]

            with open(degraded_path, 'w') as f:
                json.dump(mock_trajectories, f)

            # Mock task definitions that match the task IDs
            def mock_get_task_definition(task_id):
                if task_id == "pick_coffee_from_kitchen":
                    return {
                        "description": "Pick up the coffee mug from the kitchen counter",
                        "goal": "pick up coffee",
                        "objects": ["coffee", "mug", "counter", "kitchen"]
                    }
                elif task_id == "put_coffee_in_basket":
                    return {
                        "description": "Put the coffee mug in the basket",
                        "goal": "put coffee in basket",
                        "objects": ["coffee", "mug", "basket"]
                    }
                return None

            with patch("src.retrieval.relevance_scorer.get_task_definition", side_effect=mock_get_task_definition):
                stats = run_scorer(
                    input_path=degraded_path,
                    output_path=scored_path,
                    cohort_name="degraded"
                )

                # Verify that scores were calculated
                assert stats["num_successfully_scored"] == 2
                assert stats["mean_relevance_score"] > 0.0  # Should have some similarity

                # Verify the output file content
                with open(scored_path, 'r') as f:
                    scored_data = json.load(f)

                # Check that each trajectory has a relevance score
                scores = [t["relevance_score"] for t in scored_data]
                assert all(0.0 <= s <= 1.0 for s in scores)

    def test_degraded_scorer_handles_missing_task_definitions(self):
        """
        Test that the scorer gracefully handles missing task definitions.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            degraded_path = os.path.join(tmp_dir, "degraded_failures.json")
            scored_path = os.path.join(tmp_dir, "degraded_scores.json")

            mock_trajectories = [
                {
                    "id": "deg_001",
                    "task_id": "unknown_task",
                    "failure_signal": "failed to do something",
                    "trajectory": []
                }
            ]

            with open(degraded_path, 'w') as f:
                json.dump(mock_trajectories, f)

            # Mock task bank to return None for all tasks
            with patch("src.retrieval.relevance_scorer.get_task_definition", return_value=None):
                stats = run_scorer(
                    input_path=degraded_path,
                    output_path=scored_path,
                    cohort_name="degraded"
                )

                # Should still complete but with 0.0 scores
                assert stats["num_successfully_scored"] == 1
                assert stats["mean_relevance_score"] == 0.0

                with open(scored_path, 'r') as f:
                    scored_data = json.load(f)

                assert scored_data[0]["relevance_score"] == 0.0

    def test_end_to_end_degraded_workflow(self):
        """
        Test the complete workflow from degraded generation to scoring.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Simulate the degraded condition output
            degraded_path = os.path.join(tmp_dir, "degraded_failures.json")
            scored_path = os.path.join(tmp_dir, "degraded_scores.json")
            stats_path = os.path.join(tmp_dir, "degraded_stats.json")

            # Create mock degraded data
            mock_degraded = [
                {
                    "id": f"deg_{i:03d}",
                    "task_id": f"task_{i:03d}",
                    "failure_signal": f"failed to complete step {i}",
                    "trajectory": [{"action": "noop", "state": "failed"}]
                }
                for i in range(10)
            ]

            with open(degraded_path, 'w') as f:
                json.dump(mock_degraded, f)

            # Mock task definitions
            def mock_get_task(task_id):
                task_num = task_id.split("_")[1]
                return {
                    "description": f"Task {task_num} description",
                    "goal": f"complete task {task_num}",
                    "objects": [f"object_{task_num}"]
                }

            with patch("src.retrieval.relevance_scorer.get_task_definition", side_effect=mock_get_task):
                # Run scorer
                scorer_stats = run_scorer(
                    input_path=degraded_path,
                    output_path=scored_path,
                    cohort_name="degraded"
                )

                # Verify scorer output
                assert os.path.exists(scored_path)
                assert scorer_stats["num_trajectories"] == 10

                # Verify scored data
                with open(scored_path, 'r') as f:
                    scored_data = json.load(f)

                assert len(scored_data) == 10
                assert all("relevance_score" in t for t in scored_data)

                # Save stats (simulating T024)
                with open(stats_path, 'w') as f:
                    json.dump(scorer_stats, f, indent=2)

                assert os.path.exists(stats_path)