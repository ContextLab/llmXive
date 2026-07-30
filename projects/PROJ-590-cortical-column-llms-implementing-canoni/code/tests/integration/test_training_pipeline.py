"""Integration tests for the complete training pipeline."""

import pytest
import torch
import os
import tempfile
from pathlib import Path
from src.training.trainer import TrainingConfig, run_training
from src.models.hybrid_network import create_hybrid_network
from src.data.benchmarks import generate_training_data, generate_test_data
from src.experiments.baseline_runner import BaselineRunner, ExperimentConfig

class TestBaselineTrainingPipeline:
    def test_full_training_run(self):
        """Test a complete training run with baseline model."""
        # Create temporary directory for outputs
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup config
            config = ExperimentConfig(
                model_type='baseline',
                hidden_dim=32,
                num_layers=1,
                batch_size=8,
                epochs=2,
                lr=0.001,
                output_dir=tmpdir
            )

            runner = BaselineRunner(config)

            # Run training
            result = runner.run()

            assert result is not None
            assert hasattr(result, 'train_mae')
            assert hasattr(result, 'test_mae')
            assert result.train_mae >= 0
            assert result.test_mae >= 0

    def test_training_with_homeostasis(self):
        """Test training with homeostatic scaling enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExperimentConfig(
                model_type='hybrid',
                hidden_dim=32,
                num_layers=1,
                batch_size=8,
                epochs=2,
                lr=0.001,
                use_homeostasis=True,
                output_dir=tmpdir
            )

            runner = BaselineRunner(config)
            result = runner.run()

            assert result is not None
            assert result.train_mae >= 0

    def test_gradient_logging(self):
        """Test that gradient norms are logged during training."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExperimentConfig(
                model_type='baseline',
                hidden_dim=32,
                num_layers=1,
                batch_size=8,
                epochs=2,
                lr=0.001,
                log_gradients=True,
                output_dir=tmpdir
            )

            runner = BaselineRunner(config)
            result = runner.run()

            # Check that gradient log file was created
            log_path = Path(tmpdir) / 'gradient_norms.json'
            assert log_path.exists()

class TestResourceConstraints:
    def test_memory_usage_within_limits(self):
        """Test that training stays within memory limits."""
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExperimentConfig(
                model_type='baseline',
                hidden_dim=32,
                num_layers=1,
                batch_size=8,
                epochs=1,
                lr=0.001,
                output_dir=tmpdir
            )

            runner = BaselineRunner(config)
            runner.run()

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Should not exceed 7GB increase (conservative check)
            assert memory_increase < 7 * 1024 * 1024 * 1024
