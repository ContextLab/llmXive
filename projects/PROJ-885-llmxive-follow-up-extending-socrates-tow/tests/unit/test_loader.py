"""
Unit tests for data validation utilities in code/data/loader.py.

These tests verify that the schema validation logic correctly enforces
compliance for generated trajectories.
"""
import pytest
from typing import List, Dict, Any
from datetime import datetime

# Import entities and validation functions
from models.entities import (
    ConflictTrajectory,
    SocioCognitiveState,
    EmotionalReactivityLevel,
    CulturalIdentityDiversity,
    SocioCognitiveStateType
)
from data.loader import (
    validate_conflict_trajectory,
    validate_socio_cognitive_state,
    validate_trajectory_batch,
    ValidationError
)


def create_valid_trajectory() -> ConflictTrajectory:
    """Helper to create a valid trajectory for testing."""
    return ConflictTrajectory(
        trajectory_id="valid-test-001",
        metadata={
            "emotional_reactivity": EmotionalReactivityLevel.HIGH,
            "cultural_identity": CulturalIdentityDiversity.DIVERSE,
            "source": "test"
        },
        turns=[
            {
                "turn_id": "t1",
                "speaker": "participant_A",
                "text": "This is a test message.",
                "timestamp": "2024-01-01T10:00:00Z"
            }
        ],
        socio_cognitive_states=[
            SocioCognitiveState(
                state_type=SocioCognitiveStateType.DEESCALATION,
                confidence=0.9,
                instructions=["de-escalate"]
            )
        ]
    )


def create_valid_state() -> SocioCognitiveState:
    """Helper to create a valid state for testing."""
    return SocioCognitiveState(
        state_type=SocioCognitiveStateType.DEESCALATION,
        confidence=0.85,
        instructions=["validate", "de-escalate"]
    )


class TestValidateSocioCognitiveState:
    """Tests for validate_socio_cognitive_state function."""

    def test_valid_state_passes(self):
        """A valid state should not raise an exception."""
        state = create_valid_state()
        # Should not raise
        validate_socio_cognitive_state(state)

    def test_invalid_type_raises(self):
        """Non-SocioCognitiveState type should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_socio_cognitive_state({"state_type": "test"})
        assert "Expected SocioCognitiveState" in str(exc_info.value)

    def test_invalid_confidence_raises(self):
        """Confidence outside [0.0, 1.0] should raise ValidationError."""
        state = create_valid_state()
        state.confidence = 1.5
        with pytest.raises(ValidationError) as exc_info:
            validate_socio_cognitive_state(state)
        assert "confidence" in str(exc_info.value)

    def test_invalid_state_type_raises(self):
        """Non-enum state_type should raise ValidationError."""
        state = create_valid_state()
        state.state_type = "invalid_type"  # type: ignore
        with pytest.raises(ValidationError) as exc_info:
            validate_socio_cognitive_state(state)
        assert "state_type" in str(exc_info.value)


class TestValidateConflictTrajectory:
    """Tests for validate_conflict_trajectory function."""

    def test_valid_trajectory_passes(self):
        """A valid trajectory should not raise an exception."""
        trajectory = create_valid_trajectory()
        # Should not raise
        validate_conflict_trajectory(trajectory)

    def test_invalid_type_raises(self):
        """Non-ConflictTrajectory type should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_conflict_trajectory({"trajectory_id": "test"})
        assert "Expected ConflictTrajectory" in str(exc_info.value)

    def test_missing_trajectory_id_raises(self):
        """Missing trajectory_id should raise ValidationError."""
        trajectory = create_valid_trajectory()
        trajectory.trajectory_id = None  # type: ignore
        with pytest.raises(ValidationError) as exc_info:
            validate_conflict_trajectory(trajectory)
        assert "trajectory_id" in str(exc_info.value)

    def test_empty_turns_raises(self):
        """Empty turns list should raise ValidationError."""
        trajectory = create_valid_trajectory()
        trajectory.turns = []
        with pytest.raises(ValidationError) as exc_info:
            validate_conflict_trajectory(trajectory)
        assert "empty list" in str(exc_info.value)

    def test_missing_turn_field_raises(self):
        """Turn missing required field should raise ValidationError."""
        trajectory = create_valid_trajectory()
        trajectory.turns[0]["text"] = None
        with pytest.raises(ValidationError) as exc_info:
            validate_conflict_trajectory(trajectory)
        assert "missing required fields" in str(exc_info.value)

    def test_invalid_metadata_type_raises(self):
        """Metadata not a dict should raise ValidationError."""
        trajectory = create_valid_trajectory()
        trajectory.metadata = []  # type: ignore
        with pytest.raises(ValidationError) as exc_info:
            validate_conflict_trajectory(trajectory)
        assert "metadata" in str(exc_info.value)

    def test_invalid_emotional_reactivity_enum_raises(self):
        """Invalid emotional_reactivity enum value should raise ValidationError."""
        trajectory = create_valid_trajectory()
        trajectory.metadata["emotional_reactivity"] = "INVALID"  # type: ignore
        with pytest.raises(ValidationError) as exc_info:
            validate_conflict_trajectory(trajectory)
        assert "emotional_reactivity" in str(exc_info.value)


class TestValidateTrajectoryBatch:
    """Tests for validate_trajectory_batch function."""

    def test_valid_batch_returns_correct_count(self):
        """Batch of valid trajectories should return correct valid count."""
        trajectories = [create_valid_trajectory() for _ in range(3)]
        valid_count, errors = validate_trajectory_batch(trajectories)
        assert valid_count == 3
        assert len(errors) == 0

    def test_mixed_batch_counts_correctly(self):
        """Batch with mixed valid/invalid should count correctly."""
        valid_traj = create_valid_trajectory()
        invalid_traj = create_valid_trajectory()
        invalid_traj.trajectory_id = None  # type: ignore
        
        trajectories = [valid_traj, invalid_traj, valid_traj]
        valid_count, errors = validate_trajectory_batch(trajectories)
        
        assert valid_count == 2
        assert len(errors) == 1
        assert "Trajectory 1" in errors[0]

    def test_non_list_input_raises(self):
        """Non-list input should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_trajectory_batch(create_valid_trajectory())  # type: ignore
        assert "Expected list" in str(exc_info.value)