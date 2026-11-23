"""
Unit tests for the physics_state_extractor module.

Tests verify that physics states are correctly extracted and serialized
for different object types (kinematic, rigid, deformable).
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from physics_state_extractor import PhysicsStateExtractor
from utils import set_deterministic_seed


class TestPhysicsStateExtractor:
    """Test suite for PhysicsStateExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a PhysicsStateExtractor instance for testing."""
        return PhysicsStateExtractor(seed=42)

    @pytest.fixture
    def mock_pybullet(self):
        """Mock PyBullet functions for testing."""
        with patch('physics_state_extractor.p') as mock_p:
            # Setup mock responses
            mock_p.getNumJoints.return_value = 7
            mock_p.getJointState.return_value = (0.0, 0.0, 0.0, 0.0)
            mock_p.getBasePositionAndOrientation.return_value = (
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]
            )
            yield mock_p

    def test_extract_kinematic_state(self, extractor, mock_pybullet):
        """Test extraction of kinematic state (joint angles)."""
        mock_pybullet.getNumJoints.return_value = 7
        mock_pybullet.getJointState.return_value = (0.5, 0.0, 0.0, 0.0)

        state_vector = extractor._extract_kinematic_state(body_id=1)

        assert len(state_vector) == 7
        assert all(isinstance(x, float) for x in state_vector)
        assert all(x == 0.5 for x in state_vector)

    def test_extract_rigid_state(self, extractor, mock_pybullet):
        """Test extraction of rigid body state (position + orientation)."""
        mock_pybullet.getBasePositionAndOrientation.return_value = (
            [1.0, 2.0, 3.0],
            [0.0, 0.0, 0.0, 1.0]
        )

        state_vector = extractor._extract_rigid_state(body_id=1)

        assert len(state_vector) == 7  # 3 position + 4 orientation
        assert state_vector[0:3] == [1.0, 2.0, 3.0]
        assert state_vector[3:7] == [0.0, 0.0, 0.0, 1.0]

    def test_serialize_states(self, extractor):
        """Test serialization of states to JSON."""
        states = [
            {
                "body_id": 1,
                "object_type": "kinematic",
                "timestamp": 0.0,
                "timestep_idx": 0,
                "state_vector": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                "metadata": {"num_joints": 7}
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            content_hash = extractor.serialize_states(states, output_path)

            # Verify file was created
            assert os.path.exists(output_path)

            # Verify content is valid JSON
            with open(output_path, 'r') as f:
                loaded_states = json.load(f)

            assert len(loaded_states) == 1
            assert loaded_states[0]["body_id"] == 1
            assert content_hash is not None
        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_extract_and_serialize(self, extractor, mock_pybullet):
        """Test the full extraction and serialization pipeline."""
        simulation_data = {
            "body_ids": [1],
            "object_types": ["kinematic"],
            "timesteps": [
                {"timestamp": 0.0, "timestep_idx": 0},
                {"timestamp": 0.016, "timestep_idx": 1}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            result = extractor.extract_and_serialize(simulation_data, output_path)

            assert "output_path" in result
            assert "num_states" in result
            assert "content_hash" in result
            assert result["num_states"] == 2  # 2 timesteps * 1 body
            assert os.path.exists(result["output_path"])
        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_extract_state_unknown_type(self, extractor):
        """Test extraction with unknown object type."""
        state = extractor.extract_state(
            body_id=1,
            object_type="unknown_type",
            timestamp=0.0,
            timestep_idx=0
        )

        assert state["state_vector"] == []
        assert state["object_type"] == "unknown_type"

    def test_extract_deformable_state_empty(self, extractor, mock_pybullet):
        """Test extraction of deformable state with no vertices."""
        mock_pybullet.getNumJoints.return_value = 0

        state_vector = extractor._extract_deformable_state(body_id=1)

        assert state_vector == []

    def test_deterministic_seeding(self):
        """Test that deterministic seeding works correctly."""
        extractor1 = PhysicsStateExtractor(seed=42)
        extractor2 = PhysicsStateExtractor(seed=42)

        # Both should have the same seed
        assert extractor1.seed == extractor2.seed == 42

    def test_extract_state_with_real_data(self, extractor):
        """Test extraction with realistic state data."""
        # Simulate a more complex kinematic chain state
        state = extractor.extract_state(
            body_id=1,
            object_type="kinematic",
            timestamp=0.123,
            timestep_idx=5
        )

        assert state["body_id"] == 1
        assert state["object_type"] == "kinematic"
        assert state["timestamp"] == 0.123
        assert state["timestep_idx"] == 5
        assert "state_vector" in state
        assert "metadata" in state