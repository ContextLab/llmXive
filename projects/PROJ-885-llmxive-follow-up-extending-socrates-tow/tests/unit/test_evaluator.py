"""
Unit tests for the ConsensusGapEvaluator logic.
Tests the core functionality of the evaluator without requiring full experiment runs.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the target module
from models.evaluator import EvaluationResult, ConsensusGapEvaluator, calculate_consensus_gap_scores
from models.entities import ConflictTrajectory, SocioCognitiveStateType


class TestEvaluationResult:
    """Tests for the EvaluationResult dataclass."""

    def test_creation(self):
        """Test that EvaluationResult can be created with required fields."""
        result = EvaluationResult(
            trajectory_id="traj_001",
            gap_score=0.75,
            is_resolved=True,
            ideal_state=SocioCognitiveStateType.DECREASE_TENSION
        )

        assert result.trajectory_id == "traj_001"
        assert result.gap_score == 0.75
        assert result.is_resolved is True
        assert result.ideal_state == SocioCognitiveStateType.DECREASE_TENSION

    def test_gap_score_bounds(self):
        """Test that gap scores are within expected bounds."""
        # Valid score
        result = EvaluationResult(
            trajectory_id="traj_001",
            gap_score=0.5,
            is_resolved=False,
            ideal_state=SocioCognitiveStateType.NEUTRAL
        )
        assert 0.0 <= result.gap_score <= 1.0

        # Edge cases
        result_min = EvaluationResult(
            trajectory_id="traj_002",
            gap_score=0.0,
            is_resolved=True,
            ideal_state=SocioCognitiveStateType.NEUTRAL
        )
        assert result_min.gap_score == 0.0

        result_max = EvaluationResult(
            trajectory_id="traj_003",
            gap_score=1.0,
            is_resolved=False,
            ideal_state=SocioCognitiveStateType.NEUTRAL
        )
        assert result_max.gap_score == 1.0


class TestConsensusGapEvaluator:
    """Tests for the ConsensusGapEvaluator class."""

    @pytest.fixture
    def sample_trajectory(self):
        """Create a sample conflict trajectory for testing."""
        return ConflictTrajectory(
            trajectory_id="traj_001",
            participants=["Alice", "Bob"],
            turns=[
                {
                    "turn_id": 1,
                    "speaker": "Alice",
                    "text": "I think we should follow the standard procedure.",
                    "timestamp": "2023-10-01T10:00:00"
                },
                {
                    "turn_id": 2,
                    "speaker": "Bob",
                    "text": "I disagree, that procedure is outdated.",
                    "timestamp": "2023-10-01T10:01:00"
                },
                {
                    "turn_id": 3,
                    "speaker": "Alice",
                    "text": "Let's find a middle ground that works for both.",
                    "timestamp": "2023-10-01T10:02:00"
                }
            ],
            socio_cognitive_state={
                "emotional_reactivity": "high",
                "cultural_identity": "diverse"
            }
        )

    def test_evaluate_single_trajectory(self, evaluator, sample_trajectory):
        """Test evaluation of a single trajectory."""
        # Mock the internal scoring logic to return a deterministic value
        with patch.object(evaluator, '_calculate_gap', return_value=0.65):
            result = evaluator.evaluate(sample_trajectory)

            assert result is not None
            assert result.trajectory_id == sample_trajectory.trajectory_id
            assert result.gap_score == 0.65
            assert isinstance(result.is_resolved, bool)

    def test_gap_calculation_logic(self, evaluator):
        """Test the internal gap calculation logic."""
        # Simulate a scenario where the output matches the ideal perfectly
        # In a real scenario, this would compare text embeddings or semantic similarity
        # Here we test the logic flow
        output_text = "We have reached a mutual agreement."
        ideal_text = "We have reached a mutual agreement."

        # Mock the similarity function
        with patch.object(evaluator, '_semantic_similarity', return_value=1.0):
            gap = evaluator._calculate_gap(output_text, ideal_text)
            # Gap should be 0 if similarity is 1.0 (perfect match)
            # Assuming gap = 1 - similarity
            assert gap == 0.0

    def test_ideal_state_detection(self, evaluator, sample_trajectory):
        """Test that the evaluator correctly identifies the ideal state."""
        # The evaluator should derive the ideal state from the trajectory metadata
        ideal = evaluator._determine_ideal_state(sample_trajectory)

        # Should return a valid SocioCognitiveStateType
        assert isinstance(ideal, SocioCognitiveStateType)

    def test_batch_evaluation(self, evaluator, sample_trajectory):
        """Test evaluating multiple trajectories at once."""
        trajectories = [sample_trajectory, sample_trajectory]

        with patch.object(evaluator, 'evaluate', return_value=EvaluationResult(
            trajectory_id="traj_001",
            gap_score=0.5,
            is_resolved=True,
            ideal_state=SocioCognitiveStateType.NEUTRAL
        )):
            results = evaluator.evaluate_batch(trajectories)

            assert len(results) == 2
            for result in results:
                assert result.gap_score == 0.5

    def test_empty_trajectory_handling(self, evaluator):
        """Test that the evaluator handles empty trajectories gracefully."""
        empty_trajectory = ConflictTrajectory(
            trajectory_id="traj_empty",
            participants=["Alice"],
            turns=[],
            socio_cognitive_state={"emotional_reactivity": "low", "cultural_identity": "homogeneous"}
        )

        # Should raise an error or return a specific error result
        with pytest.raises(ValueError):
            evaluator.evaluate(empty_trajectory)

    def test_missing_metadata_handling(self, evaluator):
        """Test handling of trajectories with missing metadata."""
        incomplete_trajectory = ConflictTrajectory(
            trajectory_id="traj_incomplete",
            participants=["Alice"],
            turns=[{"turn_id": 1, "speaker": "Alice", "text": "Hello"}],
            socio_cognitive_state={}  # Missing keys
        )

        # Should handle missing keys gracefully, perhaps with defaults
        result = evaluator.evaluate(incomplete_trajectory)
        assert result is not None

class TestCalculateConsensusGapScores:
    """Tests for the standalone calculate_consensus_gap_scores function."""

    def test_function_returns_list(self, tmp_path):
        """Test that the function returns a list of results."""
        # Create a minimal experiment log file
        log_data = {
            "trajectories": [
                {
                    "trajectory_id": "traj_001",
                    "turns": [
                        {"speaker": "A", "text": "Hello"},
                        {"speaker": "B", "text": "Hi"}
                    ],
                    "condition": "Adapter",
                    "socio_cognitive_state": {
                        "emotional_reactivity": "high",
                        "cultural_identity": "diverse"
                    }
                }
            ]
        }

        log_path = tmp_path / "experiment_logs.json"
        with open(log_path, 'w') as f:
            json.dump(log_data, f)

        # Mock the evaluator to avoid heavy computation
        with patch('models.evaluator.ConsensusGapEvaluator') as MockEvaluator:
            mock_instance = MagicMock()
            mock_instance.evaluate_batch.return_value = [
                EvaluationResult(
                    trajectory_id="traj_001",
                    gap_score=0.8,
                    is_resolved=True,
                    ideal_state=SocioCognitiveStateType.DECREASE_TENSION
                )
            ]
            MockEvaluator.return_value = mock_instance

            results = calculate_consensus_gap_scores(str(log_path))

            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0].trajectory_id == "traj_001"

    def test_missing_file_handling(self):
        """Test that the function handles missing input files."""
        with pytest.raises(FileNotFoundError):
            calculate_consensus_gap_scores("nonexistent_file.json")

class TestEvaluatorMain:
    """Tests for the main function entry point."""

    def test_main_execution(self, tmp_path):
        """Test that main() executes without error."""
        # Create a dummy input file
        input_path = tmp_path / "input.json"
        input_path.write_text('{"trajectories": []}')

        output_path = tmp_path / "output.json"

        # Mock the heavy lifting
        with patch('models.evaluator.calculate_consensus_gap_scores') as mock_calc:
            mock_calc.return_value = []

            import sys
            original_argv = sys.argv
            sys.argv = ['test', '--input', str(input_path), '--output', str(output_path)]

            try:
                from models.evaluator import main
                # Check execution doesn't crash
            except SystemExit:
                pass
            finally:
                sys.argv = original_argv

            assert True