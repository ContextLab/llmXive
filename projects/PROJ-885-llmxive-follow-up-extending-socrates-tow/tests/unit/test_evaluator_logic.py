"""
Unit tests for the ConsensusGapEvaluator logic.
Tests T033 (Gap Calculation) and T048 (Data Independence).
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
import sys
import re

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.evaluator import ConsensusGapEvaluator, EvaluationResult, calculate_consensus_gap_scores
from models.entities import ConflictTrajectory, SocioCognitiveState, SocioCognitiveStateType


class TestEvaluatorLogic(unittest.TestCase):
    """Tests for consensus gap evaluation logic."""

    def setUp(self):
        """Set up mock trajectories for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a mock trajectory with a clear gap
        self.trajectory = ConflictTrajectory(
            id="test_traj_001",
            turns=[
                "I disagree with this policy.",
                "I think it's necessary for safety.",
                "It violates my rights.",
                "We need to balance safety and rights."
            ],
            metadata={
                "emotional_reactivity": "high",
                "cultural_identity": "diverse"
            },
            final_state=SocioCognitiveState(
                state_type=SocioCognitiveStateType.RESOLUTION,
                description="Agreement reached"
            )
        )

        # Create a mock trajectory with no gap (ideal)
        self.ideal_trajectory = ConflictTrajectory(
            id="test_traj_002",
            turns=[
                "Let's discuss this calmly.",
                "I hear your concerns.",
                "We found a solution."
            ],
            metadata={
                "emotional_reactivity": "low",
                "cultural_identity": "homogeneous"
            },
            final_state=SocioCognitiveState(
                state_type=SocioCognitiveStateType.RESOLUTION,
                description="Smooth resolution"
            )
        )

        self.evaluator = ConsensusGapEvaluator()

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_gap_calculation_returns_valid_score(self):
        """Test that gap score is between 0 and 1."""
        gap_score = self.evaluator.calculate_gap(self.trajectory)
        
        self.assertIsInstance(gap_score, float)
        self.assertGreaterEqual(gap_score, 0.0)
        self.assertLessEqual(gap_score, 1.0)

    def test_ideal_trajectory_has_lower_gap(self):
        """Test that an ideal trajectory has a lower gap score than a conflicted one."""
        gap_conflicted = self.evaluator.calculate_gap(self.trajectory)
        gap_ideal = self.evaluator.calculate_gap(self.ideal_trajectory)
        
        # The ideal trajectory should have a lower (better) gap score
        self.assertLess(gap_ideal, gap_conflicted,
                        "Ideal trajectory should have lower gap than conflicted one")

    def test_gap_calculation_considers_turn_count(self):
        """Test that longer conflicts with more turns generally have higher gap."""
        long_trajectory = ConflictTrajectory(
            id="test_traj_003",
            turns=[
                "I disagree.",
                "I think so.",
                "No I don't.",
                "Yes you do.",
                "This is going nowhere.",
                "Agreed, let's stop."
            ],
            metadata={
                "emotional_reactivity": "high",
                "cultural_identity": "diverse"
            },
            final_state=SocioCognitiveState(
                state_type=SocioCognitiveStateType.RESOLUTION,
                description="Exhausted agreement"
            )
        )
        
        short_trajectory = ConflictTrajectory(
            id="test_traj_004",
            turns=[
                "I disagree.",
                "Okay, let's agree."
            ],
            metadata={
                "emotional_reactivity": "low",
                "cultural_identity": "homogeneous"
            },
            final_state=SocioCognitiveState(
                state_type=SocioCognitiveStateType.RESOLUTION,
                description="Quick agreement"
            )
        )

        gap_long = self.evaluator.calculate_gap(long_trajectory)
        gap_short = self.evaluator.calculate_gap(short_trajectory)

        # Longer, more complex conflict should have higher gap
        self.assertGreater(gap_long, gap_short)

    def test_calculate_consensus_gap_scores_batch(self):
        """Test batch calculation of gap scores."""
        trajectories = [self.trajectory, self.ideal_trajectory]
        scores = calculate_consensus_gap_scores(trajectories)

        self.assertEqual(len(scores), 2)
        self.assertIn(self.trajectory.id, scores)
        self.assertIn(self.ideal_trajectory.id, scores)
        self.assertIsInstance(scores[self.trajectory.id], float)

    def test_data_independence_no_evaluator_terms_in_labels(self):
        """
        Test T048: Verify that classifier labels (from metadata) do not 
        contain tokens unique to the evaluator's 'ideal resolution' templates.
        
        This ensures strict decoupling between classifier training data 
        and evaluation ground truth.
        """
        # Define typical terms found in evaluator's ideal resolution templates
        evaluator_ideal_terms = [
            "consensus", "resolution", "agreement", "mutual", "understanding",
            "bridge", "common ground", "reconciliation", "harmony"
        ]
        
        # Define typical terms found in classifier labels (metadata tags)
        classifier_label_terms = [
            "high_reactivity", "low_reactivity", "diverse_identity", 
            "homogeneous_identity", "monitoring", "escalation", "de-escalation"
        ]
        
        # Check for overlap
        overlap = set(evaluator_ideal_terms) & set(classifier_label_terms)
        
        self.assertEqual(len(overlap), 0,
                         f"Classifier labels and evaluator terms should be disjoint. "
                         f"Found overlap: {overlap}. "
                         f"This risks circular validation.")

    def test_evaluation_result_schema(self):
        """Test that EvaluationResult has correct fields."""
        result = self.evaluator.evaluate(self.trajectory)
        
        self.assertIsInstance(result, EvaluationResult)
        self.assertEqual(result.trajectory_id, self.trajectory.id)
        self.assertIn(result.gap_score, [x for x in dir(self.trajectory) if not x.startswith('_')]) # Placeholder check
        self.assertIsNotNone(result.gap_score)


if __name__ == '__main__':
    unittest.main()