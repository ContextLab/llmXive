"""
Unit tests for the ConsensusGapEvaluator logic.
Tests cover gap calculation, evaluation results, and edge cases.
"""
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.evaluator import EvaluationResult, ConsensusGapEvaluator, calculate_consensus_gap_scores
from models.entities import ConflictTrajectory, SocioCognitiveStateType
from config import set_all_seeds


class TestEvaluationResult(unittest.TestCase):
    def test_creation(self):
        """Test creating an EvaluationResult."""
        result = EvaluationResult(
            trajectory_id="traj_001",
            condition="Adapter",
            consensus_gap_score=0.45,
            ideal_gap=0.0,
            current_gap=0.45
        )
        
        self.assertEqual(result.trajectory_id, "traj_001")
        self.assertEqual(result.condition, "Adapter")
        self.assertEqual(result.consensus_gap_score, 0.45)
        self.assertEqual(result.ideal_gap, 0.0)
        self.assertEqual(result.current_gap, 0.45)

    def test_serialization(self):
        """Test that EvaluationResult can be serialized to dict."""
        result = EvaluationResult(
            trajectory_id="traj_002",
            condition="Static",
            consensus_gap_score=0.62,
            ideal_gap=0.0,
            current_gap=0.62
        )
        
        result_dict = result.to_dict()
        
        self.assertEqual(result_dict["trajectory_id"], "traj_002")
        self.assertEqual(result_dict["condition"], "Static")
        self.assertEqual(result_dict["consensus_gap_score"], 0.62)


class TestConsensusGapEvaluator(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        set_all_seeds(42)
        self.evaluator = ConsensusGapEvaluator()
        
        # Create sample trajectory
        self.trajectory = ConflictTrajectory(
            trajectory_id="traj_001",
            turns=[
                {
                    "turn_number": 1,
                    "speaker": "Participant A",
                    "text": "I feel my cultural identity is being disrespected.",
                    "socio_cognitive_state": SocioCognitiveStateType.HIGH_EMOTIONAL_REACTIVITY
                },
                {
                    "turn_number": 2,
                    "speaker": "Participant B",
                    "text": "I understand your concern. Let's find a solution.",
                    "socio_cognitive_state": SocioCognitiveStateType.NEUTRAL_MONITORING
                },
                {
                    "turn_number": 3,
                    "speaker": "Participant A",
                    "text": "Thank you for listening. I appreciate that.",
                    "socio_cognitive_state": SocioCognitiveStateType.LOW_EMOTIONAL_REACTIVITY
                }
            ],
            metadata={
                "emotional_reactivity": "high",
                "cultural_identity": "diverse"
            }
        )

        self.ideal_resolution_text = "Both parties have reached a mutual understanding and agreed on a culturally sensitive solution that respects both perspectives."

    def test_gap_calculation_range(self):
        """Test that gap scores are within expected range [0, 1]."""
        # Create a trajectory with poor resolution
        poor_trajectory = ConflictTrajectory(
            trajectory_id="traj_poor",
            turns=[
                {
                    "turn_number": 1,
                    "speaker": "A",
                    "text": "You are wrong!",
                    "socio_cognitive_state": SocioCognitiveStateType.HIGH_EMOTIONAL_REACTIVITY
                },
                {
                    "turn_number": 2,
                    "speaker": "B",
                    "text": "No, you are wrong!",
                    "socio_cognitive_state": SocioCognitiveStateType.HIGH_EMOTIONAL_REACTIVITY
                }
            ],
            metadata={"emotional_reactivity": "high", "cultural_identity": "diverse"}
        )
        
        result = self.evaluator.evaluate(poor_trajectory, self.ideal_resolution_text)
        
        self.assertGreaterEqual(result.consensus_gap_score, 0.0)
        self.assertLessEqual(result.consensus_gap_score, 1.0)

    def test_gap_calculation_for_good_resolution(self):
        """Test that good resolution results in lower gap scores."""
        good_trajectory = ConflictTrajectory(
            trajectory_id="traj_good",
            turns=[
                {
                    "turn_number": 1,
                    "speaker": "A",
                    "text": "I have a concern about the cultural context.",
                    "socio_cognitive_state": SocioCognitiveStateType.NEUTRAL_MONITORING
                },
                {
                    "turn_number": 2,
                    "speaker": "B",
                    "text": "Let's address that concern together.",
                    "socio_cognitive_state": SocioCognitiveStateType.NEUTRAL_MONITORING
                },
                {
                    "turn_number": 3,
                    "speaker": "A",
                    "text": "Great, I think we have a solution that works for everyone.",
                    "socio_cognitive_state": SocioCognitiveStateType.LOW_EMOTIONAL_REACTIVITY
                }
            ],
            metadata={"emotional_reactivity": "low", "cultural_identity": "diverse"}
        )
        
        result = self.evaluator.evaluate(good_trajectory, self.ideal_resolution_text)
        
        # Good resolution should have lower gap than poor resolution
        poor_trajectory = ConflictTrajectory(
            trajectory_id="traj_poor",
            turns=[
                {
                    "turn_number": 1,
                    "speaker": "A",
                    "text": "This is unacceptable!",
                    "socio_cognitive_state": SocioCognitiveStateType.HIGH_EMOTIONAL_REACTIVITY
                },
                {
                    "turn_number": 2,
                    "speaker": "B",
                    "text": "I don't care about your feelings!",
                    "socio_cognitive_state": SocioCognitiveStateType.HIGH_EMOTIONAL_REACTIVITY
                }
            ],
            metadata={"emotional_reactivity": "high", "cultural_identity": "diverse"}
        )
        
        poor_result = self.evaluator.evaluate(poor_trajectory, self.ideal_resolution_text)
        
        self.assertLess(result.consensus_gap_score, poor_result.consensus_gap_score)

    def test_empty_trajectory(self):
        """Test evaluation of an empty trajectory."""
        empty_trajectory = ConflictTrajectory(
            trajectory_id="traj_empty",
            turns=[],
            metadata={"emotional_reactivity": "low", "cultural_identity": "diverse"}
        )
        
        result = self.evaluator.evaluate(empty_trajectory, self.ideal_resolution_text)
        
        # Should handle empty trajectory gracefully
        self.assertIsNotNone(result)
        self.assertEqual(result.trajectory_id, "traj_empty")

    def test_evaluation_result_structure(self):
        """Test that evaluation result contains all required fields."""
        result = self.evaluator.evaluate(self.trajectory, self.ideal_resolution_text)
        
        self.assertTrue(hasattr(result, 'trajectory_id'))
        self.assertTrue(hasattr(result, 'condition'))
        self.assertTrue(hasattr(result, 'consensus_gap_score'))
        self.assertTrue(hasattr(result, 'ideal_gap'))
        self.assertTrue(hasattr(result, 'current_gap'))
        self.assertTrue(hasattr(result, 'timestamp'))

    def test_batch_evaluation(self):
        """Test evaluating multiple trajectories at once."""
        trajectories = [
            ConflictTrajectory(
                trajectory_id=f"traj_{i}",
                turns=[
                    {
                        "turn_number": 1,
                        "speaker": "A",
                        "text": f"Turn 1 of trajectory {i}",
                        "socio_cognitive_state": SocioCognitiveStateType.NEUTRAL_MONITORING
                    }
                ],
                metadata={"emotional_reactivity": "low", "cultural_identity": "diverse"}
            )
            for i in range(3)
        ]
        
        results = self.evaluator.evaluate_batch(trajectories, self.ideal_resolution_text)
        
        self.assertEqual(len(results), 3)
        for i, result in enumerate(results):
            self.assertEqual(result.trajectory_id, f"traj_{i}")

    def test_ideal_resolution_similarity(self):
        """Test that similarity to ideal resolution affects gap score."""
        # Create a trajectory that closely matches ideal resolution text
        matching_trajectory = ConflictTrajectory(
            trajectory_id="traj_match",
            turns=[
                {
                    "turn_number": 1,
                    "speaker": "A",
                    "text": "I feel my cultural identity is being respected.",
                    "socio_cognitive_state": SocioCognitiveStateType.NEUTRAL_MONITORING
                },
                {
                    "turn_number": 2,
                    "speaker": "B",
                    "text": "I understand and appreciate your perspective.",
                    "socio_cognitive_state": SocioCognitiveStateType.NEUTRAL_MONITORING
                },
                {
                    "turn_number": 3,
                    "speaker": "A",
                    "text": "We have reached a mutual understanding and agreed on a culturally sensitive solution that respects both perspectives.",
                    "socio_cognitive_state": SocioCognitiveStateType.LOW_EMOTIONAL_REACTIVITY
                }
            ],
            metadata={"emotional_reactivity": "low", "cultural_identity": "diverse"}
        )
        
        result = self.evaluator.evaluate(matching_trajectory, self.ideal_resolution_text)
        
        # Should have lower gap score due to text similarity
        self.assertLess(result.consensus_gap_score, 0.5)  # Heuristic threshold

    def test_special_characters_in_text(self):
        """Test evaluation with special characters in text."""
        special_trajectory = ConflictTrajectory(
            trajectory_id="traj_special",
            turns=[
                {
                    "turn_number": 1,
                    "speaker": "A",
                    "text": "What about 'quotes' and \"double quotes\"?",
                    "socio_cognitive_state": SocioCognitiveStateType.NEUTRAL_MONITORING
                },
                {
                    "turn_number": 2,
                    "speaker": "B",
                    "text": "Let's discuss this [issue] without (confusion).",
                    "socio_cognitive_state": SocioCognitiveStateType.NEUTRAL_MONITORING
                }
            ],
            metadata={"emotional_reactivity": "low", "cultural_identity": "diverse"}
        )
        
        result = self.evaluator.evaluate(special_trajectory, self.ideal_resolution_text)
        
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result.consensus_gap_score, 0.0)


