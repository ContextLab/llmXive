import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import torch

from src.llmxive.trainer import AsyncRLTrainer
from src.llmxive.config import StalenessConfig


class TestTrainerManifest:
    """Test that trainer logs model_id, staleness_level, seed, and reward_curve to JSON manifests."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @patch('src.llmxive.trainer.load_model')
    @patch('src.llmxive.trainer.load_baseline_manifest')
    @patch('src.llmxive.trainer.get_baseline_thresholds')
    @patch('src.llmxive.trainer.compute_reward')
    @patch('src.llmxive.trainer.compute_gradient_norm')
    @patch('src.llmxive.trainer.load_data_batch')
    def test_manifest_contains_required_fields(
        self,
        mock_load_batch,
        mock_grad_norm,
        mock_reward,
        mock_thresholds,
        mock_load_manifest,
        mock_load_model,
        temp_output_dir
    ):
        """Verify that the generated manifest contains model_id, staleness_level, seed, and reward_curve."""
        # Setup mocks
        mock_load_model.return_value = (MagicMock(), MagicMock())
        mock_load_manifest.return_value = {"seed": 42}
        mock_thresholds.return_value = {"mean_reward": 0.5, "mean_grad_norm": 0.1}
        mock_reward.return_value = 0.8
        mock_grad_norm.return_value = 0.05
        mock_load_batch.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}

        # Configure output path
        output_path = os.path.join(temp_output_dir, "manifests", "test_manifest.json")
        config = StalenessConfig(
            buffer_size=15,
            batch_size=4,
            output_manifest_path=output_path
        )

        # Create trainer
        trainer = AsyncRLTrainer(
            model_id="test-model",
            staleness_level=2,
            seed=123,
            config=config
        )

        # Run a few steps
        trainer.run(num_steps=10)

        # Verify manifest file exists
        assert os.path.exists(output_path), "Manifest file was not created"

        # Load and verify contents
        with open(output_path, 'r') as f:
            manifest = json.load(f)

        # Check required fields
        assert manifest["model_id"] == "test-model", "model_id not logged correctly"
        assert manifest["staleness_level"] == 2, "staleness_level not logged correctly"
        assert manifest["seed"] == 123, "seed not logged correctly"
        assert "reward_curve" in manifest, "reward_curve not logged"
        assert isinstance(manifest["reward_curve"], list), "reward_curve should be a list"
        assert len(manifest["reward_curve"]) == 10, "reward_curve should have 10 entries"

    @patch('src.llmxive.trainer.load_model')
    @patch('src.llmxive.trainer.load_baseline_manifest')
    @patch('src.llmxive.trainer.get_baseline_thresholds')
    @patch('src.llmxive.trainer.compute_reward')
    @patch('src.llmxive.trainer.compute_gradient_norm')
    @patch('src.llmxive.trainer.load_data_batch')
    def test_manifest_updated_periodically(
        self,
        mock_load_batch,
        mock_grad_norm,
        mock_reward,
        mock_thresholds,
        mock_load_manifest,
        mock_load_model,
        temp_output_dir
    ):
        """Verify that manifest is updated periodically during training."""
        # Setup mocks
        mock_load_model.return_value = (MagicMock(), MagicMock())
        mock_load_manifest.return_value = {"seed": 42}
        mock_thresholds.return_value = {"mean_reward": 0.5, "mean_grad_norm": 0.1}
        mock_reward.return_value = 0.8
        mock_grad_norm.return_value = 0.05
        mock_load_batch.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}

        output_path = os.path.join(temp_output_dir, "manifests", "test_manifest.json")
        config = StalenessConfig(
            buffer_size=15,
            batch_size=4,
            output_manifest_path=output_path
        )

        trainer = AsyncRLTrainer(
            model_id="test-model",
            staleness_level=2,
            seed=123,
            config=config
        )

        # Run 200 steps (should trigger 2 periodic updates at 100 and 200)
        trainer.run(num_steps=200)

        # Load final manifest
        with open(output_path, 'r') as f:
            manifest = json.load(f)

        # Verify all 200 steps are recorded
        assert len(manifest["reward_curve"]) == 200, "All 200 steps should be recorded"
        assert len(manifest["gradient_norms"]) == 200, "All 200 gradient norms should be recorded"