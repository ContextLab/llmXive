"""
Tests for logging utilities.
"""
import pytest
import numpy as np
import os
import json
import tempfile
from utils.logging import TrainingLogger, log_training_metrics, calculate_action_entropy, calculate_training_accuracy

class TestTrainingLogger:
    def test_logger_initialization(self):
        """Test logger initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = TrainingLogger(run_id="test_run", output_dir=temp_dir, seed=42)

            assert logger.run_id == "test_run"
            assert logger.seed == 42
            assert os.path.exists(temp_dir)

    def test_log_step(self):
        """Test step logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = TrainingLogger(run_id="test_run", output_dir=temp_dir)

            logger.log_step(step=0, reward=1.0, loss=0.5)
            logger.log_step(step=1, reward=2.0, loss=0.3)

            assert len(logger.metrics['step']) == 2
            assert logger.metrics['reward'] == [1.0, 2.0]
            assert logger.metrics['loss'] == [0.5, 0.3]

    def test_get_summary(self):
        """Test summary generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = TrainingLogger(run_id="test_run", output_dir=temp_dir)

            logger.log_step(step=0, reward=1.0, loss=0.5)
            logger.log_step(step=1, reward=3.0, loss=0.3)

            summary = logger.get_summary()

            assert summary['total_steps'] == 2
            assert summary['reward_mean'] == 2.0
            assert summary['loss_mean'] == 0.4

    def test_save_metrics(self):
        """Test saving metrics to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = TrainingLogger(run_id="test_run", output_dir=temp_dir)

            logger.log_step(step=0, reward=1.0, loss=0.5)
            filepath = logger.save_metrics()

            assert os.path.exists(filepath)

            with open(filepath, 'r') as f:
                data = json.load(f)

            assert 'metrics' in data
            assert data['total_steps'] == 1

class TestCalculateActionEntropy:
    def test_uniform_distribution(self):
        """Test entropy calculation for uniform distribution."""
        action_probs = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = calculate_action_entropy(action_probs)

        # Max entropy for 4 actions is log(4)
        expected_entropy = np.log(4)
        assert np.isclose(entropy, expected_entropy)

    def test_deterministic_distribution(self):
        """Test entropy calculation for deterministic distribution."""
        action_probs = np.array([1.0, 0.0, 0.0, 0.0])
        entropy = calculate_action_entropy(action_probs)

        # Entropy should be 0
        assert np.isclose(entropy, 0.0)

    def test_empty_distribution(self):
        """Test handling of very small probabilities."""
        action_probs = np.array([1e-10, 1.0 - 1e-10])
        entropy = calculate_action_entropy(action_probs)

        # Should not raise an error
        assert entropy >= 0

class TestCalculateTrainingAccuracy:
    def test_perfect_accuracy(self):
        """Test perfect accuracy."""
        predictions = np.array([1, 2, 3, 4])
        targets = np.array([1, 2, 3, 4])

        accuracy = calculate_training_accuracy(predictions, targets)
        assert accuracy == 1.0

    def test_zero_accuracy(self):
        """Test zero accuracy."""
        predictions = np.array([1, 2, 3, 4])
        targets = np.array([4, 3, 2, 1])

        accuracy = calculate_training_accuracy(predictions, targets)
        assert accuracy == 0.0

    def test_partial_accuracy(self):
        """Test partial accuracy."""
        predictions = np.array([1, 2, 3, 4])
        targets = np.array([1, 2, 4, 4])

        accuracy = calculate_training_accuracy(predictions, targets)
        assert accuracy == 0.75

    def test_empty_arrays(self):
        """Test handling of empty arrays."""
        predictions = np.array([])
        targets = np.array([])

        accuracy = calculate_training_accuracy(predictions, targets)
        assert accuracy == 0.0