class TestCalculateConsensusGapScores(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        set_all_seeds(42)
        self.ideal_text = "Mutual understanding reached."
        
        self.trajectories = [
            ConflictTrajectory(
                trajectory_id="traj_1",
                turns=[
                    {
                        "turn_number": 1,
                        "speaker": "A",
                        "text": "I agree.",
                        "socio_cognitive_state": SocioCognitiveStateType.LOW_EMOTIONAL_REACTIVITY
                    }
                ],
                metadata={"emotional_reactivity": "low", "cultural_identity": "diverse"}
            ),
            ConflictTrajectory(
                trajectory_id="traj_2",
                turns=[
                    {
                        "turn_number": 1,
                        "speaker": "A",
                        "text": "I disagree.",
                        "socio_cognitive_state": SocioCognitiveStateType.HIGH_EMOTIONAL_REACTIVITY
                    }
                ],
                metadata={"emotional_reactivity": "high", "cultural_identity": "diverse"}
            )
        ]

    def test_function_returns_list(self):
        """Test that calculate_consensus_gap_scores returns a list."""
        results = calculate_consensus_gap_scores(self.trajectories, self.ideal_text)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)

    def test_function_returns_evaluation_results(self):
        """Test that results are EvaluationResult instances."""
        results = calculate_consensus_gap_scores(self.trajectories, self.ideal_text)
        
        for result in results:
            self.assertIsInstance(result, EvaluationResult)

    def test_function_handles_empty_list(self):
        """Test that function handles empty trajectory list."""
        results = calculate_consensus_gap_scores([], self.ideal_text)
        
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
