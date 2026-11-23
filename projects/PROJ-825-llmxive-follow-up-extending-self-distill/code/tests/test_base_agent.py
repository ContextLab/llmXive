"""
Unit tests for the Base Agent interface.
Verifies that the abstract contract is correctly defined and that
a mock implementation can satisfy the interface requirements.
"""
import pytest
import numpy as np
import torch
from unittest.mock import MagicMock
from config import TrainingConfig, EnvironmentConfig, ModelConfig
from agents.base_agent import BaseAgent


class MockAgent(BaseAgent):
    """
    Minimal concrete implementation of BaseAgent for testing purposes.
    """
    def reset(self, env):
        return env.reset()

    def select_action(self, observation, training=False):
        # Return a dummy action and info dict
        return 0, {"entropy": 0.0, "gating_score": 0.5}

    def update(self, trajectory):
        return {"policy_loss": 0.01, "value_loss": 0.005}

    def save_checkpoint(self, path):
        pass

    def load_checkpoint(self, path):
        pass


def test_base_agent_initialization():
    """Test that BaseAgent initializes correctly with config objects."""
    # Create minimal config objects
    train_cfg = TrainingConfig(variant="test", max_steps=100)
    env_cfg = EnvironmentConfig(max_steps_per_episode=50)
    model_cfg = ModelConfig(model_type="test", model_name="test")

    agent = MockAgent(
        config=train_cfg,
        env_config=env_cfg,
        model_config=model_cfg,
        seed=42
    )

    assert agent.seed == 42
    assert agent.config == train_cfg
    assert agent.env_config == env_cfg
    assert agent.model_config == model_cfg
    assert agent.step_count == 0
    assert agent.episode_count == 0
    assert agent.is_training is False


def test_base_agent_abstract_methods():
    """Verify that the base class enforces abstract methods."""
    with pytest.raises(TypeError):
        # Attempting to instantiate BaseAgent directly should fail
        BaseAgent(
            config=TrainingConfig(variant="test", max_steps=100),
            env_config=EnvironmentConfig(max_steps_per_episode=50),
            model_config=ModelConfig(model_type="test", model_name="test"),
            seed=0
        )


def test_run_episode_logic():
    """Test the episode run loop logic with a mock environment."""
    train_cfg = TrainingConfig(variant="test", max_steps=100)
    env_cfg = EnvironmentConfig(max_steps_per_episode=50)
    model_cfg = ModelConfig(model_type="test", model_name="test")

    agent = MockAgent(
        config=train_cfg,
        env_config=env_cfg,
        model_config=model_cfg,
        seed=42
    )

    # Create a mock environment
    mock_env = MagicMock()
    mock_env.reset.return_value = "initial_obs"
    mock_env.step.side_effect = [
        ("obs_1", 1.0, False, False, {}),
        ("obs_2", 1.0, False, False, {}),
        ("obs_3", 2.0, True, False, {}),  # Done
    ]

    # Run one episode
    total_reward = agent.run_episode(mock_env, max_steps=10)

    assert total_reward == 3.0  # 1.0 + 1.0 + 2.0
    assert agent.episode_count == 1
    assert mock_env.reset.called
    assert mock_env.step.call_count == 3


def test_train_method_aggregation():
    """Test that the train method aggregates metrics correctly."""
    train_cfg = TrainingConfig(variant="test", max_steps=100)
    env_cfg = EnvironmentConfig(max_steps_per_episode=50)
    model_cfg = ModelConfig(model_type="test", model_name="test")

    agent = MockAgent(
        config=train_cfg,
        env_config=env_cfg,
        model_config=model_cfg,
        seed=42
    )

    mock_env = MagicMock()
    mock_env.reset.return_value = "obs"
    # Simulate 2 episodes, each with 2 steps
    mock_env.step.side_effect = [
        ("obs", 1.0, False, False, {}),
        ("obs", 1.0, True, False, {}),
        ("obs", 1.0, False, False, {}),
        ("obs", 1.0, True, False, {}),
    ]

    metrics = agent.train(mock_env, num_episodes=2)

    assert "policy_loss" in metrics
    assert "value_loss" in metrics
    # Since update always returns 0.01 and 0.005, averages should match
    assert np.isclose(metrics["policy_loss"], 0.01)
    assert np.isclose(metrics["value_loss"], 0.005)


def test_select_action_returns_dict():
    """Ensure select_action returns the expected info dictionary structure."""
    train_cfg = TrainingConfig(variant="test", max_steps=100)
    env_cfg = EnvironmentConfig(max_steps_per_episode=50)
    model_cfg = ModelConfig(model_type="test", model_name="test")

    agent = MockAgent(
        config=train_cfg,
        env_config=env_cfg,
        model_config=model_cfg,
        seed=42
    )

    action, info = agent.select_action("dummy_obs")

    assert isinstance(action, int)
    assert isinstance(info, dict)
    assert "entropy" in info
    assert "gating_score" in info
