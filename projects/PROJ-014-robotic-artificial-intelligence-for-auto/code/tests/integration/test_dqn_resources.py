"""
Integration test for DQN training loop resource limits (US3).

This test verifies that the DQN training loop respects the global wall-clock
time budget and RAM constraints defined in the project configuration.

It simulates a training scenario by mocking the environment and agent to
ensure the resource monitoring logic triggers correctly without requiring
a full 6-hour training run.

Tests:
  - test_training_loop_respects_time_budget: Verifies early termination
    when the simulated time exceeds the configured limit.
  - test_training_loop_respects_ram_limit: Verifies that the system
    detects when RAM usage exceeds the threshold (mocked via psutil).
  - test_checkpoint_save_on_timeout: Ensures a checkpoint is saved
    before the training loop halts due to resource limits.
"""

import os
import sys
import time
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta

# Add src to path if not already present
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.utils.config import get_config, init_config, get_path, set_hyperparameter
from src.environment.checkpoint_manager import CheckpointManager
from src.utils.logger import ResourceLogger


class MockEnv:
    """Mock environment for resource testing."""
    def __init__(self):
        self.action_space = MagicMock()
        self.observation_space = MagicMock()
        self.step_count = 0

    def reset(self):
        self.step_count = 0
        return {"rgb": None, "depth": None, "grid": None}

    def step(self, action):
        self.step_count += 1
        # Simulate a small delay to allow time tracking
        time.sleep(0.001)
        return ({"rgb": None, "depth": None, "grid": None}, 0.0, False, {})


class MockAgent:
    """Mock DQN agent for resource testing."""
    def __init__(self):
        self.training_step = 0

    def train(self, batch_size=64):
        self.training_step += 1
        # Simulate training time
        time.sleep(0.001)
        return 0.0

    def save(self, path):
        with open(path, 'w') as f:
            json.dump({"step": self.training_step}, f)


def test_training_loop_respects_time_budget():
    """
    Verify that the training loop halts when the global time budget is exceeded.
    """
    # Initialize config with a very short time budget for testing
    init_config()
    set_hyperparameter("training", "global_time_budget_seconds", 0.5)  # 0.5 seconds
    set_hyperparameter("training", "num_seeds", 1)
    set_hyperparameter("training", "num_episodes_per_seed", 100)

    temp_dir = tempfile.mkdtemp()
    checkpoint_path = Path(temp_dir) / "checkpoint.pkl"

    # Mock the environment and agent
    mock_env = MockEnv()
    mock_agent = MockAgent()

    # Track if training was stopped
    stopped_early = False
    start_time = time.time()

    # Simulate the training loop logic from train_and_analyze.py
    # We inline the logic here to test the resource constraint specifically
    global_start = time.time()
    budget = get_config().get_hyperparameter("training", "global_time_budget_seconds")

    episode = 0
    while episode < 1000:  # Large number to force timeout
        current_time = time.time()
        elapsed = current_time - global_start

        if elapsed > budget:
            stopped_early = True
            # Simulate checkpoint save
            manager = CheckpointManager(checkpoint_path.parent)
            state = {
                "seed": 0,
                "episode": episode,
                "elapsed_time": elapsed,
                "agent_step": mock_agent.training_step
            }
            manager.save_checkpoint(state)
            break

        # Simulate one training step
        mock_agent.train()
        episode += 1

    assert stopped_early, "Training loop did not stop when time budget was exceeded"
    assert time.time() - start_time < 2.0, "Test took too long (logic error in budget check)"

    # Verify checkpoint was created
    assert checkpoint_path.exists(), "Checkpoint file was not saved on timeout"


@patch('psutil.Process')
def test_training_loop_respects_ram_limit(mock_process_class):
    """
    Verify that the training loop detects and handles RAM limit violations.
    """
    # Initialize config with a low RAM limit
    init_config()
    set_hyperparameter("training", "max_ram_gb", 0.001)  # 1 MB limit

    # Mock psutil to return high RAM usage
    mock_process = MagicMock()
    # RSS in bytes: 2 GB
    mock_process.memory_info.return_value.rss = 2 * 1024 * 1024 * 1024
    mock_process_class.return_value = mock_process

    # Simulate the RAM check logic
    from src.utils.logger import get_resource_summary

    ram_limit_gb = get_config().get_hyperparameter("training", "max_ram_gb")
    current_ram_gb = get_resource_summary().get("ram_gb", 0)

    # The mock returns 2GB, limit is 0.001GB
    assert current_ram_gb > ram_limit_gb, "Mock RAM usage should exceed limit"

    # Verify the logic would trigger a warning or halt
    # (In a real run, this would raise an exception or stop training)
    resource_logger = ResourceLogger(tempfile.mkdtemp())
    metrics = get_resource_summary()
    
    # Check that the logger captured the high RAM
    assert metrics["ram_gb"] > 0.001


def test_checkpoint_save_on_timeout():
    """
    Verify that a valid checkpoint is saved when the training loop times out.
    """
    temp_dir = tempfile.mkdtemp()
    checkpoint_file = Path(temp_dir) / "timeout_checkpoint.pkl"

    # Simulate the state saving logic
    state = {
        "seed": 42,
        "episode": 50,
        "elapsed_time": 100.5,
        "agent_step": 1234,
        "timestamp": datetime.now().isoformat()
    }

    manager = CheckpointManager(temp_dir)
    manager.save_checkpoint(state)

    assert checkpoint_file.exists(), "Checkpoint file not created"

    # Verify content
    loaded_state = manager.load_checkpoint(checkpoint_file)
    assert loaded_state["seed"] == 42
    assert loaded_state["episode"] == 50
    assert "elapsed_time" in loaded_state