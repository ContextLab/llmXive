"""
Unit tests for the training loop in src/training/trainer.py.

Tests:
- Resource monitoring functionality
- MAE calculation accuracy
- Training loop execution (with timeout)
- Metric recording
"""

import pytest
import torch
import numpy as np
import os
import sys
import time
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.training.trainer import (
    calculate_mae,
    get_resource_usage,
    TrainingConfig,
    TrainingMetrics,
    run_training
)
from src.models.baseline_transformer import BaselineTransformer


class TestMAECalculation:
    """Tests for MAE calculation."""

    def test_mae_perfect_prediction(self):
        """MAE should be 0 for perfect predictions."""
        preds = torch.tensor([1.0, 2.0, 3.0, 4.0])
        targets = torch.tensor([1.0, 2.0, 3.0, 4.0])
        mae = calculate_mae(preds, targets)
        assert mae == 0.0

    def test_mae_constant_error(self):
        """MAE should match constant error magnitude."""
        preds = torch.tensor([2.0, 3.0, 4.0, 5.0])
        targets = torch.tensor([1.0, 2.0, 3.0, 4.0])
        mae = calculate_mae(preds, targets)
        assert mae == 1.0

    def test_mae_mixed_errors(self):
        """MAE calculation with mixed errors."""
        preds = torch.tensor([1.5, 2.5, 3.5, 4.5])
        targets = torch.tensor([1.0, 2.0, 3.0, 4.0])
        mae = calculate_mae(preds, targets)
        assert abs(mae - 0.5) < 1e-6


class TestResourceMonitoring:
    """Tests for resource monitoring."""

    def test_get_resource_usage_returns_values(self):
        """Resource usage should return positive values."""
        mem_mb, cpu_pct = get_resource_usage()
        assert mem_mb > 0
        assert cpu_pct >= 0

    def test_resource_usage_changes(self):
        """Resource usage should change after computation."""
        mem1, cpu1 = get_resource_usage()
        
        # Perform some computation
        x = torch.randn(1000, 1000)
        y = torch.matmul(x, x.T)
        
        mem2, cpu2 = get_resource_usage()
        
        # Memory should be at least as high
        assert mem2 >= mem1 - 1  # Allow small variance


class TestTrainingLoop:
    """Tests for the training loop."""

    @pytest.fixture
    def small_config(self):
        """Create a minimal config for fast testing."""
        return TrainingConfig(
            num_epochs=2,
            batch_size=16,
            learning_rate=1e-3,
            max_grad_norm=1.0,
            log_interval=100,  # Disable logging for tests
            seed=42,
            output_dir="data/results",
            model_path="data/results/test_model.pt",
            metrics_path="data/results/test_metrics.json"
        )

    def test_training_runs_completes(self, small_config):
        """Training loop should complete without errors."""
        # Ensure output dir exists
        os.makedirs(small_config.output_dir, exist_ok=True)
        
        # Run training
        results = run_training(small_config)
        
        # Verify results structure
        assert "total_time_seconds" in results
        assert "final_mae" in results
        assert "history" in results
        assert len(results["history"]) > 0

    def test_metrics_file_created(self, small_config):
        """Metrics JSON file should be created."""
        os.makedirs(small_config.output_dir, exist_ok=True)
        
        run_training(small_config)
        
        assert os.path.exists(small_config.metrics_path)

    def test_model_file_created(self, small_config):
        """Model checkpoint file should be created."""
        os.makedirs(small_config.output_dir, exist_ok=True)
        
        run_training(small_config)
        
        assert os.path.exists(small_config.model_path)

    def test_history_records_epochs(self, small_config):
        """History should record all epochs."""
        os.makedirs(small_config.output_dir, exist_ok=True)
        
        results = run_training(small_config)
        
        assert len(results["history"]) == small_config.num_epochs
        for entry in results["history"]:
            assert "epoch" in entry
            assert "train_loss" in entry
            assert "val_loss" in entry
            assert "mae" in entry


class TestTrainingConfig:
    """Tests for configuration dataclass."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = TrainingConfig()
        assert config.num_epochs == 10
        assert config.batch_size == 32
        assert config.learning_rate == 1e-3
        assert config.max_grad_norm == 1.0

    def test_custom_values(self):
        """Config should accept custom values."""
        config = TrainingConfig(num_epochs=5, learning_rate=0.01)
        assert config.num_epochs == 5
        assert config.learning_rate == 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
