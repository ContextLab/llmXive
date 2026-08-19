"""
Unit tests for dynamic E/I ratio enforcement (T010c).

Tests the enforce_ei_ratio function to ensure it:
1. Reads the static initialization state from model.ei_ratio_state
2. Calculates and applies correct scaling factors
3. Logs results to data/logs/ei_ratio_log.json
4. Bounds scaling factors within reasonable ranges
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import torch
import torch.nn as nn

from src.training.homeostasis import (
    enforce_ei_ratio,
    calculate_current_ei_ratio,
    _collect_ei_activities,
    HomeostaticScaler,
    HomeostasisConfig
)


class DummyModelWithEiState(nn.Module):
    """A dummy model with explicit excitatory and inhibitory parameters."""

    def __init__(self):
        super().__init__()
        # Excitatory weights
        self.exc_weights = nn.Parameter(torch.ones(10, 10) * 0.5)
        # Inhibitory weights
        self.inh_weights = nn.Parameter(torch.ones(10, 10) * 0.5)
        # Set the static initialization state (from T009c)
        self.ei_ratio_state = {
            "initial_exc_mean": 0.5,
            "initial_inh_mean": 0.5,
            "initial_ratio": 1.0
        }

    def forward(self, x):
        return x


class DummyModelWithoutEiState(nn.Module):
    """A dummy model without ei_ratio_state attribute."""

    def __init__(self):
        super().__init__()
        self.weights = nn.Parameter(torch.ones(10, 10))

    def forward(self, x):
        return x


@pytest.fixture
def temp_log_dir(monkeypatch):
    """Set up a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Monkeypatch the LOG_DIR constant
        import src.training.homeostasis as homeostasis_module
        original_log_dir = homeostasis_module.LOG_DIR
        homeostasis_module.LOG_DIR = tmpdir
        homeostasis_module.EI_RATIO_LOG_FILE = os.path.join(tmpdir, "ei_ratio_log.json")

        yield tmpdir

        # Restore original
        homeostasis_module.LOG_DIR = original_log_dir
        homeostasis_module.EI_RATIO_LOG_FILE = os.path.join(original_log_dir, "ei_ratio_log.json")


def test_enforce_ei_ratio_requires_ei_ratio_state():
    """Test that enforce_ei_ratio raises AttributeError if ei_ratio_state is missing."""
    model = DummyModelWithoutEiState()

    with pytest.raises(AttributeError, match="Model must have 'ei_ratio_state' attribute"):
        enforce_ei_ratio(model, step=0, target_ratio=4.0)


def test_enforce_ei_ratio_calculates_scaling_factor(temp_log_dir):
    """Test that enforce_ei_ratio calculates and applies correct scaling."""
    model = DummyModelWithEiState()

    # Initial ratio should be 1.0 (both weights are 0.5)
    initial_ratio = calculate_current_ei_ratio(model)
    assert abs(initial_ratio - 1.0) < 0.01

    # Enforce target ratio of 4.0
    result = enforce_ei_ratio(model, step=0, target_ratio=4.0)

    # Check result structure
    assert "step" in result
    assert "exc_activity" in result
    assert "inh_activity" in result
    assert "scaling_factor" in result

    # Check that scaling factor is applied
    assert result["scaling_factor"] > 1.0  # Should scale up excitatory
    assert result["scaling_factor"] < 10.0  # Should be bounded

    # Check that log file was created
    log_file = os.path.join(temp_log_dir, "ei_ratio_log.json")
    assert os.path.exists(log_file)

    with open(log_file, 'r') as f:
        log_data = json.load(f)

    assert len(log_data) == 1
    assert log_data[0]["step"] == 0


def test_enforce_ei_ratio_bounds_scaling_factor(temp_log_dir):
    """Test that scaling factors are bounded within MIN and MAX limits."""
    model = DummyModelWithEiState()

    # Set extreme target ratio to test bounds
    result = enforce_ei_ratio(model, step=0, target_ratio=100.0)

    # Check bounds (MIN_SCALING_FACTOR = 0.1, MAX_SCALING_FACTOR = 10.0)
    assert 0.1 <= result["scaling_factor"] <= 10.0


def test_enforce_ei_ratio_multiple_steps(temp_log_dir):
    """Test that enforce_ei_ratio works correctly across multiple steps."""
    model = DummyModelWithEiState()

    results = []
    for step in range(5):
        result = enforce_ei_ratio(model, step=step, target_ratio=4.0)
        results.append(result)

    # Check that log file has 5 entries
    log_file = os.path.join(temp_log_dir, "ei_ratio_log.json")
    with open(log_file, 'r') as f:
        log_data = json.load(f)

    assert len(log_data) == 5

    # Check that steps are sequential
    for i, entry in enumerate(log_data):
        assert entry["step"] == i


def test_homeostatic_scaler_class(temp_log_dir):
    """Test the HomeostaticScaler class interface."""
    config = HomeostasisConfig(target_ei_ratio=4.0, scaling_decay_rate=0.01)
    scaler = HomeostaticScaler(config)

    model = DummyModelWithEiState()

    # Test step method
    result = scaler.step(model)
    assert "step" in result
    assert result["step"] == 1

    # Test another step
    result = scaler.step(model)
    assert result["step"] == 2


def test_collect_ei_activities_separates_params():
    """Test that _collect_ei_activities correctly separates excitatory and inhibitory."""
    model = DummyModelWithEiState()

    exc_activity, inh_activity = _collect_ei_activities(model)

    # Both should be non-zero
    assert exc_activity > 0
    assert inh_activity > 0

    # Should be equal initially (both 0.5)
    assert abs(exc_activity - inh_activity) < 0.01