"""
Contract tests for the Relevance Scorer module.

These tests verify the output schema and basic functionality of the
relevance scoring logic without requiring full integration with the
task bank or real trajectory data.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.retrieval.relevance_scorer import (
    _normalize_text,
    _tokenize,
    _jaccard_similarity,
    _calculate_relevance_score,
    score_trajectory_relevance,
    calculate_relevance_scores_for_cohort,
    run
)


class TestRelevanceScorerContract:
    """Contract tests for relevance scoring functions."""

    def test_normalize_text_lowercase(self):
        """Test that normalize_text converts to lowercase."""
        assert _normalize_text("HELLO WORLD") == "hello world"
        assert _normalize_text("HeLLo WoRLd") == "hello world"

    def test_normalize_text_removes_punctuation(self):
        """Test that normalize_text removes punctuation."""
        assert _normalize_text("hello, world!") == "hello world"
        assert _normalize_text("test-case_123") == "testcase 123"

    def test_normalize_text_strips_whitespace(self):
        """Test that normalize_text strips leading/trailing whitespace."""
        assert _normalize_text("  hello world  ") == "hello world"
        assert _normalize_text("\n\ttest\n") == "test"

    def test_tokenize_basic(self):
        """Test basic tokenization."""
        tokens = _tokenize("hello world test")
        assert tokens == ["hello", "world", "test"]
        assert isinstance(tokens, list)

    def test_jaccard_similarity_identical_sets(self):
        """Test Jaccard similarity with identical sets."""
        set_a = {"a", "b", "c"}
        set_b = {"a", "b", "c"}
        assert _jaccard_similarity(set_a, set_b) == 1.0

    def test_jaccard_similarity_disjoint_sets(self):
        """Test Jaccard similarity with disjoint sets."""
        set_a = {"a", "b"}
        set_b = {"c", "d"}
        assert _jaccard_similarity(set_a, set_b) == 0.0

    def test_jaccard_similarity_partial_overlap(self):
        """Test Jaccard similarity with partial overlap."""
        set_a = {"a", "b", "c"}
        set_b = {"b", "c", "d"}
        # Intersection: {b, c} (2), Union: {a, b, c, d} (4)
        assert _jaccard_similarity(set_a, set_b) == 0.5

    def test_jaccard_similarity_empty_sets(self):
        """Test Jaccard similarity with empty sets."""
        assert _jaccard_similarity(set(), set()) == 0.0
        assert _jaccard_similarity({"a"}, set()) == 0.0
        assert _jaccard_similarity(set(), {"a"}) == 0.0

    @patch("src.retrieval.relevance_scorer.get_task_definition")
    def test_calculate_relevance_score_with_mock_task(self, mock_get_task):
        """Test relevance score calculation with mocked task definition."""
        mock_task = {
            "description": "pick up the apple and put it in the basket",
            "goal": "put apple in basket",
            "objects": ["apple", "basket"]
        }
        mock_get_task.return_value = mock_task

        score = _calculate_relevance_score("failed to pick up apple", "task_001")

        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)
        # Should have some similarity due to "apple" overlap
        assert score > 0.0

    @patch("src.retrieval.relevance_scorer.get_task_definition")
    def test_calculate_relevance_score_no_task(self, mock_get_task):
        """Test relevance score calculation when task not found."""
        mock_get_task.return_value = None

        score = _calculate_relevance_score("some failure", "task_001")

        assert score == 0.0

    @patch("src.retrieval.relevance_scorer.get_task_definition")
    def test_score_trajectory_relevance_with_valid_trajectory(self, mock_get_task):
        """Test scoring a valid trajectory."""
        mock_task = {
            "description": "clean the sink",
            "goal": "clean sink",
            "objects": ["sink"]
        }
        mock_get_task.return_value = mock_task

        trajectory = {
            "id": "traj_001",
            "task_id": "task_001",
            "failure_signal": "failed to clean sink"
        }

        score = score_trajectory_relevance(trajectory)

        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)

    def test_score_trajectory_relevance_missing_task_id(self):
        """Test scoring a trajectory missing task_id."""
        trajectory = {
            "id": "traj_001",
            "failure_signal": "some failure"
        }

        with pytest.raises(ValueError, match="missing 'task_id'"):
            score_trajectory_relevance(trajectory)

    def test_calculate_relevance_scores_for_cohort_basic(self):
        """Test batch scoring of multiple trajectories."""
        trajectories = [
            {
                "id": "traj_001",
                "task_id": "task_001",
                "failure_signal": "failed to pick up apple"
            },
            {
                "id": "traj_002",
                "task_id": "task_002",
                "failure_signal": "failed to open drawer"
            }
        ]

        with patch("src.retrieval.relevance_scorer.get_task_definition") as mock_get_task:
            mock_get_task.return_value = {
                "description": "test task",
                "goal": "test goal",
                "objects": ["test"]
            }

            scored = calculate_relevance_scores_for_cohort(trajectories)

            assert len(scored) == len(trajectories)
            for traj in scored:
                assert "relevance_score" in traj
                assert 0.0 <= traj["relevance_score"] <= 1.0

    def test_calculate_relevance_scores_for_cohort_with_output_file(self):
        """Test batch scoring with file output."""
        trajectories = [
            {
                "id": "traj_001",
                "task_id": "task_001",
                "failure_signal": "test failure"
            }
        ]

        with patch("src.retrieval.relevance_scorer.get_task_definition") as mock_get_task:
            mock_get_task.return_value = {
                "description": "test",
                "goal": "test",
                "objects": []
            }

            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                scored = calculate_relevance_scores_for_cohort(
                    trajectories,
                    output_path=tmp_path
                )

                # Verify file was created
                assert os.path.exists(tmp_path)

                # Verify file content
                with open(tmp_path, 'r') as f:
                    saved_data = json.load(f)

                assert len(saved_data) == 1
                assert saved_data[0]["relevance_score"] is not None
            finally:
                os.unlink(tmp_path)

    @patch("src.retrieval.relevance_scorer.calculate_relevance_scores_for_cohort")
    @patch("builtins.open")
    @patch("os.path.exists")
    def test_run_function_basic(self, mock_exists, mock_open, mock_calc_scores):
        """Test the main run function."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = '[]'
        mock_calc_scores.return_value = [{"relevance_score": 0.5}]

        stats = run(
            input_path="data/raw/test.json",
            output_path="data/derived/test_scores.json",
            cohort_name="test"
        )

        assert "cohort" in stats
        assert "mean_relevance_score" in stats
        assert stats["cohort"] == "test"

    def test_run_function_missing_input_file(self):
        """Test run function with missing input file."""
        with pytest.raises(FileNotFoundError):
            run(
                input_path="nonexistent.json",
                output_path="output.json",
                cohort_name="test"
            )

    def test_run_function_invalid_json_format(self):
        """Test run function with invalid JSON format."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
            f.write('{"not": "a list"}')
            tmp_path = f.name

        try:
            with pytest.raises(ValueError, match="Expected list"):
                run(
                    input_path=tmp_path,
                    output_path="output.json",
                    cohort_name="test"
                )
        finally:
            os.unlink(tmp_path)
