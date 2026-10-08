"""
Unit tests for T019: Turn-level training data derivation.

Tests the split_trajectory_into_turns and derive_classifier_training_data
functions to ensure they correctly create sliding windows and derive labels
from metadata only (FR-005 compliance).
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

# Import from project API surface
from data.generator import (
    split_trajectory_into_turns,
    derive_classifier_training_data,
    generate_conflict_trajectory,
    write_classifier_training_data
)
from models.entities import (
    ConflictTrajectory,
    SocioCognitiveState,
    SocioCognitiveStateType,
    EmotionalReactivityLevel,
    CulturalIdentityDiversity
)
from config import CONFIDENCE_THRESHOLD


class TestSplitTrajectoryIntoTurns:
    """Tests for split_trajectory_into_turns function."""
    
    def test_split_returns_correct_window_size(self):
        """Test that the function creates windows of size N=3."""
        # Create a trajectory with 5 turns
        state = SocioCognitiveState(
            state_type=SocioCognitiveStateType.NEUTRAL,
            emotional_reactivity=EmotionalReactivityLevel.LOW,
            cultural_identity=CulturalIdentityDiversity.STANDARD,
            timestamp=datetime.now().isoformat()
        )
        turns = [f"Turn {i}" for i in range(5)]
        trajectory = ConflictTrajectory(
            trajectory_id="test_001",
            socio_cognitive_state=state,
            turns=turns,
            created_at=datetime.now().isoformat()
        )
        
        windows = split_trajectory_into_turns(trajectory)
        
        # With 5 turns and window size 3, we should get 3 windows
        # (indices 0-2, 1-3, 2-4)
        assert len(windows) == 3
        
        # Check each window has the correct number of turns
        for window in windows:
            # The turn_text should contain 3 turns joined by " | "
            parts = window["turn_text"].split(" | ")
            assert len(parts) == 3
    
    def test_split_preserves_turn_order(self):
        """Test that windows preserve the original turn order."""
        state = SocioCognitiveState(
            state_type=SocioCognitiveStateType.NEUTRAL,
            emotional_reactivity=EmotionalReactivityLevel.LOW,
            cultural_identity=CulturalIdentityDiversity.STANDARD,
            timestamp=datetime.now().isoformat()
        )
        turns = ["A", "B", "C", "D", "E"]
        trajectory = ConflictTrajectory(
            trajectory_id="test_002",
            socio_cognitive_state=state,
            turns=turns,
            created_at=datetime.now().isoformat()
        )
        
        windows = split_trajectory_into_turns(trajectory)
        
        # First window should be A, B, C
        assert "A" in windows[0]["turn_text"]
        assert "B" in windows[0]["turn_text"]
        assert "C" in windows[0]["turn_text"]
        # Second window should be B, C, D
        assert "B" in windows[1]["turn_text"]
        assert "C" in windows[1]["turn_text"]
        assert "D" in windows[1]["turn_text"]
    
    def test_split_handles_short_trajectories(self):
        """Test behavior with fewer turns than window size."""
        state = SocioCognitiveState(
            state_type=SocioCognitiveStateType.NEUTRAL,
            emotional_reactivity=EmotionalReactivityLevel.LOW,
            cultural_identity=CulturalIdentityDiversity.STANDARD,
            timestamp=datetime.now().isoformat()
        )
        turns = ["A", "B"]  # Only 2 turns
        trajectory = ConflictTrajectory(
            trajectory_id="test_003",
            socio_cognitive_state=state,
            turns=turns,
            created_at=datetime.now().isoformat()
        )
        
        windows = split_trajectory_into_turns(trajectory)
        
        # Should return empty list since we can't form a window of 3
        assert len(windows) == 0


class TestDeriveClassifierTrainingData:
    """Tests for derive_classifier_training_data function."""
    
    def test_derives_correct_labels_from_metadata(self):
        """Test that labels are derived from metadata, not turn content."""
        # Create a high reactivity trajectory
        state = SocioCognitiveState(
            state_type=SocioCognitiveStateType.HIGH_REACTIVITY,
            emotional_reactivity=EmotionalReactivityLevel.HIGH,
            cultural_identity=CulturalIdentityDiversity.STANDARD,
            timestamp=datetime.now().isoformat()
        )
        turns = ["Neutral text", "More neutral", "Still neutral"]
        trajectory = ConflictTrajectory(
            trajectory_id="test_004",
            socio_cognitive_state=state,
            turns=turns,
            created_at=datetime.now().isoformat()
        )
        
        training_data = derive_classifier_training_data([trajectory])
        
        # All records should have 'high_reactivity' label regardless of turn text
        for record in training_data:
            assert record["label"] == "high_reactivity"
    
    def test_derives_cultural_friction_label(self):
        """Test that diverse cultural identity gets 'cultural_friction' label."""
        state = SocioCognitiveState(
            state_type=SocioCognitiveStateType.CULTURAL_FRICTION,
            emotional_reactivity=EmotionalReactivityLevel.LOW,
            cultural_identity=CulturalIdentityDiversity.DIVERSE,
            timestamp=datetime.now().isoformat()
        )
        turns = ["Text A", "Text B", "Text C"]
        trajectory = ConflictTrajectory(
            trajectory_id="test_005",
            socio_cognitive_state=state,
            turns=turns,
            created_at=datetime.now().isoformat()
        )
        
        training_data = derive_classifier_training_data([trajectory])
        
        for record in training_data:
            assert record["label"] == "cultural_friction"
    
    def test_includes_required_fields(self):
        """Test that all required fields are present in training records."""
        state = SocioCognitiveState(
            state_type=SocioCognitiveStateType.NEUTRAL,
            emotional_reactivity=EmotionalReactivityLevel.LOW,
            cultural_identity=CulturalIdentityDiversity.STANDARD,
            timestamp=datetime.now().isoformat()
        )
        turns = ["A", "B", "C", "D"]
        trajectory = ConflictTrajectory(
            trajectory_id="test_006",
            socio_cognitive_state=state,
            turns=turns,
            created_at=datetime.now().isoformat()
        )
        
        training_data = derive_classifier_training_data([trajectory])
        
        assert len(training_data) > 0
        record = training_data[0]
        
        # Check required fields from T019
        assert "turn_text" in record
        assert "label" in record
        assert "trajectory_id" in record
        assert "confidence_score" in record
        assert "threshold_used" in record
        
        # Check types
        assert isinstance(record["label"], str)
        assert isinstance(record["confidence_score"], float)
        assert isinstance(record["threshold_used"], float)
    
    def test_confidence_and_threshold_values(self):
        """Test that confidence_score and threshold_used are correctly set."""
        state = SocioCognitiveState(
            state_type=SocioCognitiveStateType.NEUTRAL,
            emotional_reactivity=EmotionalReactivityLevel.LOW,
            cultural_identity=CulturalIdentityDiversity.STANDARD,
            timestamp=datetime.now().isoformat()
        )
        turns = ["A", "B", "C"]
        trajectory = ConflictTrajectory(
            trajectory_id="test_007",
            socio_cognitive_state=state,
            turns=turns,
            created_at=datetime.now().isoformat()
        )
        
        training_data = derive_classifier_training_data([trajectory])
        
        for record in training_data:
            # For training data derivation, confidence is 1.0
            assert record["confidence_score"] == 1.0
            # threshold_used should match config
            assert record["threshold_used"] == CONFIDENCE_THRESHOLD
    
    def test_multiple_trajectories(self):
        """Test derivation from multiple trajectories."""
        trajectories = []
        for i in range(3):
            state = SocioCognitiveState(
                state_type=SocioCognitiveStateType.NEUTRAL,
                emotional_reactivity=EmotionalReactivityLevel.LOW,
                cultural_identity=CulturalIdentityDiversity.STANDARD,
                timestamp=datetime.now().isoformat()
            )
            turns = [f"T{i}_{j}" for j in range(5)]
            traj = ConflictTrajectory(
                trajectory_id=f"test_00{i}",
                socio_cognitive_state=state,
                turns=turns,
                created_at=datetime.now().isoformat()
            )
            trajectories.append(traj)
        
        training_data = derive_classifier_training_data(trajectories)
        
        # Should have training data from all trajectories
        trajectory_ids = set(r["trajectory_id"] for r in training_data)
        assert len(trajectory_ids) == 3


class TestLabelIndependenceFromEvaluator:
    """Tests to verify FR-005: Label derivation uses ONLY metadata, not evaluator logic."""
    
    def test_no_evaluator_logic_in_label_derivation(self):
        """
        Verify that the label derivation logic does not incorporate any
        logic or data from the ConsensusGapScore evaluator.
        """
        # Create a trajectory with neutral turns but high reactivity metadata
        state = SocioCognitiveState(
            state_type=SocioCognitiveStateType.HIGH_REACTIVITY,
            emotional_reactivity=EmotionalReactivityLevel.HIGH,
            cultural_identity=CulturalIdentityDiversity.STANDARD,
            timestamp=datetime.now().isoformat()
        )
        # Turns that sound neutral (no "resolution" or "agreement" keywords)
        turns = [
            "I understand your point.",
            "Let's consider the facts.",
            "That's a reasonable observation."
        ]
        trajectory = ConflictTrajectory(
            trajectory_id="test_008",
            socio_cognitive_state=state,
            turns=turns,
            created_at=datetime.now().isoformat()
        )
        
        training_data = derive_classifier_training_data([trajectory])
        
        # Despite neutral turn text, the label should be 'high_reactivity'
        # because it comes from metadata, not turn content
        for record in training_data:
            assert record["label"] == "high_reactivity"
            # Verify turn_text does not contain evaluator-specific keywords
            # (This is a simplified check; real evaluator logic is more complex)
            assert "resolution" not in record["turn_text"].lower()
            assert "agreement" not in record["turn_text"].lower()
    
    def test_label_mapping_is_metadata_only(self):
        """
        Explicitly verify that the label derivation logic uses ONLY
        trajectory metadata tags (emotional_reactivity, cultural_identity).
        """
        # Test case 1: High emotion -> high_reactivity
        state1 = SocioCognitiveState(
            state_type=SocioCognitiveStateType.HIGH_REACTIVITY,
            emotional_reactivity=EmotionalReactivityLevel.HIGH,
            cultural_identity=CulturalIdentityDiversity.STANDARD,
            timestamp=datetime.now().isoformat()
        )
        traj1 = ConflictTrajectory(
            trajectory_id="test_009a",
            socio_cognitive_state=state1,
            turns=["A", "B", "C"],
            created_at=datetime.now().isoformat()
        )
        
        # Test case 2: Diverse culture -> cultural_friction
        state2 = SocioCognitiveState(
            state_type=SocioCognitiveStateType.CULTURAL_FRICTION,
            emotional_reactivity=EmotionalReactivityLevel.LOW,
            cultural_identity=CulturalIdentityDiversity.DIVERSE,
            timestamp=datetime.now().isoformat()
        )
        traj2 = ConflictTrajectory(
            trajectory_id="test_009b",
            socio_cognitive_state=state2,
            turns=["A", "B", "C"],
            created_at=datetime.now().isoformat()
        )
        
        # Test case 3: Neither -> neutral
        state3 = SocioCognitiveState(
            state_type=SocioCognitiveStateType.NEUTRAL,
            emotional_reactivity=EmotionalReactivityLevel.LOW,
            cultural_identity=CulturalIdentityDiversity.STANDARD,
            timestamp=datetime.now().isoformat()
        )
        traj3 = ConflictTrajectory(
            trajectory_id="test_009c",
            socio_cognitive_state=state3,
            turns=["A", "B", "C"],
            created_at=datetime.now().isoformat()
        )
        
        training_data = derive_classifier_training_data([traj1, traj2, traj3])
        
        # Extract labels by trajectory
        labels_by_traj = {r["trajectory_id"]: r["label"] for r in training_data}
        
        # Verify mapping
        assert labels_by_traj["test_009a"] == "high_reactivity"
        assert labels_by_traj["test_009b"] == "cultural_friction"
        assert labels_by_traj["test_009c"] == "neutral"


class TestWriteClassifierTrainingData:
    """Tests for the write function."""
    
    def test_writes_valid_json(self, tmp_path):
        """Test that the write function creates a valid JSON file."""
        state = SocioCognitiveState(
            state_type=SocioCognitiveStateType.NEUTRAL,
            emotional_reactivity=EmotionalReactivityLevel.LOW,
            cultural_identity=CulturalIdentityDiversity.STANDARD,
            timestamp=datetime.now().isoformat()
        )
        turns = ["A", "B", "C"]
        trajectory = ConflictTrajectory(
            trajectory_id="test_010",
            socio_cognitive_state=state,
            turns=turns,
            created_at=datetime.now().isoformat()
        )
        
        training_data = derive_classifier_training_data([trajectory])
        output_path = tmp_path / "classifier_training_data.json"
        
        write_classifier_training_data(training_data, output_path)
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify it's valid JSON
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert len(loaded_data) == len(training_data)
        assert "turn_text" in loaded_data[0]
        assert "label" in loaded_data[0]
        assert "confidence_score" in loaded_data[0]
        assert "threshold_used" in loaded_data[0]