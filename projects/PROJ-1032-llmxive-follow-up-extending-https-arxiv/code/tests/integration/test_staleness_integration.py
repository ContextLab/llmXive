import pytest
import torch
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.llmxive.trainer import AsyncRLTrainer
from src.llmxive.config import StalenessConfig, ModelConfig, SeedConfig
from src.llmxive.staleness_queue import StalenessQueue

class TestStalenessIntegration:
    """Integration tests for staleness queue integration in training loop."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model for testing."""
        model = MagicMock()
        model.parameters.return_value = [torch.nn.Parameter(torch.randn(10, 10)) for _ in range(3)]
        return model

    @pytest.fixture
    def mock_data_loader(self):
        """Create a mock data loader."""
        loader = MagicMock()
        loader.__next__.return_value = {
            'input_ids': torch.randint(0, 1000, (1, 10)),
            'labels': torch.randint(0, 1000, (1, 10))
        }
        return loader

    @pytest.fixture
    def trainer_config(self):
        """Configuration for the trainer."""
        staleness_config = StalenessConfig(
            staleness_level=2,
            buffer_size=10
        )
        
        model_config = ModelConfig(
            model_id="microsoft/phi-2",
            device="cpu",
            data_split="train",
            max_length=512,
            quantization_config=None
        )
        
        seed_config = SeedConfig(seed=42)
        
        return staleness_config, model_config, seed_config

    def test_staleness_queue_integration(self, trainer_config, tmp_path):
        """Test that staleness queue is properly integrated into training loop."""
        staleness_config, model_config, seed_config = trainer_config
        
        # Create a minimal trainer (mocking heavy components)
        with patch('src.llmxive.trainer.load_model') as mock_load_model, \
             patch('src.llmxive.trainer.GSM8KDataLoader') as mock_data_loader_class, \
             patch('src.llmxive.trainer.MetricsTracker') as mock_metrics_class:
            
            # Setup mocks
            mock_model = MagicMock()
            mock_model.parameters.return_value = [torch.nn.Parameter(torch.randn(10, 10)) for _ in range(3)]
            mock_load_model.return_value = (mock_model, MagicMock())
            
            mock_loader = MagicMock()
            mock_loader.__next__.return_value = {
                'input_ids': torch.randint(0, 1000, (1, 10)),
                'labels': torch.randint(0, 1000, (1, 10))
            }
            mock_data_loader_class.return_value = mock_loader
            
            mock_metrics = MagicMock()
            mock_metrics.record_step = MagicMock()
            mock_metrics.get_results.return_value = {
                'steps': [],
                'mean_reward': 0.5,
                'mean_grad_norm': 0.1
            }
            mock_metrics_class.return_value = mock_metrics
            
            # Create trainer
            trainer = AsyncRLTrainer(
                model_config=model_config,
                staleness_config=staleness_config,
                seed_config=seed_config,
                output_dir=str(tmp_path)
            )
            
            # Verify staleness queue was initialized with correct buffer size
            assert trainer.staleness_queue.buffer_size == staleness_config.buffer_size
            assert trainer.staleness_queue.staleness_level == staleness_config.staleness_level

    def test_gradient_delay_logic(self, trainer_config, tmp_path):
        """Test that gradients are delayed by staleness steps."""
        staleness_config, model_config, seed_config = trainer_config
        
        with patch('src.llmxive.trainer.load_model') as mock_load_model, \
             patch('src.llmxive.trainer.GSM8KDataLoader') as mock_data_loader_class, \
             patch('src.llmxive.trainer.MetricsTracker') as mock_metrics_class, \
             patch('src.llmxive.trainer.get_baseline_thresholds', return_value={'mean_reward': 0.5, 'mean_grad_norm': 0.1}):
            
            # Setup mocks
            mock_model = MagicMock()
            mock_model.parameters.return_value = [torch.nn.Parameter(torch.randn(10, 10)) for _ in range(3)]
            mock_load_model.return_value = (mock_model, MagicMock())
            
            mock_loader = MagicMock()
            mock_loader.__next__.return_value = {
                'input_ids': torch.randint(0, 1000, (1, 10)),
                'labels': torch.randint(0, 1000, (1, 10))
            }
            mock_data_loader_class.return_value = mock_loader
            
            mock_metrics = MagicMock()
            mock_metrics.record_step = MagicMock()
            mock_metrics.get_results.return_value = {
                'steps': [],
                'mean_reward': 0.5,
                'mean_grad_norm': 0.1
            }
            mock_metrics_class.return_value = mock_metrics
            
            # Create trainer
            trainer = AsyncRLTrainer(
                model_config=model_config,
                staleness_config=staleness_config,
                seed_config=seed_config,
                output_dir=str(tmp_path)
            )
            
            # Simulate adding gradients to queue
            for i in range(5):
                gradients = [torch.randn(10, 10) for _ in range(3)]
                trainer.staleness_queue.add(gradients, i)
            
            # Verify queue size
            assert len(trainer.staleness_queue) == 5
            
            # Verify that we can get stale gradients
            if len(trainer.staleness_queue) > staleness_config.staleness_level:
                stale_grads = trainer.staleness_queue.get_stale_gradients(staleness_config.staleness_level)
                assert stale_grads is not None
                assert len(stale_grads) > 0

    def test_training_loop_with_staleness(self, trainer_config, tmp_path):
        """Test that training loop runs with staleness enabled."""
        staleness_config, model_config, seed_config = trainer_config
        
        with patch('src.llmxive.trainer.load_model') as mock_load_model, \
             patch('src.llmxive.trainer.GSM8KDataLoader') as mock_data_loader_class, \
             patch('src.llmxive.trainer.MetricsTracker') as mock_metrics_class, \
             patch('src.llmxive.trainer.get_baseline_thresholds', return_value={'mean_reward': 0.5, 'mean_grad_norm': 0.1}):
            
            # Setup mocks
            mock_model = MagicMock()
            mock_model.parameters.return_value = [torch.nn.Parameter(torch.randn(10, 10)) for _ in range(3)]
            mock_load_model.return_value = (mock_model, MagicMock())
            
            mock_loader = MagicMock()
            mock_loader.__next__.return_value = {
                'input_ids': torch.randint(0, 1000, (1, 10)),
                'labels': torch.randint(0, 1000, (1, 10))
            }
            mock_data_loader_class.return_value = mock_loader
            
            mock_metrics = MagicMock()
            mock_metrics.record_step = MagicMock()
            mock_metrics.get_results.return_value = {
                'steps': [],
                'mean_reward': 0.5,
                'mean_grad_norm': 0.1
            }
            mock_metrics_class.return_value = mock_metrics
            
            # Create trainer and run a few steps
            trainer = AsyncRLTrainer(
                model_config=model_config,
                staleness_config=staleness_config,
                seed_config=seed_config,
                output_dir=str(tmp_path)
            )
            
            # Run a small number of steps
            results = trainer.train(num_steps=10)
            
            # Verify results contain expected keys
            assert 'steps' in results or 'mean_reward' in results
            assert 'divergence_detected' in results
            assert 'peak_ram_gb' in results
            
            # Verify output file was created
            output_files = list(tmp_path.glob("training_manifest_*.json"))
            assert len(output_files) > 0
            
            # Verify JSON content
            with open(output_files[0], 'r') as f:
                saved_results = json.load(f)
                assert 'divergence_detected' in saved_results
                assert 'peak_ram_gb' in saved_results