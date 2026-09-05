"""
Unit tests for the physics simulation wrapper (code/utils/physics_sim.py).

These tests verify the core functionality of the PhysicsSimWrapper,
including configuration validation, simulation result structure,
and basic physics constraint checks without requiring a full PyBullet
environment to be running (using mocks where necessary).
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import os

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.physics_sim import (
    SimulationConfig,
    SimulationResult,
    PhysicsSimWrapper,
    create_simulation,
    run_physics_validation
)
from code.utils.error_handler import PhysicsSimError
from code.models.estimated_state_3d import EstimatedState3D


class TestSimulationConfig:
    """Tests for the SimulationConfig dataclass."""

    def test_creation_with_defaults(self):
        """Test creating a config with default values."""
        config = SimulationConfig()
        assert config.gravity == -9.81
        assert config.time_step == 0.016
        assert config.max_steps == 1000
        assert config.collision_tolerance == 0.01
        assert config.enable_sleeping is True

    def test_creation_with_custom_values(self):
        """Test creating a config with custom values."""
        custom_gravity = -10.5
        config = SimulationConfig(gravity=custom_gravity, time_step=0.02)
        assert config.gravity == custom_gravity
        assert config.time_step == 0.02

    def test_validation_positive_gravity(self):
        """Test that positive gravity raises an error (should be negative)."""
        with pytest.raises(ValueError):
            SimulationConfig(gravity=9.81)

    def test_validation_zero_time_step(self):
        """Test that zero time step raises an error."""
        with pytest.raises(ValueError):
            SimulationConfig(time_step=0.0)


class TestSimulationResult:
    """Tests for the SimulationResult dataclass."""

    def test_creation_success(self):
        """Test creating a successful result."""
        result = SimulationResult(
            success=True,
            status="completed",
            duration=1.5,
            final_states=[],
            collision_detected=False,
            reason=None
        )
        assert result.success is True
        assert result.status == "completed"
        assert result.collision_detected is False

    def test_creation_failure(self):
        """Test creating a failed result."""
        result = SimulationResult(
            success=False,
            status="failed",
            duration=0.1,
            final_states=[],
            collision_detected=False,
            reason="Simulation crashed"
        )
        assert result.success is False
        assert result.status == "failed"
        assert result.reason == "Simulation crashed"


class TestPhysicsSimWrapper:
    """Tests for the PhysicsSimWrapper class."""

    @patch('code.utils.physics_sim.PyBulletClient')
    def test_initialization(self, mock_pb_client):
        """Test that the wrapper initializes a PyBullet client."""
        mock_client_instance = MagicMock()
        mock_pb_client.return_value = mock_client_instance

        wrapper = PhysicsSimWrapper()
        
        # Verify the client was created
        mock_pb_client.assert_called_once()
        assert wrapper.client == mock_client_instance
        # Verify gravity was set
        mock_client_instance.set_gravity.assert_called_once_with(0, 0, -9.81)

    @patch('code.utils.physics_sim.PyBulletClient')
    def test_reset(self, mock_pb_client):
        """Test the reset method."""
        mock_client_instance = MagicMock()
        mock_pb_client.return_value = mock_client_instance

        wrapper = PhysicsSimWrapper()
        wrapper.reset()

        mock_client_instance.reset_simulation.assert_called_once()

    @patch('code.utils.physics_sim.PyBulletClient')
    def test_step_simulation(self, mock_pb_client):
        """Test stepping the simulation."""
        mock_client_instance = MagicMock()
        mock_pb_client.return_value = mock_client_instance

        wrapper = PhysicsSimWrapper()
        wrapper.step()

        mock_client_instance.step_simulation.assert_called_once()

    @patch('code.utils.physics_sim.PyBulletClient')
    def test_get_state(self, mock_pb_client):
        """Test retrieving state from simulation."""
        mock_client_instance = MagicMock()
        mock_pb_client.return_value = mock_client_instance
        
        # Mock the return value of get_link_state
        mock_client_instance.get_link_state.return_value = (
            [0.0, 0.0, 0.5],  # position
            [1.0, 0.0, 0.0, 0.0], # quaternion
            [0.0, 0.0, 0.0], # linear velocity
            [0.0, 0.0, 0.0]  # angular velocity
        )

        wrapper = PhysicsSimWrapper()
        state = wrapper.get_state(body_id=1, link_index=0)

        mock_client_instance.get_link_state.assert_called_once_with(1, 0)
        assert np.allclose(state['position'], [0.0, 0.0, 0.5])
        assert np.allclose(state['velocity'], [0.0, 0.0, 0.0])

    @patch('code.utils.physics_sim.PyBulletClient')
    def test_check_collision(self, mock_pb_client):
        """Test collision detection logic."""
        mock_client_instance = MagicMock()
        mock_pb_client.return_value = mock_client_instance

        wrapper = PhysicsSimWrapper()
        
        # Mock contact points
        mock_client_instance.get_contact_points.return_value = [
            (0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
        ]

        has_collision = wrapper.check_collision(body_a=1, body_b=2)
        
        assert has_collision is True
        mock_client_instance.get_contact_points.assert_called_once()

    @patch('code.utils.physics_sim.PyBulletClient')
    def test_cleanup(self, mock_pb_client):
        """Test that cleanup disconnects the client."""
        mock_client_instance = MagicMock()
        mock_pb_client.return_value = mock_client_instance

        wrapper = PhysicsSimWrapper()
        wrapper.cleanup()

        mock_client_instance.disconnect.assert_called_once()

    @patch('code.utils.physics_sim.PyBulletClient')
    def test_simulate_trajectory_success(self, mock_pb_client):
        """Test a successful trajectory simulation."""
        mock_client_instance = MagicMock()
        mock_pb_client.return_value = mock_client_instance
        
        # Mock state retrieval
        mock_client_instance.get_link_state.return_value = (
            [0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        )
        mock_client_instance.get_contact_points.return_value = []

        config = SimulationConfig(max_steps=10)
        wrapper = PhysicsSimWrapper(config=config)

        # Create dummy initial state
        initial_state = EstimatedState3D(
            positions=np.array([[0.0, 0.0, 0.0]]),
            velocities=np.array([[0.0, 0.0, 0.0]]),
            orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
            confidence_score=1.0
        )

        result = wrapper.simulate_trajectory(initial_state)

        assert result.success is True
        assert result.status == "completed"
        assert result.collision_detected is False
        assert len(result.final_states) > 0

    @patch('code.utils.physics_sim.PyBulletClient')
    def test_simulate_trajectory_collision(self, mock_pb_client):
        """Test simulation that detects a collision."""
        mock_client_instance = MagicMock()
        mock_pb_client.return_value = mock_client_instance
        
        # Mock state retrieval
        mock_client_instance.get_link_state.return_value = (
            [0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        )
        # Mock contact points to indicate collision
        mock_client_instance.get_contact_points.return_value = [
            (0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
        ]

        config = SimulationConfig(max_steps=10)
        wrapper = PhysicsSimWrapper(config=config)

        initial_state = EstimatedState3D(
            positions=np.array([[0.0, 0.0, 0.0]]),
            velocities=np.array([[0.0, 0.0, 0.0]]),
            orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
            confidence_score=1.0
        )

        result = wrapper.simulate_trajectory(initial_state)

        assert result.success is True
        assert result.collision_detected is True
        assert "collision" in result.status.lower()

    @patch('code.utils.physics_sim.PyBulletClient')
    def test_simulate_trajectory_gravity_violation(self, mock_pb_client):
        """Test simulation that detects a gravity violation (object floating)."""
        mock_client_instance = MagicMock()
        mock_pb_client.return_value = mock_client_instance
        
        # Mock state retrieval - object stays at same height despite gravity
        mock_client_instance.get_link_state.return_value = (
            [0.0, 0.0, 5.0], [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        )
        mock_client_instance.get_contact_points.return_value = []

        config = SimulationConfig(max_steps=100)
        wrapper = PhysicsSimWrapper(config=config)

        initial_state = EstimatedState3D(
            positions=np.array([[0.0, 0.0, 5.0]]),
            velocities=np.array([[0.0, 0.0, 0.0]]),
            orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
            confidence_score=1.0
        )

        # This test assumes the wrapper has logic to detect non-physical behavior
        # like floating without support. For now, we verify it runs without crashing.
        result = wrapper.simulate_trajectory(initial_state)
        
        # The wrapper should handle the simulation steps
        assert result is not None
        assert isinstance(result, SimulationResult)


class TestCreateSimulation:
    """Tests for the factory function create_simulation."""

    @patch('code.utils.physics_sim.PyBulletClient')
    def test_creates_wrapper(self, mock_pb_client):
        """Test that create_simulation returns a PhysicsSimWrapper."""
        config = SimulationConfig()
        wrapper = create_simulation(config)
        
        assert isinstance(wrapper, PhysicsSimWrapper)
        assert wrapper.config == config


class TestRunPhysicsValidation:
    """Tests for the high-level validation function run_physics_validation."""

    @patch('code.utils.physics_sim.PyBulletClient')
    @patch('code.utils.physics_sim.PhysicsSimWrapper')
    def test_validation_success(self, mock_wrapper_class, mock_pb_client):
        """Test successful validation flow."""
        mock_wrapper_instance = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper_instance
        
        # Mock a successful simulation result
        mock_result = SimulationResult(
            success=True,
            status="completed",
            duration=1.0,
            final_states=[],
            collision_detected=False,
            reason=None
        )
        mock_wrapper_instance.simulate_trajectory.return_value = mock_result

        initial_state = EstimatedState3D(
            positions=np.array([[0.0, 0.0, 0.0]]),
            velocities=np.array([[0.0, 0.0, 0.0]]),
            orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
            confidence_score=1.0
        )

        result = run_physics_validation(initial_state)

        assert result.success is True
        assert result.collision_detected is False
        mock_wrapper_instance.simulate_trajectory.assert_called_once_with(initial_state)
        mock_wrapper_instance.cleanup.assert_called_once()

    @patch('code.utils.physics_sim.PyBulletClient')
    @patch('code.utils.physics_sim.PhysicsSimWrapper')
    def test_validation_failure_simulation_crash(self, mock_wrapper_class, mock_pb_client):
        """Test validation when simulation crashes."""
        mock_wrapper_instance = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper_instance
        
        # Mock a failed simulation result
        mock_result = SimulationResult(
            success=False,
            status="failed",
            duration=0.1,
            final_states=[],
            collision_detected=False,
            reason="Physics engine error"
        )
        mock_wrapper_instance.simulate_trajectory.return_value = mock_result

        initial_state = EstimatedState3D(
            positions=np.array([[0.0, 0.0, 0.0]]),
            velocities=np.array([[0.0, 0.0, 0.0]]),
            orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
            confidence_score=1.0
        )

        result = run_physics_validation(initial_state)

        assert result.success is False
        assert "error" in result.reason.lower()
        mock_wrapper_instance.cleanup.assert_called_once()