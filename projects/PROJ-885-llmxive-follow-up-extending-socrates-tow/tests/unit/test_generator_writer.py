import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.data.generator import (
    _write_trajectories,
    _write_statistics,
    _compute_statistics,
    _serialize_trajectory,
)
from code.models.entities import (
    ConflictTrajectory,
    SocioCognitiveState,
    EmotionalReactivityLevel,
    CulturalIdentityDiversity,
    SocioCognitiveStateType,
)
from code.config import DATA_PROCESSED_DIR


@pytest.fixture
def sample_trajectory():
    return ConflictTrajectory(
        trajectory_id="test-uuid-123",
        created_at="2023-10-27T10:00:00",
        emotional_reactivity=EmotionalReactivityLevel.HIGH,
        cultural_identity_diversity=CulturalIdentityDiversity.DIVERSE,
        turns=[
            {"turn_id": "t1", "speaker": "A", "text": "Hello", "timestamp": "2023-10-27T10:00:00"}
        ],
        initial_state=SocioCognitiveState(
            state_type=SocioCognitiveStateType.CONFLICT,
            intensity=0.8,
            description="Start"
        ),
        final_state=SocioCognitiveState(
            state_type=SocioCognitiveStateType.CONFLICT,
            intensity=0.9,
            description="End"
        ),
        metadata={"source": "test"}
    )


def test_serialize_trajectory_handles_enums(sample_trajectory):
    """Test that the serializer correctly handles Enum values."""
    result = _serialize_trajectory(sample_trajectory)
    assert result["emotional_reactivity"] == "HIGH"
    assert result["cultural_identity_diversity"] == "DIVERSE"
    assert result["initial_state"]["state_type"] == "CONFLICT"


def test_write_trajectories_creates_file(sample_trajectory, tmp_path):
    """Test that _write_trajectories creates the file and writes valid JSON."""
    output_file = tmp_path / "trajectories.json"
    _write_trajectories([sample_trajectory], output_file)

    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["trajectory_id"] == "test-uuid-123"


def test_compute_statistics_counts_distribution(sample_trajectory):
    """Test that statistics computation correctly counts distributions."""
    # Create a list with known distribution
    trajectories = [sample_trajectory]
    
    stats = _compute_statistics(trajectories)
    
    assert stats["total_count"] == 1
    assert "HIGH" in stats["distribution"]["emotional_reactivity"]
    assert stats["distribution"]["emotional_reactivity"]["HIGH"] == 1
    assert "average_turns_per_trajectory" in stats["metrics"]


def test_write_statistics_creates_file(sample_trajectory, tmp_path):
    """Test that _write_statistics creates the file and writes valid JSON."""
    output_file = tmp_path / "stats.json"
    stats = _compute_statistics([sample_trajectory])
    _write_statistics(stats, output_file)

    assert output_file.exists()

    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert data["total_count"] == 1
    assert "generated_at" in data