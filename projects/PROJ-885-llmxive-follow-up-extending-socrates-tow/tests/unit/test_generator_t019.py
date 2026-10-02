"""
Unit tests for T019: Deriving turn-level training pairs from trajectories.

These tests verify that the split_trajectory_into_turns function:
1. Correctly splits trajectories into sliding windows of N=3 turns.
2. Derives labels ONLY from metadata tags (independence from evaluator).
3. Includes required fields: confidence_score and threshold_used.
4. Produces the correct label schema (string).
"""
import pytest
from datetime import datetime
from code.data.generator import split_trajectory_into_turns
from code.models.entities import (
    ConflictTrajectory,
    SocioCognitiveState,
    SocioCognitiveStateType,
    EmotionalReactivityLevel,
    CulturalIdentityDiversity
)

def create_test_trajectory(reactivity, cultural, num_turns=10):
    """Helper to create a test trajectory."""
    turns = []
    for i in range(num_turns):
        turns.append({
            "turn_id": i,
            "text": f"Turn {i} text",
            "speaker": "A" if i % 2 == 0 else "B"
        })
    
    return ConflictTrajectory(
        trajectory_id="test-id-123",
        turns=turns,
        socio_cognitive_state=SocioCognitiveState(
            state_type=SocioCognitiveStateType.NEUTRAL,
            confidence=1.0,
            timestamp=datetime.now()
        ),
        metadata={
            "emotional_reactivity": reactivity,
            "cultural_identity": cultural
        },
        created_at=datetime.now()
    )

def test_split_trajectory_window_size():
    """Test that sliding windows are created with correct size (N=3)."""
    traj = create_test_trajectory(
        EmotionalReactivityLevel.HIGH,
        CulturalIdentityDiversity.HOMOGENEOUS,
        num_turns=5
    )
    
    # With 5 turns and window_size=3, we should get 5 - 3 + 1 = 3 pairs
    pairs = split_trajectory_into_turns(traj, window_size=3)
    
    assert len(pairs) == 3, f"Expected 3 pairs, got {len(pairs)}"
    
    # Check that each pair has exactly 3 turns in the text
    for pair in pairs:
        # The text should contain 3 turn texts joined by " | "
        assert pair["turn_text"].count(" | ") == 2, "Window should contain exactly 3 turns"

def test_label_derivation_high_reactivity():
    """Test that label is derived from emotional_reactivity metadata."""
    traj = create_test_trajectory(
        EmotionalReactivityLevel.HIGH,
        CulturalIdentityDiversity.HOMOGENEOUS
    )
    
    pairs = split_trajectory_into_turns(traj)
    
    # All pairs from this trajectory should have the same label
    for pair in pairs:
        assert pair["label"] == "high_reactivity", "Label should be 'high_reactivity' for HIGH reactivity"

def test_label_derivation_cultural_friction():
    """Test that label is derived from cultural_identity metadata."""
    # Low reactivity but diverse cultural identity -> cultural_friction
    traj = create_test_trajectory(
        EmotionalReactivityLevel.LOW,
        CulturalIdentityDiversity.DIVERSE
    )
    
    pairs = split_trajectory_into_turns(traj)
    
    for pair in pairs:
        assert pair["label"] == "cultural_friction", "Label should be 'cultural_friction' for DIVERSE culture"

def test_label_derivation_neutral():
    """Test that label is neutral when neither condition is met."""
    traj = create_test_trajectory(
        EmotionalReactivityLevel.LOW,
        CulturalIdentityDiversity.HOMOGENEOUS
    )
    
    pairs = split_trajectory_into_turns(traj)
    
    for pair in pairs:
        assert pair["label"] == "neutral", "Label should be 'neutral' for LOW reactivity and HOMOGENEOUS culture"

def test_schema_fields_present():
    """Test that all required schema fields are present."""
    traj = create_test_trajectory(
        EmotionalReactivityLevel.HIGH,
        CulturalIdentityDiversity.HOMOGENEOUS
    )
    
    pairs = split_trajectory_into_turns(traj)
    
    required_fields = ["turn_text", "label", "trajectory_id", "confidence_score", "threshold_used"]
    
    for pair in pairs:
        for field in required_fields:
            assert field in pair, f"Missing required field: {field}"
            
        # Check types
        assert isinstance(pair["turn_text"], str), "turn_text must be string"
        assert isinstance(pair["label"], str), "label must be string"
        assert isinstance(pair["trajectory_id"], str), "trajectory_id must be string"
        assert isinstance(pair["confidence_score"], float), "confidence_score must be float"
        assert isinstance(pair["threshold_used"], float), "threshold_used must be float"

def test_label_independence_from_evaluator():
    """
    Test that label derivation uses ONLY metadata tags.
    This verifies FR-005: No circular validation with ConsensusGapScore evaluator.
    """
    # Create a trajectory with specific metadata
    reactivity = EmotionalReactivityLevel.HIGH
    cultural = CulturalIdentityDiversity.HOMOGENEOUS
    traj = create_test_trajectory(reactivity, cultural)
    
    pairs = split_trajectory_into_turns(traj)
    
    # Verify that the label is based on metadata, not on turn text content
    # The turn text is generic, so if the label is correct, it came from metadata
    for pair in pairs:
        assert pair["label"] == "high_reactivity"
        # The turn_text should NOT contain any special tokens that would suggest
        # it was derived from an evaluator's "ideal resolution"
        assert "ideal_resolution" not in pair["turn_text"].lower()
        assert "gap_score" not in pair["turn_text"].lower()